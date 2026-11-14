variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Target deployment environment (staging or production)"
  type        = string
  default     = "staging"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "skillsphere"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "web_container_cpu" {
  description = "Fargate vCPU allocation for Web task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "web_container_memory" {
  description = "Fargate RAM allocation for Web task (MB)"
  type        = number
  default     = 2048
}

variable "web_min_capacity" {
  description = "Minimum number of Web Fargate tasks"
  type        = number
  default     = 2
}

variable "web_max_capacity" {
  description = "Maximum number of Web Fargate tasks under load"
  type        = number
  default     = 20
}

variable "worker_min_capacity" {
  description = "Minimum number of background Worker Fargate tasks"
  type        = number
  default     = 2
}

variable "worker_max_capacity" {
  description = "Maximum number of background Worker Fargate tasks"
  type        = number
  default     = 10
}

variable "db_instance_class" {
  description = "RDS PostgreSQL instance type"
  type        = string
  default     = "db.r6g.xlarge"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}
