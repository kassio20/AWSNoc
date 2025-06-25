# EC2 Instance para AWSNoc-IA IA
# Configuração da instância que vai hospedar a aplicação

# AMI mais recente do Ubuntu
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# EC2 Instance
resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.small"  # Suficiente para desenvolvimento
  key_name              = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.web.id]
  subnet_id             = aws_subnet.public[0].id
  iam_instance_profile  = aws_iam_instance_profile.ec2_profile.name

  # Storage
  root_block_device {
    volume_type = "gp3"
    volume_size = 20  # GB
    encrypted   = false
  }

  # User data para setup inicial
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    DB_ENDPOINT  = aws_db_instance.main.endpoint
    DB_PASSWORD  = var.db_password
    DB_NAME      = aws_db_instance.main.db_name
    DB_USER      = aws_db_instance.main.username
    S3_BUCKET    = aws_s3_bucket.frontend.bucket
    AWS_REGION   = data.aws_region.current.name
  }))

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-server"
  })

  depends_on = [aws_db_instance.main]
}

# Elastic IP para ter IP fixo
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-eip"
  })
}

# Outputs adicionais para EC2
output "app_public_ip" {
  description = "IP público da aplicação"
  value       = aws_eip.app.public_ip
}

output "app_url" {
  description = "URL da aplicação"
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "ssh_command" {
  description = "Comando para SSH na instância"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.app.public_ip}"
}

