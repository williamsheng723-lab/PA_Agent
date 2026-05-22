"""Normalize common Stage 2 AI JSON variants before schema validation."""
from __future__ import annotations

import copy
import logging
from typing import Any

from pa_agent.ai.trace_normalize import normalize_stage2_traces

logger = logging.getLogger(__name__)


def normalize_stage2(obj: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *obj* with decision_trace quirks corrected."""
    out = copy.deepcopy(obj)
    normalize_stage2_traces(out)
    decision = out.get("decision")
    if isinstance(decision, dict) and decision.get("order_type") == "不下单":
        # A no-order decision has no executable trade; tolerate model-provided
        # win-rate estimates in legacy payloads by clearing them before schema
        # validation while keeping price-field mistakes strict.
        decision["estimated_win_rate"] = None
    return out
