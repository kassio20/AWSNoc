# Application Load Balancer
resource "aws_lb" "test_alb" {
  name               = "awsnoc-iaia-test-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = aws_subnet.public_subnets[*].id

  enable_deletion_protection = false

  tags = {
    Name = "awsnoc-iaia-test-alb"
  }
}

# Target Group for Hello World App
resource "aws_lb_target_group" "hello_world_tg" {
  name        = "awsnoc-iaia-hello-world-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.test_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "awsnoc-iaia-hello-world-tg"
  }
}

# Target Group for Unhealthy App (for failure simulation)
resource "aws_lb_target_group" "unhealthy_app_tg" {
  name        = "awsnoc-iaia-unhealthy-app-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.test_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "awsnoc-iaia-unhealthy-app-tg"
  }
}

# ALB Listener
resource "aws_lb_listener" "test_listener" {
  load_balancer_arn = aws_lb.test_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "forward"
    forward {
      target_group {
        arn = aws_lb_target_group.hello_world_tg.arn
      }
    }
  }
}

# ALB Listener Rule for /unhealthy path
resource "aws_lb_listener_rule" "unhealthy_rule" {
  listener_arn = aws_lb_listener.test_listener.arn
  priority     = 100

  action {
    type = "forward"
    forward {
      target_group {
        arn = aws_lb_target_group.unhealthy_app_tg.arn
      }
    }
  }

  condition {
    path_pattern {
      values = ["/unhealthy*"]
    }
  }
}

