import json
import uuid
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

import os
QUEUE_DIR = Path(os.environ.get("QUEUE_DIR", str(Path.home() / "day4-pipeline" / "queue")))

app = FastAPI(title="Day 4 Pipeline API")


class JobRequest(BaseModel):
    text: str


@app.post("/jobs")
def create_job(req: JobRequest) -> dict:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "text": req.text,
    }
    job_file = QUEUE_DIR / f"{job_id}.json"
    job_file.write_text(json.dumps(job_data, ensure_ascii=False), encoding="utf-8")

    queued_count = len(list(QUEUE_DIR.glob("*.json")))
    return {
        "job_id": job_id,
        "queue_size": queued_count,
    }
