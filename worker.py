import json
import os
import random
import re
import time

import boto3

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "ap-northeast-1"


def mask_pii(text: str) -> str:
    masked = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]", text)
    masked = re.sub(r"\b\d{2,4}-\d{2,4}-\d{4}\b", "[PHONE]", masked)
    return masked


def process_job(job: dict) -> dict:
    text = job.get("text", "")
    job_id = job.get("job_id", "unknown")

    if "ERROR_SIM" in text or random.random() < 0.1:
        raise RuntimeError(f"Simulated failure for job_id={job_id}")

    return {
        "job_id": job_id,
        "status": "completed",
        "masked_text": mask_pii(text),
    }


def save_result_to_s3(s3_client, job_id: str, payload: dict) -> str:
    key = f"results/{job_id}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
    )
    return key


def run_worker(wait_time_seconds: int = 10, idle_sleep: float = 1.0) -> None:
    if not SQS_QUEUE_URL:
        raise RuntimeError("SQS_QUEUE_URL environment variable is not set")
    if not S3_BUCKET_NAME:
        raise RuntimeError("S3_BUCKET_NAME environment variable is not set")

    sqs = boto3.client("sqs", region_name=AWS_REGION)
    s3 = boto3.client("s3", region_name=AWS_REGION)
    print(f"Worker started. Polling SQS: {SQS_QUEUE_URL}, Bucket: {S3_BUCKET_NAME}")

    while True:
        resp = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=wait_time_seconds,
        )
        messages = resp.get("Messages", [])
        if not messages:
            time.sleep(idle_sleep)
            continue

        for msg in messages:
            receipt_handle = msg["ReceiptHandle"]
            body_raw = msg.get("Body", "{}")
            try:
                job = json.loads(body_raw)
                job_id = job.get("job_id", "unknown")
                print(f"[INFO] Picked up job_id={job_id}")

                result = process_job(job)
                s3_key = save_result_to_s3(s3, job_id, result)

                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=receipt_handle,
                )
                print(f"[SUCCESS] Saved s3://{S3_BUCKET_NAME}/{s3_key} and deleted SQS message")
            except Exception as exc:
                print(f"[ERROR] Failed processing message: {exc}")


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        print("\nWorker stopped.")
