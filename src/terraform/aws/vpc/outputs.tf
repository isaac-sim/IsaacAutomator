output "vpc" {
  description = "Created VPC"

  value = {
    id         = aws_vpc.vpc.id
    cidr_block = aws_vpc.vpc.cidr_block
  }
}
