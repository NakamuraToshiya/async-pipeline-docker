import json
import random
import re
import time
from pathlib import Path

import os
QUEUE_DIR = Path(os.environ.get("QUEUE_DIR", str(Path.home() / "day4-pipeline" / "queue")))
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", str(Path.home() / "day4-pipeline" / "storage")))


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


def save_result(job_id: str, payload: dict) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    out_file = STORAGE_DIR / f"{job_id}.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_worker(poll_interval: float = 1.0) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    print("Day 4 Worker started. Watching queue...")

    while True:
        job_files = sorted(QUEUE_DIR.glob("*.json"))
        if job_files:
            job_file = job_files[0]
            try:
                job = json.loads(job_file.read_text(encoding="utf-8"))
                job_id = job.get("job_id", job_file.stem)
                print(f"[INFO] Picked up {job_id}")
                result = process_job(job)
                save_result(job_id, result)
                job_file.unlink()
                print(f"[SUCCESS] Saved to storage: {job_id}")
            except Exception as exc:
                job_id = job_file.stem
                error_result = {
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(exc),
                }
                save_result(job_id, error_result)
                job_file.unlink()
                print(f"[ERROR] {job_id} failed ({exc}). Saved error to storage.")
        else:
            time.sleep(poll_interval)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        print("\nWorker stopped.")
