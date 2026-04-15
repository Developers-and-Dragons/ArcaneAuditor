"""Tests for desktop-only POST /api/analyze-directory."""
import json
import time

import pytest

from file_processing import FileProcessor
from tests.test_server_config_crud import server_ctx


def _norm_rel(s: str) -> str:
    return s.replace("\\", "/")

MIN_PMD_A = json.dumps(
    {
        "id": "pageA",
        "presentation": {"body": {"type": "section", "children": []}},
    }
)
MIN_PMD_B = json.dumps(
    {
        "id": "pageB",
        "presentation": {"body": {"type": "section", "children": []}},
    }
)


def _wait_for_job(client, job_id, timeout=60.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/job/{job_id}")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            return data
        if data["status"] == "failed":
            pytest.fail(f"Job failed: {data.get('error')}")
        time.sleep(0.2)
    pytest.fail("Job did not complete in time")


def test_analyze_directory_forbidden_when_disabled(server_ctx):
    app = server_ctx.server.app
    app.state.allow_directory_analysis = False
    response = server_ctx.client.post(
        "/api/analyze-directory",
        json={"directory": str(server_ctx.personal), "config": "alpha_personal"},
    )
    assert response.status_code == 403


def test_analyze_directory_requires_valid_path(server_ctx):
    app = server_ctx.server.app
    app.state.allow_directory_analysis = True
    response = server_ctx.client.post(
        "/api/analyze-directory",
        json={"directory": str(server_ctx.personal / "does_not_exist"), "config": "alpha_personal"},
    )
    assert response.status_code == 400


def test_analyze_directory_rejects_invalid_config(server_ctx):
    app = server_ctx.server.app
    app.state.allow_directory_analysis = True
    response = server_ctx.client.post(
        "/api/analyze-directory",
        json={"directory": str(server_ctx.personal), "config": "not_a_real_config_id"},
    )
    assert response.status_code == 400


def test_analyze_directory_nested_duplicate_basenames(server_ctx, tmp_path):
    """Two files named x.pmd in different folders map to distinct relative paths."""
    app = server_ctx.server.app
    app.state.allow_directory_analysis = True

    root = tmp_path / "proj"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    (root / "a" / "x.pmd").write_text(MIN_PMD_A, encoding="utf-8")
    (root / "b" / "x.pmd").write_text(MIN_PMD_B, encoding="utf-8")

    processor = FileProcessor()
    keys = {_norm_rel(k) for k in processor.process_directory(root).keys()}
    assert "a/x.pmd" in keys and "b/x.pmd" in keys

    response = server_ctx.client.post(
        "/api/analyze-directory",
        json={"directory": str(root), "config": "alpha_personal"},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    data = _wait_for_job(server_ctx.client, job_id)
    result = data["result"]
    assert result is not None
    assert "summary" in result


def test_analyze_directory_job_completes_with_two_distinct_paths(server_ctx, tmp_path):
    app = server_ctx.server.app
    app.state.allow_directory_analysis = True

    root = tmp_path / "proj2"
    (root / "nested" / "deep").mkdir(parents=True)
    (root / "nested" / "deep" / "one.pmd").write_text(MIN_PMD_A, encoding="utf-8")
    (root / "other.pmd").write_text(MIN_PMD_B, encoding="utf-8")

    response = server_ctx.client.post(
        "/api/analyze-directory",
        json={"directory": str(root), "config": "alpha_personal"},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    data = _wait_for_job(server_ctx.client, job_id)
    assert data["result"] is not None
    assert "summary" in data["result"]

