"""Single source of truth for market cycle enumerations, labels, and display helpers.

Used by: prompt assembler, JSON schema, stage2 normalizer, JSON validator, and GUI panels.
"""
from __future__ import annotations

# ── Cycle enum order (used for argmax tie-breaking — first wins) ──────────────

CYCLE_ORDER: tuple[str, ...] = (
    "spike",
    "micro_channel",
    "tight_channel",
    "normal_channel",
    "broad_channel",
    "trending_tr",
    "trading_range",
    "extreme_tr",
)

# Predictable cycle values (excludes "unknown")
CYCLE_ENUM: tuple[str, ...] = CYCLE_ORDER

# ── Chinese display labels ────────────────────────────────────────────────────

CYCLE_POSITION_ZH: dict[str, str] = {
    "spike": "尖峰 (Spike)",
    "micro_channel": "微型通道",
    "tight_channel": "窄通道",
    "normal_channel": "正常通道",
    "broad_channel": "宽通道",
    "trending_tr": "趋势型交易区间",
    "trading_range": "交易区间",
    "extreme_tr": "极端交易区间",
    "unknown": "未知",
}

# Direction → Chinese prefix (only applied to trending_tr)
_DIRECTION_PREFIX_ZH: dict[str, str] = {
    "bullish": "上涨",
    "bearish": "下跌",
}


# ── Public helpers ────────────────────────────────────────────────────────────

def format_cycle_position(raw: str) -> str:
    """Return the Chinese display text for a cycle enum value.

    Falls back to the raw value (or '—' for empty/None) for unknown keys.
    Pure function — does not modify any argument.
    """
    key = (raw or "").strip().lower()
    if not key:
        return "—"
    return CYCLE_POSITION_ZH.get(key, raw)


def format_cycle_with_direction(
    cycle_position: str,
    direction: str | None,
) -> str:
    """Return the Chinese display text for a cycle, with an optional direction prefix.

    The prefix (上涨 / 下跌) is applied ONLY when cycle_position == "trending_tr":
      - bullish  → "上涨趋势型交易区间"
      - bearish  → "下跌趋势型交易区间"
      - neutral / missing / any other value → "趋势型交易区间" (no prefix)

    For every other cycle the result is identical to format_cycle_position(cycle_position).

    Pure function — does not modify any argument.
    """
    base = format_cycle_position(cycle_position)
    cp = (cycle_position or "").strip().lower()
    if cp != "trending_tr":
        return base
    d = (direction or "").strip().lower()
    prefix = _DIRECTION_PREFIX_ZH.get(d, "")
    return f"{prefix}{base}" if prefix else base
