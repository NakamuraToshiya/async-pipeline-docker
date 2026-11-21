import json
import random
from fastapi.testclient import TestClient

import api
import worker


def test_mask_pii():
    text = "Contact me at test@example.com or 090-1234-5678."
    masked = worker.mask_pii(text)
    assert "[EMAIL]" in masked
    assert "[PHONE]" in masked
    assert "test@example.com" not in masked
    assert "090-1234-5678" not in masked


def test_process_job_success():
    random.seed(42)
    job = {"job_id": "job-123", "text": "User: alice@example.com, Tel: 03-1234-5678"}
    result = worker.process_job(job)
    assert result["job_id"] == "job-123"
    assert result["status"] == "completed"
    assert result["masked_text"] == "User: [EMAIL], Tel: [PHONE]"


def test_process_job_error_sim():
    job = {"job_id": "job-err", "text": "trigger ERROR_SIM please"}
    try:
        worker.process_job(job)
        assert False, "Expected RuntimeError for ERROR_SIM"
    except RuntimeError:
        assert True


def test_create_job_endpoint(tmp_path, monkeypatch):
    queue_dir = tmp_path / "queue"
    monkeypatch.setattr(api, "QUEUE_DIR", queue_dir)

    client = TestClient(api.app)
    res = client.post("/jobs", json={"text": "hello 090-1111-2222"})
    assert res.status_code == 200
    body = res.json()
    assert "job_id" in body
    assert body["queue_size"] == 1

    saved_file = queue_dir / f"{body['job_id']}.json"
    assert saved_file.exists()
    saved_data = json.loads(saved_file.read_text(encoding="utf-8"))
    assert saved_data["text"] == "hello 090-1111-2222"
