terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Cloud SQL PostgreSQL Instance (HA Regional)
resource "google_sql_database_instance" "postgres" {
  name             = "skillsphere-${var.environment}-pg"
  database_version = "POSTGRES_17"
  region           = var.gcp_region

  settings {
    tier              = "db-custom-4-16384"
    availability_type = "REGIONAL"
    disk_size         = 100
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = "projects/${var.gcp_project_id}/global/networks/default"
    }
  }
}

# 2. Cloud Memorystore Redis Instance (Standard HA Tier)
resource "google_redis_instance" "cache" {
  name           = "skillsphere-${var.environment}-redis"
  tier           = "STANDARD_HA"
  memory_size_gb = 5
  region         = var.gcp_region

  redis_version     = "REDIS_7_0"
  display_name      = "SkillSphere Redis Cluster"
  transit_encryption_mode = "SERVER_AUTHENTICATION"
}

# 3. Google Cloud Storage Bucket for Media & Resumes
resource "google_storage_bucket" "media" {
  name          = "skillsphere-${var.environment}-media"
  location      = var.gcp_region
  force_destroy = false

  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

# 4. Cloud Run Web Service (Serverless Container Autoscaling)
resource "google_cloud_run_v2_service" "web" {
  name     = "skillsphere-${var.environment}-web"
  location = var.gcp_region

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "gcr.io/${var.gcp_project_id}/skillsphere:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      env {
        name  = "DEBUG"
        value = "False"
      }
      env {
        name  = "STORAGE_BACKEND"
        value = "s3"
      }
    }
  }
}

output "web_service_uri" {
  value = google_cloud_run_v2_service.web.uri
}
