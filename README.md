# Async Pipeline Docker

Asynchronous job processing pipeline (FastAPI + Worker) containerized with Docker Compose.

## Architecture
- api: Accepts jobs via POST /jobs and writes job payloads to /app/queue.
- worker: Polls /app/queue, masks sensitive data (emails and phone numbers), and writes results to /app/storage.
- Shared Volumes: queue/ and storage/ are mounted into containers.

## Quick Start
1. Start services: docker compose up -d --build
2. Check status: docker compose ps
3. Send a test job: curl -s -X POST http://127.0.0.1:8000/jobs -H "Content-Type: application/json" -d '{"text":"hello user@example.com 090-1234-5678"}'
4. Stop services: docker compose down

## Files
- Dockerfile.api / Dockerfile.worker
- docker-compose.yml
- api.py / worker.py / requirements.txt
- .gitignore / README.md
