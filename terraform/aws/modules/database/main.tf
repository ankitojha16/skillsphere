terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "project_name" { type = string }
variable "environment" { type = string }
variable "subnet_ids" { type = list(string) }
variable "security_group_id" { type = string }
variable "instance_class" { type = string }

# RDS DB Subnet Group
resource "aws_db_subnet_group" "rds" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids
}

# RDS PostgreSQL Database (Multi-AZ with Automated Backups and PITR)
resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-${var.environment}-db"
  allocated_storage      = 100
  max_allocated_storage  = 500
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "17.2"
  instance_class         = var.instance_class
  db_name                = "skillsphere"
  username               = "skillsphere_admin"
  manage_master_user_password = true

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [var.security_group_id]

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:30-Sun:05:30"
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot"

  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  tags = {
    Environment = var.environment
  }
}

output "endpoint" { value = aws_db_instance.postgres.endpoint }
output "address" { value = aws_db_instance.postgres.address }
