from __future__ import annotations

import subprocess
import sys

from fastapi import APIRouter

from app.storage.migrations import main as init_schema

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/init-schema")
def admin_init_schema() -> dict:
    init_schema()
    return {"status": "ok", "message": "Cassandra schema initialized"}


@router.post("/train-models")
def admin_train_models() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "app.ai.train_models"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
