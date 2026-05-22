from __future__ import annotations

from pa_agent.ai.kline_features import compute_kline_geometry_features
from pa_agent.data.base import IndicatorBundle, KlineBar, KlineFrame


def test_compute_kline_geometry_features_classifies_basic_bars() -> None:
    frame = KlineFrame(
        symbol="XAUUSD",
        timeframe="5m",
        bars=(
            KlineBar(seq=1, ts_open=1.0, open=10.0, high=15.0, low=9.0, close=14.5, volume=1, closed=True),
            KlineBar(seq=2, ts_open=0.0, open=11.0, high=13.0, low=10.0, close=12.0, volume=1, closed=True),
        ),
        indicators=IndicatorBundle(ema20=(12.0, 11.0), atr14=(3.0, 2.0)),
        snapshot_ts_local_ms=1,
    )

    features = compute_kline_geometry_features(frame)

    assert features[0].seq == 1
    assert features[0].bar_type == "outside_bull"
    assert features[0].ema_relation == "above"
    assert features[0].range_atr_ratio == 2.0
    assert features[0].overlap_prev_ratio == 0.5
    assert features[1].bar_type == "trend_bull"


def test_compute_kline_geometry_features_marks_multibar_patterns() -> None:
    frame = KlineFrame(
        symbol="XAUUSD",
        timeframe="5m",
        bars=(
            KlineBar(seq=1, ts_open=3.0, open=12.0, high=13.0, low=11.0, close=12.8, volume=1, closed=True),
            KlineBar(seq=2, ts_open=2.0, open=11.0, high=14.0, low=10.0, close=13.5, volume=1, closed=True),
            KlineBar(seq=3, ts_open=1.0, open=10.0, high=12.0, low=10.0, close=11.5, volume=1, closed=True),
            KlineBar(seq=4, ts_open=0.0, open=10.0, high=15.0, low=9.0, close=14.0, volume=1, closed=True),
        ),
        indicators=IndicatorBundle(
            ema20=(9.0, 9.0, 9.0, 9.0),
            atr14=(5.0, 5.0, 5.0, 5.0),
        ),
        snapshot_ts_local_ms=1,
    )

    features = compute_kline_geometry_features(frame)

    assert features[0].ioi_pattern is True
    assert features[0].gap_bar == "bull_gap"
    assert features[0].ema_gap_count == 3
    assert features[0].breakout_prev == "none"


def test_compute_kline_geometry_features_detects_inside_sequence_and_micro_double() -> None:
    frame = KlineFrame(
        symbol="XAUUSD",
        timeframe="5m",
        bars=(
            KlineBar(seq=1, ts_open=2.0, open=10.0, high=12.0, low=10.0, close=11.0, volume=1, closed=True),
            KlineBar(seq=2, ts_open=1.0, open=11.0, high=13.0, low=10.0, close=12.0, volume=1, closed=True),
            KlineBar(seq=3, ts_open=0.0, open=12.0, high=14.0, low=9.0, close=13.0, volume=1, closed=True),
        ),
        indicators=IndicatorBundle(ema20=(11.0, 11.0, 11.0), atr14=(1.0, 1.0, 1.0)),
        snapshot_ts_local_ms=1,
    )

    features = compute_kline_geometry_features(frame)

    assert features[0].inside_sequence == "ii"
    assert features[0].micro_double == "MDB"
