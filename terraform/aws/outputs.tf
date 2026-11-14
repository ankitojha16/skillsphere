output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster"
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "PostgreSQL endpoint address"
  value       = module.database.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.cache.primary_endpoint_address
}

output "s3_bucket_name" {
  description = "Name of the media assets S3 bucket"
  value       = module.storage.bucket_name
}
