# ECS Cluster
resource "aws_ecs_cluster" "test_cluster" {
  name = "selectnocia-test-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "selectnocia-test-cluster"
  }
}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "selectnocia-test-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (for CloudWatch logs)
resource "aws_iam_role" "ecs_task_role" {
  name = "selectnocia-test-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/selectnocia-test"
  retention_in_days = 7

  tags = {
    Name = "selectnocia-test-log-group"
  }
}

# Task Definition for Hello World App
resource "aws_ecs_task_definition" "hello_world_task" {
  family                   = "selectnocia-hello-world"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "hello-world"
      image = "nginx:alpine"
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = "us-east-2"
          "awslogs-stream-prefix" = "hello-world"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "selectnocia-hello-world-task"
  }
}

# Task Definition for Node.js Hello World App
resource "aws_ecs_task_definition" "nodejs_hello_world_task" {
  family                   = "selectnocia-nodejs-hello-world"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "nodejs-hello-world"
      image = "nginx:alpine"
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = "us-east-2"
          "awslogs-stream-prefix" = "nodejs-hello-world"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost/ || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "selectnocia-nodejs-hello-world-task"
  }
}

# Task Definition for Unhealthy App (for failure simulation)
resource "aws_ecs_task_definition" "unhealthy_app_task" {
  family                   = "selectnocia-unhealthy-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "unhealthy-app"
      image = "node:16-alpine"
      command = ["sh", "-c", "echo 'const express = require(\"express\"); const app = express(); let healthy = true; app.get(\"/\", (req, res) => res.send(\"<h1>Unhealthy App for Testing</h1><p>Call /break to simulate failure</p><p>Call /fix to restore health</p>\")); app.get(\"/health\", (req, res) => healthy ? res.json({status: \"ok\"}) : res.status(500).json({status: \"error\"})); app.get(\"/break\", (req, res) => { healthy = false; res.send(\"App is now unhealthy!\"); }); app.get(\"/fix\", (req, res) => { healthy = true; res.send(\"App is now healthy!\"); }); app.listen(3000, () => console.log(\"Unhealthy test app running on port 3000\"));' > app.js && npm init -y && npm install express && node app.js"]
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = "us-east-2"
          "awslogs-stream-prefix" = "unhealthy-app"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "selectnocia-unhealthy-app-task"
  }
}

