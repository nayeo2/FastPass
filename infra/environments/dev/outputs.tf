output "instance_id" {
  value = aws_instance.fastpass_server.id
}

output "public_ip" {
  value = aws_instance.fastpass_server.public_ip
}