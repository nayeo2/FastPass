
# ----------------------------
# VPC
# VPC 생성 (CIDR: 10.0.0.0/16)
# VPC 이름: ${var.project_name}-${var.environment}-vpc
# ----------------------------
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# ----------------------------
# Public Subnet
# 퍼블릭 서브넷 생성 (AZ: var.aws_region + a)
# 서브넷 이름: ${var.project_name}-${var.environment}-public-a
# ----------------------------
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-a"
  }
}

# ----------------------------
# Internet Gateway
# 인터넷 게이트웨이 생성
# IGW 이름: ${var.project_name}-${var.environment}-igw
# ----------------------------
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# ----------------------------
# Route Table
# 퍼블릭 라우트 테이블 생성 (0.0.0.0/0 → IGW)
# 라우트 테이블 이름: ${var.project_name}-${var.environment}-public-rt
# ----------------------------
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

# 퍼블릭 서브넷에 라우트 테이블 연결
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_rt.id
}

# ----------------------------
# Security Group
# EC2용 보안 그룹 생성
# 보안 그룹 이름: ${var.project_name}-${var.environment}-ec2-sg
# ----------------------------
resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-${var.environment}-ec2-sg"
  description = "Security group for fastpass dev EC2"
  vpc_id      = aws_vpc.main.id

  # SSH (22) - var.my_ip 허용
  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # HTTP (80) - var.my_ip 허용
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # HTTPS (443) - var.my_ip 허용
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # redis (6379) - var.my_ip 허용
  ingress {
    description = "Redis access from my IP"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # 8000번 포트 열어두기
  ingress {
    description = "FastAPI 8000"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 모든 아웃바운드 허용
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-sg"
  }
}

# ----------------------------
# Ubuntu AMI
# Ubuntu 24.04 최신 AMI 조회 (Canonical)
# ----------------------------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ----------------------------
# EC2
# EC2 인스턴스 생성 (리전: var.aws_region)
# EC2 타입: var.instance_type
# 키페어: var.key_name
# EC2 이름: ${var.project_name}-${var.environment}-app-server
# ----------------------------
resource "aws_instance" "app_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_a.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true

  # 루트 볼륨 설정 (20GB, gp3)
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-app-server"
  }
}