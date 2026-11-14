terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. Multi-AZ VPC Network
module "vpc" {
  source       = "./modules/vpc"
  vpc_cidr     = var.vpc_cidr
  environment  = var.environment
  project_name = var.project_name
}

# 2. Least-Privilege Security Groups
module "security" {
  source       = "./modules/security"
  vpc_id       = module.vpc.vpc_id
  environment  = var.environment
  project_name = var.project_name
}

# 3. Persistent Object Storage (S3 & CloudFront OAC)
module "storage" {
  source       = "./modules/storage"
  environment  = var.environment
  project_name = var.project_name
}

# 4. Amazon RDS PostgreSQL (Multi-AZ with Automated Backups)
module "database" {
  source            = "./modules/database"
  environment       = var.environment
  project_name      = var.project_name
  subnet_ids        = module.vpc.private_data_subnet_ids
  security_group_id = module.security.rds_sg_id
  instance_class    = var.db_instance_class
}

# 5. Amazon ElastiCache Redis (Multi-AZ Cluster)
module "cache" {
  source            = "./modules/cache"
  environment       = var.environment
  project_name      = var.project_name
  subnet_ids        = module.vpc.private_data_subnet_ids
  security_group_id = module.security.redis_sg_id
  redis_node_type   = var.redis_node_type
}

# 6. ECS Fargate Cluster, Services, ALB & Auto Scaling
module "ecs" {
  source                   = "./modules/ecs"
  environment              = var.environment
  project_name             = var.project_name
  vpc_id                   = module.vpc.vpc_id
  public_subnet_ids        = module.vpc.public_subnet_ids
  private_subnet_ids       = module.vpc.private_app_subnet_ids
  alb_security_group_id    = module.security.alb_sg_id
  web_security_group_id    = module.security.ecs_web_sg_id
  worker_security_group_id = module.security.ecs_worker_sg_id
  container_image          = "skillsphere:latest"
  web_cpu                  = var.web_container_cpu
  web_memory               = var.web_container_memory
  web_min_capacity         = var.web_min_capacity
  web_max_capacity         = var.web_max_capacity
  worker_min_capacity      = var.worker_min_capacity
  worker_max_capacity      = var.worker_max_capacity
}
