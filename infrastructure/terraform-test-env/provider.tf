terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2" # Ohio region
  
  default_tags {
    tags = {
      Project     = "SelectNocIA"
      Environment = "test"
      Purpose     = "failure-simulation"
    }
  }
}

