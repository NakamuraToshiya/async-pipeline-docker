from datetime import datetime, timezone
import json
import os
import uuid

import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "ap-northeast-1"
SERVICE_NAME = "api"

app = FastAPI(title="Pipeline API (SQS/S3)")


def log_json(level: str, message: str, **fields) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "service": SERVICE_NAME,
        "message": message,
        **fields,
    }
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def get_sqs_client():
    if not SQS_QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL environment variable is not set")
    return boto3.client("sqs", region_name=AWS_REGION)


class JobRequest(BaseModel):
    text: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs")
def create_job(req: JobRequest) -> dict:
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "text": req.text,
    }
    try:
        sqs = get_sqs_client()
        resp = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(job_data, ensure_ascii=False),
        )
    except Exception as exc:
        log_json(
            "ERROR",
            "Failed to enqueue job",
            job_id=job_id,
            status_code=500,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {exc}") from exc

    message_id = resp.get("MessageId")
    log_json(
        "INFO",
        "Job enqueued to SQS",
        job_id=job_id,
        message_id=message_id,
        status="queued",
    )
    return {
        "job_id": job_id,
        "message_id": message_id,
        "status": "queued",
    }