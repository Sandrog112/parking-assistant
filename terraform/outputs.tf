output "instance_public_ip" {
  value = aws_instance.parking.public_ip
}

output "instance_id" {
  value = aws_instance.parking.id
}

output "mcp_url" {
  value = "http://${aws_instance.parking.public_ip}:8000"
}

output "weaviate_url" {
  value = "http://${aws_instance.parking.public_ip}:8080"
}
