output "ssh_key" {
  value = tls_private_key.ssh_key
}

output "aws_key_pair_id" {
  value = aws_key_pair.keypair.id
}
