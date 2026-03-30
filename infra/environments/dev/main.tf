locals {
  name_prefix = "${var.project_name}-${var.environment}"

}

# 서울 리전에 fastpass_server ec2 생성
# 이름: ticketing-backdffice-dev-server
resource "aws_instance" "fastpass_server" {
  ami                    = "ami-0c9c942bd7bf113a2"
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.fastpass_sg.id]

  tags = {
    Name = "${var.project_name}-${var.environment}-server"
  }
}

# 보안그룹 생성
resource "aws_security_group" "fastpass_sg" {
  name        = "${var.project_name}-${var.environment}-sg"
  description = "Security group for fastpass dev server"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-sg"
  }
}