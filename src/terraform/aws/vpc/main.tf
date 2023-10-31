
resource "aws_vpc" "vpc" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  tags = {
    Name = "${var.prefix}.vpc"
  }
}

resource "aws_internet_gateway" "vpc_gateway" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    Name = "${var.prefix}.vpc_gateway"
  }
}

resource "aws_default_route_table" "vpc_route_table" {
  default_route_table_id = aws_vpc.vpc.default_route_table_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.vpc_gateway.id
  }

  timeouts {
    create = "5m"
    update = "5m"
  }

  tags = {
    Name = "${var.prefix}.vpc_route_table"
  }
}
