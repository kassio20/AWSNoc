# Security Group for Application Load Balancer
resource "aws_security_group" "alb_sg" {
  name        = "selectnocia-test-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.test_vpc.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "selectnocia-test-alb-sg"
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_task_sg" {
  name        = "selectnocia-test-ecs-task-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.test_vpc.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  ingress {
    description     = "Custom port from ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "selectnocia-test-ecs-task-sg"
  }
}

