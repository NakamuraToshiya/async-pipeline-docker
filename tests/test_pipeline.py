from fastapi.testclient import TestClient

import api
import worker


def test_mask_pii():
    raw = "Contact me at test.user@example.com or 090-1234-5678."
    masked = worker.mask_pii(raw)
    assert "[EMAIL]" in masked
    assert "[PHONE]" in masked
    assert "test.user@example.com" not in masked
    assert "090-1234-5678" not in masked


def test_process_job_success(monkeypatch):
    monkeypatch.setattr(worker.random, "random", lambda: 0.9)
    res = worker.process_job({"job_id": "job-1", "text": "hello 03-1234-5678"})
    assert res["job_id"] == "job-1"
    assert res["status"] == "completed"
    assert "[PHONE]" in res["masked_text"]


def test_process_job_error_sim():
    try:
        worker.process_job({"job_id": "job-err", "text": "ERROR_SIM test"})
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "job-err" in str(exc)


def test_create_job_endpoint(monkeypatch):
    sent_messages = []

    class DummySQSClient:
        def send_message(self, QueueUrl, MessageBody):
            sent_messages.append({"QueueUrl": QueueUrl, "MessageBody": MessageBody})
            return {"MessageId": "msg-12345"}

    monkeypatch.setattr(api, "SQS_QUEUE_URL", "https://sqs.ap-northeast-1.amazonaws.com/766282146484/pipeline-job-queue")
    monkeypatch.setattr(api.boto3, "client", lambda service_name, region_name=None: DummySQSClient())

    client = TestClient(api.app)
    resp = client.post("/jobs", json={"text": "hello world"})
    assert resp.status_code == 200
    body = resp.json()
    assert "job_id" in body
    assert body["message_id"] == "msg-12345"
    assert len(sent_messages) == 1
    assert "hello world" in sent_messages[0]["MessageBody"]
