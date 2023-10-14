
output "public_ip" {
  value = aws_eip.eip.public_ip
}

output "isaac_vm_id" {
  value = aws_instance.isaac.id
}
