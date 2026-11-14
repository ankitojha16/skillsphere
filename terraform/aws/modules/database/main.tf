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

# RDS PostgreSQL Database (Multi-AZ DB Instance Deployment)
# - Synchronous physical block-level replication to standby instance in secondary AZ
# - Standby is passive and does NOT serve read queries (single endpoint for read/write)
# - Automatic failover with automated DNS failover in 60-120 seconds
# - Zero I/O suspension during daily automated snapshots and PITR
resource "aws_db_instance" "postgres" {
  identifier            = "${var.project_name}-${var.environment}-db"
  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  engine                = "postgres"
  # Target latest active supported PostgreSQL 17 minor release (17.11)
  # Verify with: aws rds describe-db-engine-versions --region ap-south-1 --engine postgres --engine-version 17.11
  engine_version              = "17.11"
  auto_minor_version_upgrade  = true
  instance_class              = var.instance_class
  db_name                     = "skillsphere"
  username                    = "skillsphere_admin"
  manage_master_user_password = true
  publicly_accessible         = false
  storage_encrypted           = true

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [var.security_group_id]

  backup_retention_period   = 30
  backup_window             = "03:00-04:00"
  maintenance_window        = "Sun:04:30-Sun:05:30"
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot"
  copy_tags_to_snapshot     = true

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Environment = var.environment
  }
}

output "endpoint" { value = aws_db_instance.postgres.endpoint }
output "address" { value = aws_db_instance.postgres.address }
output "master_user_secret_arn" { value = try(aws_db_instance.postgres.master_user_secret[0].secret_arn, "") }
