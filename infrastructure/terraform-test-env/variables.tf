variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "selectnocia"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "hello_world_desired_count" {
  description = "Desired count for hello world service"
  type        = number
  default     = 2
}

variable "unhealthy_app_desired_count" {
  description = "Desired count for unhealthy app service"
  type        = number
  default     = 1
}

