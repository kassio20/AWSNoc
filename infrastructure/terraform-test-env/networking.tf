# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "test_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "selectnocia-test-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "test_igw" {
  vpc_id = aws_vpc.test_vpc.id

  tags = {
    Name = "selectnocia-test-igw"
  }
}

# Public Subnets (for ALB)
resource "aws_subnet" "public_subnets" {
  count                   = 2
  vpc_id                  = aws_vpc.test_vpc.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "selectnocia-test-public-subnet-${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets (for ECS tasks)
resource "aws_subnet" "private_subnets" {
  count             = 2
  vpc_id            = aws_vpc.test_vpc.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "selectnocia-test-private-subnet-${count.index + 1}"
    Type = "Private"
  }
}

# NAT Gateways
resource "aws_eip" "nat_eips" {
  count  = 2
  domain = "vpc"

  tags = {
    Name = "selectnocia-test-nat-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.test_igw]
}

resource "aws_nat_gateway" "nat_gateways" {
  count         = 2
  allocation_id = aws_eip.nat_eips[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index].id

  tags = {
    Name = "selectnocia-test-nat-gateway-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.test_igw]
}

# Route Tables
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.test_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.test_igw.id
  }

  tags = {
    Name = "selectnocia-test-public-rt"
  }
}

resource "aws_route_table" "private_rt" {
  count  = 2
  vpc_id = aws_vpc.test_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gateways[count.index].id
  }

  tags = {
    Name = "selectnocia-test-private-rt-${count.index + 1}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_rta" {
  count          = 2
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "private_rta" {
  count          = 2
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_rt[count.index].id
}

