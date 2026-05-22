# Brooks Pattern Enum Reference

本文件是提示词工程参考层，不参与每次 Stage 1 / Stage 2 prompt 加载。用途是统一 `detected_patterns`、`bar_analysis.entry_setup_type` 与后续程序特征命名。

## detected_patterns 建议枚举

- `wedge`：楔形或三推结构。
- `reversal_attempt`：反转尝试，未必满足完整 MTR。
- `mtr`：主要趋势反转，需趋势线突破 + 前极点测试失败等核心条件。
- `breakout_failure`：突破失败，突破后快速回到原结构内。
- `breakout_pullback`：突破回踩或突破测试。
- `final_flag`：最终旗形或趋势末端旗形失败。
- `barbwire`：铁丝网或极紧凑交易区间。
- `double_top_bottom`：双顶、双底、微型双顶或微型双底。
- `climax`：买进高潮、卖出高潮、连续高潮。
- `shrinking_stairs`：收缩台阶或推进幅度递减。

## bar_type 建议枚举

- `trend_bull`
- `trend_bear`
- `doji`
- `inside`
- `outside_bull`
- `outside_bear`
- `flat`
- `other`

## entry_setup_type 建议枚举

- `H1`
- `H2`
- `L1`
- `L2`
- `MTR`
- `wedge`
- `tr_boundary`
- `breakout_pullback`
- `EMA_pullback`
- `none`

## 命名原则

- 程序特征使用英文枚举，提示词解释使用简体中文。
- `detected_patterns` 只放结构候选，不放具体交易方向。
- 是否可交易由 Stage 2 的 §9、§10、§14 决定，不能仅凭 pattern 枚举下单。
