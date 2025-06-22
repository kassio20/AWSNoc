# ECS Service for Hello World App
resource "aws_ecs_service" "hello_world_service" {
  name            = "selectnocia-hello-world-service"
  cluster         = aws_ecs_cluster.test_cluster.id
  task_definition = aws_ecs_task_definition.nodejs_hello_world_task.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_task_sg.id]
    subnets          = aws_subnet.private_subnets[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.hello_world_tg.arn
    container_name   = "nodejs-hello-world"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.test_listener]

  tags = {
    Name = "selectnocia-hello-world-service"
  }
}

# ECS Service for Unhealthy App
resource "aws_ecs_service" "unhealthy_app_service" {
  name            = "selectnocia-unhealthy-app-service"
  cluster         = aws_ecs_cluster.test_cluster.id
  task_definition = aws_ecs_task_definition.unhealthy_app_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_task_sg.id]
    subnets          = aws_subnet.private_subnets[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.unhealthy_app_tg.arn
    container_name   = "unhealthy-app"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.test_listener]

  tags = {
    Name = "selectnocia-unhealthy-app-service"
  }
}

