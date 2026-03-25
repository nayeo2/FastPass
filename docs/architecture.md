# Architecture

## Final Goal
- Route53 / CloudFront / WAF
- ALB
- Private subnet 기반 서비스 운영
- K3S Master / Worker node 구성
- Redis
- MySQL Active / Standby
- Prometheus / Grafana / Loki
- ArgoCD
- SQS / SNS
- WebSocket

## Current Step
- 초기에는 단일 서버에서 핵심 기능 먼저 검증
- App + Redis + MySQL 구조로 시작
- 이후 K3S 및 다중 노드 구조로 확장

## Core Focus
- 티켓팅 트래픽 처리
- Redis 기반 대기열
- 좌석 선점 동시성 제어
