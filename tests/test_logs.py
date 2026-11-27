import contextlib
import io
import json
import os

os.environ.setdefault("SQS_QUEUE_URL", "https://sqs.ap-northeast-1.amazonaws.com/123456789012/test-queue")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")

import api
import worker


def test_structured_json_logs():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        api.log_json("INFO", "Job enqueued", job_id="job-1", status="queued")
        worker.log_json("ERROR", "Job failed", job_id="job-1", error_type="RuntimeError")

    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 2

    api_log = json.loads(lines[0])
    worker_log = json.loads(lines[1])

    assert api_log["service"] == "api"
    assert api_log["level"] == "INFO"
    assert api_log["job_id"] == "job-1"
    assert "timestamp" in api_log

    assert worker_log["service"] == "worker"
    assert worker_log["level"] == "ERROR"
    assert worker_log["error_type"] == "RuntimeError"
