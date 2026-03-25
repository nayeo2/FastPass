# FASTPASS
## Ticketing & Backoffice System (AWS + Terraform + K3s)

대규모 트래픽 환경을 고려한 티켓팅 및 백오피스 시스템입니다.  
Terraform 기반으로 AWS 인프라를 코드화하고, K3s 클러스터 위에 MSA 구조로 서비스를 운영합니다.

## Architecture
- AWS VPC (Multi-AZ)
- Public / Private Subnet 분리
- ALB + CloudFront + WAF
- K3s 기반 Kubernetes 클러스터
- MySQL (Active/Standby), ElastiCache(Redis)
- SQS / SNS 비동기 메시징
- WebSocket 기반 실시간 대기열
- Argo CD 기반 GitOps 배포
- Prometheus + Grafana 모니터링

## Tech Stack
- Infra: Terraform, AWS
- Backend: Spring Boot (MSA)
- Frontend: React
- DB: MySQL, Redis
- DevOps: Docker, Kubernetes(K3s), Argo CD, GitHub Actions

## Features
- 대기열 기반 티켓팅 시스템
- 좌석 선점 및 동시성 제어
- 비동기 처리 (SQS/SNS)
- 실시간 상태 알림 (WebSocket)
- 관리자 백오피스 기능

## CI/CD
- GitHub Actions: Build & Docker Image Push (ECR)
- Argo CD: GitOps 기반 자동 배포
- Terraform: 인프라 코드 관리

## Project Structure
### 사진 추가 예정

## How to Run (Dev)
bash
# terraform
cd infra/environments/dev
terraform init
terraform apply

# backend
./gradlew bootRun

# frontend
npm install && npm run dev
Author
Nayoung Lee
