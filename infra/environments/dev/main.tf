locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "aws_instance" "fastpass_server" {
  ami           = "ami-0c9c942bd7bf113a2" # 서울 리전 Ubuntu 22.04 (변경 가능)
  instance_type = "t3.micro"

  tags = {
    Name = "${var.project_name}-${var.environment}-server"
  }
}

