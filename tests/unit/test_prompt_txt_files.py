"""Tests for stage prompt .txt file list helpers."""
from __future__ import annotations

from pa_agent.ai.prompt_assembler import (
    stage1_prompt_txt_files,
    stage2_prompt_txt_files,
)


def test_stage1_txt_files() -> None:
    files = stage1_prompt_txt_files()
    assert files == [
        "提示词大纲_人设与思维方式.txt",
        "二元决策.txt",
        "市场诊断框架.txt",
        "文件16-K线信号识别.txt",
        "逐棒分析检查单.txt",
    ]


def test_stage2_txt_files_order() -> None:
    routed = ["震荡区间交易策略.txt", "震荡区间分析识别.txt"]
    files = stage2_prompt_txt_files(routed)
    assert files[:2] == [
        "提示词大纲_人设与思维方式.txt",
        "二元决策.txt",
    ]
    assert files[2:-3] == routed
    assert files[-3:] == [
        "逐棒分析检查单.txt",
        "文件16-K线信号识别.txt",
        "文件17-止损和止盈与仓位管理.txt",
    ]
