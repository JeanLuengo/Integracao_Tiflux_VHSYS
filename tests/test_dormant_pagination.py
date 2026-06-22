"""Testes do helper de paginação do relatório de empresas inativas (frontend)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def _run_node(script: str) -> dict:
    result = subprocess.run(
        ["node", "-e", script],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def test_apply_pagination_update_skips_identical_state():
    out = _run_node(
        r"""
import { applyPaginationUpdate } from './src/lib/dormantPagination.ts';
const prev = { pageIndex: 0, pageSize: 100 };
const next = applyPaginationUpdate(prev, { pageIndex: 0, pageSize: 100 });
console.log(JSON.stringify({ sameRef: next === prev, next }));
"""
    )
    assert out["sameRef"] is True


def test_apply_pagination_update_applies_changes():
    out = _run_node(
        r"""
import { applyPaginationUpdate } from './src/lib/dormantPagination.ts';
const prev = { pageIndex: 0, pageSize: 25 };
const next = applyPaginationUpdate(prev, (p) => ({ ...p, pageIndex: 1 }));
console.log(JSON.stringify({ pageIndex: next.pageIndex, pageSize: next.pageSize }));
"""
    )
    assert out["pageIndex"] == 1
    assert out["pageSize"] == 25
