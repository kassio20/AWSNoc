output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.test_alb.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.test_alb.zone_id
}

output "hello_world_url" {
  description = "URL for the Hello World application"
  value       = "http://${aws_lb.test_alb.dns_name}/"
}

output "unhealthy_app_url" {
  description = "URL for the Unhealthy application (for testing failures)"
  value       = "http://${aws_lb.test_alb.dns_name}/unhealthy"
}

output "break_app_url" {
  description = "URL to break the unhealthy app (simulate failure)"
  value       = "http://${aws_lb.test_alb.dns_name}/unhealthy/break"
}

output "fix_app_url" {
  description = "URL to fix the unhealthy app (restore health)"
  value       = "http://${aws_lb.test_alb.dns_name}/unhealthy/fix"
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.test_cluster.name
}

output "target_group_arns" {
  description = "ARNs of the target groups"
  value = {
    hello_world  = aws_lb_target_group.hello_world_tg.arn
    unhealthy_app = aws_lb_target_group.unhealthy_app_tg.arn
  }
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.test_vpc.id
}

output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs_log_group.name
}

