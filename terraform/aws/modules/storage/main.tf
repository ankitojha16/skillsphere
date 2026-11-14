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

# -------------------------------------------------------------
# 1. S3 Bucket for Media Assets & Certificate PDFs (Private)
# -------------------------------------------------------------
resource "aws_s3_bucket" "media" {
  bucket = "${var.project_name}-${var.environment}-media-assets"
}

resource "aws_s3_bucket_versioning" "media" {
  bucket = aws_s3_bucket.media.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket                  = aws_s3_bucket.media.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# -------------------------------------------------------------
# 2. S3 Bucket for Shared Immutable Static Assets
# -------------------------------------------------------------
resource "aws_s3_bucket" "static" {
  bucket = "${var.project_name}-${var.environment}-static-assets"
}

resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket                  = aws_s3_bucket.static.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy: retain old release assets for 90 days before transitioning to Glacier or expiration
resource "aws_s3_bucket_lifecycle_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    id     = "retire-old-asset-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# -------------------------------------------------------------
# 3. CloudFront Origin Access Control (OAC)
# -------------------------------------------------------------
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${var.project_name}-${var.environment}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# -------------------------------------------------------------
# 4. CloudFront Distribution for Static Assets
# -------------------------------------------------------------
resource "aws_cloudfront_distribution" "static_cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "SkillSphere ${var.environment} CloudFront CDN distribution for static assets"
  default_root_object = ""

  origin {
    domain_name              = aws_s3_bucket.static.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.static.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static.id}"

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
  }

  price_class = "PriceClass_100" # Lowest tier: US, Canada, Europe, and Asia (including India)

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = var.environment
  }
}

# S3 Bucket Policy granting CloudFront OAC read permissions
resource "aws_s3_bucket_policy" "static_cdn" {
  bucket = aws_s3_bucket.static.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontOAC"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.static.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.static_cdn.arn
        }
      }
    }]
  })
}

# -------------------------------------------------------------
# Outputs
# -------------------------------------------------------------
output "bucket_name" { value = aws_s3_bucket.media.id }
output "bucket_arn" { value = aws_s3_bucket.media.arn }
output "static_bucket_name" { value = aws_s3_bucket.static.id }
output "static_bucket_arn" { value = aws_s3_bucket.static.arn }
output "cloudfront_distribution_id" { value = aws_cloudfront_distribution.static_cdn.id }
output "cloudfront_domain_name" { value = aws_cloudfront_distribution.static_cdn.domain_name }
