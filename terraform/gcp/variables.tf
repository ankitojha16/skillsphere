variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "skillsphere-production"
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

variable "min_instances" {
  description = "Minimum Cloud Run container instances"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum Cloud Run container instances under load"
  type        = number
  default     = 25
}
