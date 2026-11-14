terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "vpc_id" { type = string }
variable "project_name" { type = string }
variable "environment" { type = string }

# ALB Security Group (Public HTTPS/HTTP ingress)
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Allows public inbound traffic to ALB"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Web Security Group (Ingress strictly from ALB)
resource "aws_security_group" "ecs_web" {
  name        = "${var.project_name}-${var.environment}-ecs-web-sg"
  description = "Allows traffic from ALB to ECS Web tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Gunicorn port from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Worker Security Group (Egress only, no public ingress)
resource "aws_security_group" "ecs_worker" {
  name        = "${var.project_name}-${var.environment}-ecs-worker-sg"
  description = "Security group for background worker tasks"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS Security Group (Ingress from Web and Worker tasks only)
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "PostgreSQL ingress from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from ECS Web & Worker"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_web.id, aws_security_group.ecs_worker.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ElastiCache Redis Security Group (Ingress from Web and Worker tasks only)
resource "aws_security_group" "redis" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Redis ingress from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis port from ECS Web & Worker"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_web.id, aws_security_group.ecs_worker.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "alb_sg_id" { value = aws_security_group.alb.id }
output "ecs_web_sg_id" { value = aws_security_group.ecs_web.id }
output "ecs_worker_sg_id" { value = aws_security_group.ecs_worker.id }
output "rds_sg_id" { value = aws_security_group.rds.id }
output "redis_sg_id" { value = aws_security_group.redis.id }
