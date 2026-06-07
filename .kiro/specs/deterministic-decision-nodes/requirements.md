# Requirements Document

## Introduction

本规格描述 PA_Agent（Price Action 交易分析代理，目标工程仅为 `D:\cl\PA_Agent`，不含 zhibo 变体）二元决策树的一次改造：将一组**判据为纯确定性数值/结构规则**的决策节点，从「由 AI（DeepSeek 模型）撰写 answer/branch/reason」改为「由程序确定性判定」，并彻底移除市场可读性闸门节点。

改造目标有二：

1. **降低 AI token 用量**——AI 不再为这些节点输出内容。
2. **消除 AI 在确定性节点上的判断错误**——这些节点的判据本就是程序已能精确计算的数值/结构事实。

PA_Agent 采用两阶段 AI 流水线，由二元决策树（`prompt_engineering/二元决策.txt`）驱动：

- **阶段一（诊断闸门，§0–§2）**：产出诊断 JSON，含 `gate_trace`。
- **阶段二（策略与执行，§3–§14）**：产出决策 JSON，含 `decision_trace`。

程序已在 `pa_agent/ai/kline_features.py` 的 `compute_kline_geometry_features` 中计算了每根 K 线的确定性几何特征（`bar_type`、`close_position`、`ema_relation`、`range_atr_ratio`、`follow_through_1_2`、`ema_gap_count`、`breakout_prev` 等），帧上也带有 EMA20 与 ATR14 指标；`pa_agent/ai/router.py` 的 `route_strategy_files` 已按 `cycle_position`+`direction` 路由策略文件。本规格在此基础上把指定节点的判定职责移交给程序。

### 改造范围（确认清单，不得超出）

- **移除**：§0.1、§0.2（市场可读性）。
- **改为程序判定**：§1.1（数据是否足够，改为**调用阶段一 AI 之前**的前置数据闸门判定——数据不足时根本不把数据上传给 AI，直接报错；详见 Requirement 2 与 Requirement 12）、§2.3（多空方向）、§2.4（Always In 状态）、§9.1（信号 K 线是否已收盘）、§9.2（信号 K 线方向是否与计划一致）、§9.3（信号棒是否过长）、§9.5（入场棒是否有跟随）、§11.1–§11.4（下单方式路由）。
- **保持 AI 判定（不改）**：§1.2、§1.3、§2.1、§2.2、§2.5、§3–§8、§9.0/§9.4/§9.6/§9.7、§10.1/§10.2/§10.3（§10 已由 `validate_order_trade_metrics` 做数值校验，§10.3 仍由 AI 给出胜率主观估计）、§14（已由程序依据 AI 的 answer 强制执行）。
- **受控覆盖（在程序判定之上叠加）**：程序判定为权威默认；AI 可对可受控覆盖节点（§2.3、§2.4、§9.2、§9.3、§11.1–§11.4）提交带 `override_reason` 的覆盖；锁定节点（§1.1、§9.1）不可覆盖；安全闸门仅可朝更保守方向覆盖。详见 Requirement 11。

## Glossary

- **PA_Agent**：本交易分析代理系统，仅指 `D:\cl\PA_Agent` 工程实例。
- **DecisionNodeEngine（程序判定引擎）**：本规格新增/扩展的程序组件总称，负责对范围内节点做确定性判定并写入 `gate_trace`/`decision_trace`。
- **DataSufficiencyJudge**：判定 §1.1 数据是否足够（与质量是否合格）的确定性纯校验子职责；本次改造后由 PreflightDataGate 在调用阶段一 AI 之前调用，不再于归一化阶段（AI 之后）事后纠正。
- **PreflightDataGate（前置数据闸门 / Pre-flight Data Gate）**：在 `pa_agent/orchestrator/two_stage.py` 的 `submit()` 中、Pre-Stage-1 取消检查之后、构建阶段一消息（`build_stage1`）与调用阶段一 AI 之前执行的一道确定性数据校验闸门。命中数据不足时直接返回数据不足错误结果，并跳过阶段一与阶段二的全部 AI 调用。
- **InsufficientDataError（数据不足错误）**：PreflightDataGate 命中数据不足时返回的显式错误结果，带独立错误类型标识（如 `exception.type="insufficient_data"` 或等价 `reason`），可与 `network_error`、`validation_error` 区分，供 DecisionFlowUI 提示「数据不足，无法分析」与历史记录过滤。
- **DirectionJudge**：判定 §2.3 多空方向并填充 `direction` 字段的子职责。
- **AlwaysInJudge**：判定 §2.4 Always In 状态的子职责。
- **SignalBarJudge**：判定 §9.1/§9.2/§9.3 信号棒相关节点的子职责。
- **FollowThroughJudge**：判定 §9.5 入场棒跟随的子职责。
- **OrderMethodRouter**：依据 `cycle_position` 路由 §11.1–§11.4 下单方式的子职责。
- **GateEvaluation（闸门评估流程）**：阶段一产生 `gate_result` 与 `gate_trace` 的整体流程。
- **GateValidator（一致性校验器）**：`pa_agent/ai/coherence_checks.py` 与 `pa_agent/ai/decision_tree.py` 中的 `validate_gate_result_consistency`、`validate_stage1_coherence`、`validate_stage2_trace_consistency` 等校验函数。
- **TraceNormalizer（轨迹归一化器）**：`pa_agent/ai/trace_normalize.py` 中对 `gate_trace`/`decision_trace` 做归一化的逻辑。
- **PromptAssembler（提示词组装器）**：`pa_agent/ai/prompt_assembler.py`，组装阶段一/阶段二提示文本。
- **DecisionFlowUI（决策流可视化）**：`pa_agent/gui/decision_flow_viz.py`，渲染合并后的 trace。
- **KlineFrame**：K 线帧对象，`frame.bars` 为已收盘 K 线序列，`frame.indicators` 含 `ema20`、`atr14`。
- **BarCountThreshold**：§1.1 数据充足阈值，等于 20 根已收盘 K 线。
- **数据质量校验项（data quality checks）**：PreflightDataGate 在 K 线数量阈值之外额外校验的「数据不足/质量不足」情形：`frame` 为空或缺少 OHLC 数据（`bars` 为空或 OHLC 字段缺失/非法）、EMA20 与 ATR14 全为 NaN（指标预热不足）。
- **STAGE1_MANDATORY_GATE_NODES**：`coherence_checks.py` 中定义、`gate_result=proceed` 时 `gate_trace` 必须包含的节点元组。
- **node_id / question / answer / reason / branch / bar_range**：trace 条目字段。`answer` 取值集合为 {是, 否, 中性, 等待, 不适用}。`bar_range` 形如 `K50-K1` 或单根 `K1`（序号 1 = 最新已收盘）。
- **direction**：阶段一方向字段，取值 `bullish`、`bearish`、`neutral`。
- **AIL / AIS**：Always In Long / Always In Short。
- **受控覆盖（controlled override）**：AI 在具备程序规则未捕捉到的明确结构性理由时，对可受控覆盖节点提交的、带非空 `override_reason` 的判定替换；受程序规则约束（锁定节点不可覆盖、安全闸门仅可更保守、方向覆盖须整体一致）。
- **锁定节点（locked node）**：纯客观事实节点，程序能 100% 确定，AI 不得覆盖。范围为 §1.1（K 线数量是否 ≥ 20，由 PreflightDataGate 在调用 AI 之前判定）与 §9.1（信号 K 线是否已收盘）。
- **可受控覆盖节点（overridable node）**：允许受控覆盖的判断类节点，范围为 §2.3、§2.4、§9.2、§9.3、§11.1–§11.4。
- **override_reason**：AI 提交覆盖时必须随附的非空理由字段，说明程序规则未捕捉到的结构性依据。
- **overridden_by_ai**：trace 节点上的布尔留痕标记，为 `true` 时表示该程序判定已被 AI 受控覆盖。
- **program_answer / program_branch**：trace 节点上记录的程序原始判定值，覆盖发生后用于留痕与审计。
- **安全闸门单向覆盖（safety gate one-directional override）**：对安全相关结论（§1.1 数据不足→前置闸门报错（不调用 AI）、§10.3 不通过→`不下单`、§14 触犯→`不下单`）的覆盖只能朝更保守方向修改，禁止改为更激进。

## Requirements

### Requirement 1：移除市场可读性闸门节点（§0.1、§0.2）

**User Story:** 作为系统维护者，我希望彻底移除 §0.1（是否看得懂当前市场）与 §0.2（是否具备继续深入分析的条件）两个可读性判断节点，以便 AI 不再为「永远视为可读」的判断消耗 token，且闸门不再因可读性而停止。

#### Acceptance Criteria

1. THE GateValidator SHALL 从 STAGE1_MANDATORY_GATE_NODES 中移除 `0.1` 与 `0.2`。
2. WHEN `gate_result` 等于 `proceed`，THE GateValidator SHALL 在 `gate_trace` 不含 `0.1` 与 `0.2` 时返回零条一致性错误。
3. THE PromptAssembler SHALL 从阶段一闸门提示文本中移除节点 §0.1 与 §0.2 的强制评估要求。
4. THE GateEvaluation SHALL 不因市场可读性而将 `gate_result` 置为 `wait` 或 `unknown`。
5. IF AI 输出仍包含 `0.1` 或 `0.2` 节点，THEN THE GateValidator SHALL 将其视为可选节点并不产生校验错误。

### Requirement 2：§1.1 数据是否足够（改为调用 AI 之前的前置闸门判定）

**User Story:** 作为交易分析使用者，我希望程序在**调用阶段一 AI 之前**就依据已收盘 K 线数量与数据质量判定 §1.1，以便在数据不足时根本不把数据上传给 AI 分析，直接报错并节省 token，而不是先让 AI 跑一遍再事后改判为等待。

> 时机变更说明：改造前 §1.1 的判定发生在归一化阶段（`normalize_stage1`，即阶段一 AI 已返回结果之后），数据不足时阶段一 AI 已被白白调用一次。本次将 §1.1 的判定时机前移到 PreflightDataGate（`submit()` 中、构建并调用阶段一 AI 之前），数据不足时不调用任何 AI。集中描述前置闸门机制见 Requirement 12。

#### Acceptance Criteria

1. WHEN `submit()` 通过 Pre-Stage-1 取消检查后、构建阶段一消息（`build_stage1`）与调用阶段一 AI 之前，THE PreflightDataGate SHALL 从 `frame.bars` 计算已收盘 K 线数量并执行数据充足度与质量校验。
2. IF 已收盘 K 线数量小于 BarCountThreshold（20），THEN THE PreflightDataGate SHALL 判定为数据不足，不调用阶段一 AI，也不调用阶段二 AI。
3. IF `frame` 为空或缺少 OHLC 数据（`bars` 为空或 OHLC 字段缺失/非法），THEN THE PreflightDataGate SHALL 判定为数据不足，不调用阶段一 AI，也不调用阶段二 AI。
4. IF EMA20 与 ATR14 全为 NaN（指标预热不足），THEN THE PreflightDataGate SHALL 判定为数据不足，不调用阶段一 AI，也不调用阶段二 AI。
5. WHEN PreflightDataGate 判定为数据不足，THE PreflightDataGate SHALL 返回一个显式标记为数据不足/错误类型的 record（InsufficientDataError），使 DecisionFlowUI 明确提示「数据不足，无法分析」。
6. WHERE PreflightDataGate 判定数据充足且质量合格，THE PreflightDataGate SHALL 放行，使 `submit()` 继续正常的阶段一 AI 调用与后续流程。
7. THE PreflightDataGate SHALL 对相同的 `frame` 必得相同结论（确定性纯校验，不引入随机性或外部状态）。
8. WHERE 在 trace/诊断中体现 §1.1 节点，THE DecisionNodeEngine SHALL 可填充 §1.1 节点的 `answer=否`（数据不足）以保持决策树语义；但 §1.1 的权威判定来源 SHALL 为 PreflightDataGate，而非阶段一 AI 或归一化阶段。
9. THE PromptAssembler SHALL 指示 AI 不再输出 §1.1 节点。
10. THE GateValidator SHALL 接受 §1.1 来源由 AI 改为程序（前置闸门/程序填充）的事实（§1.1 仍属强制节点语义）。

### Requirement 3：§2.3 多空方向（改为程序判定，并填充 direction 字段）

**User Story:** 作为交易分析使用者，我希望程序依据确定性结构特征判定多空方向，以便消除 AI 在方向判定上的偏差，并统一驱动策略文件路由。

#### Acceptance Criteria

1. THE DirectionJudge SHALL 依据 EMA20 斜率、最近收盘重心位移、以及 HH/HL 与 LL/LH 波段结构推导方向，取值为 `bullish`、`bearish` 或 `neutral`。
2. THE DirectionJudge SHALL 将推导出的方向写入阶段一 `direction` 字段。
3. WHEN 推导方向为 `bullish` 或 `bearish`，THE DirectionJudge SHALL 将 §2.3 节点的 `answer` 置为 `是` 且 `branch` 置为对应方向值（`bullish` 或 `bearish`）。
4. WHEN 推导方向为 `neutral`，THE DirectionJudge SHALL 将 §2.3 节点的 `answer` 置为 `中性` 且 `branch` 置为 `neutral`。
5. THE DirectionJudge SHALL 使 §2.3 节点的 `branch` 与 `direction` 字段一致，满足 `validate_stage1_coherence` 对节点 2.3 的 branch/answer 校验。
6. THE PromptAssembler SHALL 指示 AI 不再输出 §2.3 节点，亦不再自行判定 `direction`。
7. THE TraceNormalizer SHALL 对程序填充的 §2.3 节点保持幂等（`_sync_gate_23_answer_with_direction` 不改变已正确填充的节点）。
8. WHEN AI 受控覆盖 §2.3 方向（见 Requirement 11），THE DecisionNodeEngine SHALL 使 `direction` 字段、§2.3 节点 `branch`/`answer` 与下游 `validate_stage1_coherence` 一致性校验保持自洽：覆盖要么整体生效（`direction` 字段随 §2.3 `branch` 一并更新），要么整体被拒绝，不得产生半生效的矛盾状态。

### Requirement 4：§2.4 Always In 状态（改为程序判定）

**User Story:** 作为交易分析使用者，我希望程序依据近 N 根 K 线相对 EMA20 的同侧收盘比例与 EMA20 斜率判定 Always In 状态，以便该纯数值节点不再依赖 AI。

#### Acceptance Criteria

1. THE AlwaysInJudge SHALL 依据最近 N 根 K 线收盘相对 EMA20 的同侧占比与 EMA20 斜率，判定状态为 AIL、AIS 或 `neutral`。
2. WHEN 判定为 AIL 或 AIS，THE AlwaysInJudge SHALL 将 §2.4 节点的 `answer` 置为 `是` 且在 `branch` 写明 `AIL` 或 `AIS`。
3. WHEN 判定既非 AIL 也非 AIS，THE AlwaysInJudge SHALL 将 §2.4 节点的 `answer` 置为 `否`。
4. THE AlwaysInJudge SHALL 为 §2.4 节点填写 `node_id="2.4"`、与决策树原文一致的 `question`、`answer`、非空 `reason` 与合法 `bar_range`。
5. THE PromptAssembler SHALL 指示 AI 不再输出 §2.4 节点。

### Requirement 5：信号棒检查 §9.1/§9.2/§9.3/§9.5（改为程序判定）

**User Story:** 作为交易分析使用者，我希望程序依据信号棒的几何特征确定性判定 §9.1、§9.2、§9.3、§9.5，以便这些数值/结构判断不再由 AI 撰写。

#### Acceptance Criteria

1. THE SignalBarJudge SHALL 将 §9.1 节点的 `answer` 置为 `是`（KlineFrame 内 K 线均为已收盘棒），并将信号棒引用限定为 K1 或更早的已收盘 K 线。
2. WHEN 信号棒 `bar_type` 与计划方向一致（做多 ↔ `trend_bull`，做空 ↔ `trend_bear`），THE SignalBarJudge SHALL 将 §9.2 节点的 `answer` 置为 `是`。
3. IF 信号棒 `bar_type` 为 `doji` 或与计划方向相反，THEN THE SignalBarJudge SHALL 将 §9.2 节点的 `answer` 置为 `否`。
4. WHEN 信号棒 `range_atr_ratio` 大于止损过长阈值，THE SignalBarJudge SHALL 将 §9.3 节点的 `answer` 置为 `是`（表示信号棒过长）。
5. WHERE 信号棒 `range_atr_ratio` 不超过止损过长阈值，THE SignalBarJudge SHALL 将 §9.3 节点的 `answer` 置为 `否`。
6. WHEN 信号棒之后的 `follow_through_1_2` 为 `yes`，THE FollowThroughJudge SHALL 将 §9.5 节点的 `answer` 置为 `是`。
7. IF `follow_through_1_2` 为 `failed` 或 `no`，THEN THE FollowThroughJudge SHALL 将 §9.5 节点的 `answer` 置为 `否`。
8. WHILE `follow_through_1_2` 为 `pending`，THE FollowThroughJudge SHALL 将 §9.5 节点的 `answer` 置为 `等待`。
9. THE SignalBarJudge SHALL 为 §9.1、§9.2、§9.3 各节点填写完整字段（`node_id`、`question`、`answer`、非空 `reason`、合法 `bar_range`）；THE FollowThroughJudge SHALL 为 §9.5 节点填写完整字段。
10. THE PromptAssembler SHALL 指示 AI 不再输出 §9.1、§9.2、§9.3、§9.5 节点，同时保留 §9.0、§9.4、§9.6、§9.7 由 AI 判定。

### Requirement 6：§11 下单方式路由（改为程序判定）

**User Story:** 作为交易分析使用者，我希望程序依据阶段一已确定的 `cycle_position` 直接路由下单方式（§11.1–§11.4），以便 AI 不再逐节点走这四步。

#### Acceptance Criteria

1. THE OrderMethodRouter SHALL 依据阶段一 `cycle_position` 推导下单方式，结果为 `限价单`、`突破单` 或 `市价单` 之一。
2. THE OrderMethodRouter SHALL 将 §11.1–§11.4 的路由结论写入 `decision_trace`，且使 §11 节点出现在 §10.3 之后（满足 `validate_stage2_trace_consistency` 的顺序约束）。
3. WHERE §10.3（交易者方程）`answer` 为 `是` 且决定下单，THE OrderMethodRouter SHALL 输出对应下单方式。
4. IF §10.3 `answer` 为 `否` 或 §14 禁止行为被触犯，THEN THE OrderMethodRouter SHALL 将 `order_type` 置为 `不下单`。
5. THE PromptAssembler SHALL 指示 AI 不再逐节点输出 §11.1–§11.4。
6. THE OrderMethodRouter SHALL 区别于既有 `route_strategy_files`（后者路由策略文件），仅负责下单方式（order method）的确定性选择。

### Requirement 7：跨组件一致性（提示文本 + 校验器 + 归一化器 + UI）

**User Story:** 作为系统维护者，我希望所有受影响组件保持一致，以便程序填充节点不会触发校验失败或界面异常。

#### Acceptance Criteria

1. THE GateValidator SHALL 使 STAGE1_MANDATORY_GATE_NODES 与 PromptAssembler 闸门提示文本中列出的强制节点集合完全一致。
2. THE PromptAssembler SHALL 将「必须包含……共 N 条」描述更新为与改造后 STAGE1_MANDATORY_GATE_NODES 数量一致。
3. THE DecisionNodeEngine SHALL 使程序填充节点产生与校验器、归一化器、UI 期望相同的结构：`node_id`、`question`、`answer` ∈ {是, 否, 中性, 等待, 不适用}、非空 `reason`、形如 `K50-K1` 或 `K1` 的 `bar_range`，以及方向/分类节点的 `branch`。
4. THE DecisionNodeEngine SHALL 使程序填充节点满足 `validate_gate_result_consistency`、`validate_stage1_coherence` 与 `validate_stage2_trace_consistency` 的顺序与枚举约束。
5. WHEN 渲染合并后的 `gate_trace` 与 `decision_trace`，THE DecisionFlowUI SHALL 正确显示程序填充节点的 `answer` 颜色、`branch` 中文标签与 `bar_range` 依据。
6. THE PromptAssembler SHALL 将闸门来源引用更新为实际存在的源（`二元决策.txt` 与内置提示文本），不再引用不存在的 `二元决策_闸门.txt`。

### Requirement 8：安全与行为保持

**User Story:** 作为风控负责人，我希望程序判定不削弱任何安全闸门，以便 token 节省不会带来更激进的交易。

#### Acceptance Criteria

1. WHEN PreflightDataGate 判定数据不足（§1.1 = `否`），THE submit() 流水线 SHALL 不调用阶段一/阶段二 AI、不加载策略文件，并返回数据不足错误结果（InsufficientDataError），其保守程度不弱于改造前「不交易/等待」的行为（绝不因此产生任何交易动作）。
2. WHERE 程序判定某节点为阻断结果（如 §9.3 过长、§9.5 无跟随导致放弃、§1.1 数据不足由前置闸门拦截并报错），THE DecisionNodeEngine SHALL 保持等待/不下单/报错的保守结果，不得将原本的「不交易」转为「交易」。
3. THE OrderMethodRouter SHALL 保持「§10.3 不通过或 §14 触犯 → `order_type=不下单`」的安全约束不被绕过。
4. THE DecisionNodeEngine SHALL 不因将节点从 AI 改为程序判定而放宽 §14 禁止行为清单的任一约束。
5. THE DecisionNodeEngine SHALL 不允许受控覆盖（Requirement 11）绕过任一安全闸门（§1.1 数据不足→前置闸门报错（不调用 AI）、§10.3 不通过→`不下单`、§14 触犯→`不下单`）。
6. WHERE 覆盖目标为安全闸门相关结论，THE DecisionNodeEngine SHALL 仅接受朝更保守方向的覆盖（如将「下单」改为「不下单/等待」），并拒绝任何朝更激进方向的覆盖（如将「数据不足报错」改为「足够、下单」，或将「不下单」改为任一下单类型）。
7. THE PA_Agent SHALL 使凡属硬性前置条件（数据充足度、数据质量）的程序权威判定在调用 AI 之前完成，不得在 AI 之后才纠正；属于「对已有足够数据的分析结论」的程序判定节点（§2.3、§2.4、§9.x、§11）可继续在归一化阶段（AI 之后）填充。

### Requirement 9：Token 减少（可测量目标）

**User Story:** 作为成本负责人，我希望减少 AI 在 trace 中需要生成的节点数量，以便降低调用成本。

#### Acceptance Criteria

1. THE PromptAssembler SHALL 从阶段一/阶段二提示中移除所有已改为程序判定节点（§0.1、§0.2、§1.1、§2.3、§2.4、§9.1、§9.2、§9.3、§9.5、§11.1–§11.4）的输出要求。
2. WHEN AI 完成一次阶段一分析，THE 阶段一 SHALL 使 AI 需生成的强制闸门节点数量由 10（§0.1、§0.2、§1.1、§1.2、§1.3、§2.1、§2.2、§2.3、§2.4、§2.5）减少为 5（§1.2、§1.3、§2.1、§2.2、§2.5）。
3. WHEN AI 完成一次阶段二分析，THE 阶段二 SHALL 使 §9.1、§9.2、§9.3、§9.5 与 §11.1–§11.4 共 8 个节点不再由 AI 生成。
4. WHERE AI 未提交任何受控覆盖（Requirement 11），THE 阶段一/阶段二 SHALL 维持上述 token 节省目标，即默认情况下 AI 直接采纳程序判定、不重复输出已改造节点。
5. THE 受控覆盖 SHALL 被视为低频例外，其额外 token（`node_id`、新 `answer`/`branch`、`override_reason`）不计入常态 token 预算。
6. WHEN PreflightDataGate 判定数据不足，THE submit() 流水线 SHALL 完全不调用阶段一 AI 与阶段二 AI，实现比「AI 仍被调用但少写若干节点」更彻底的 token 节省（数据不足时零 AI token 消耗）。

### Requirement 10：非功能性需求——测试与可复现性

**User Story:** 作为开发者，我希望现有测试不被破坏且程序判定输出可复现，以便本改造可安全合入。

#### Acceptance Criteria

1. THE DecisionNodeEngine SHALL 对相同的 KlineFrame 输入产生完全相同的节点判定输出（确定性、可复现）。
2. THE DecisionNodeEngine SHALL 复用既有确定性特征（`compute_kline_geometry_features`、EMA20、ATR14），不引入随机性或外部状态。
3. WHEN 运行既有测试套件，THE 改造 SHALL 不引入新的测试失败（除针对节点来源变更而更新的断言外）。
4. WHERE 测试覆盖 `gate_trace`/`decision_trace` 一致性，THE 测试套件 SHALL 新增对程序填充节点（§1.1、§2.3、§2.4、§9.1、§9.2、§9.3、§9.5、§11.1–§11.4）的回归测试。

### Requirement 11：AI 受控覆盖程序判定

**User Story:** 作为交易分析使用者，我希望 AI 能复核程序的判定，并在具备明确结构性理由时受控地修改程序判错的节点，以便在保留 token 节省的同时不被程序的规则盲点拖累，且不削弱任何安全约束。

程序判定节点按覆盖权限分为三类：

- **锁定节点（不可覆盖）**：§1.1（K 线数量是否 ≥ 20，由 PreflightDataGate 在调用 AI 之前判定）、§9.1（信号 K 线是否已收盘）。
- **可受控覆盖节点（允许受控覆盖）**：§2.3、§2.4、§9.2、§9.3、§11.1–§11.4。
- **安全闸门（单向覆盖，仅可更保守）**：§1.1 数据不足→前置闸门报错（不调用 AI）、§10.3 不通过→`不下单`、§14 触犯→`不下单` 等安全相关结论。

#### Acceptance Criteria

1. THE DecisionNodeEngine SHALL 对每个程序判定节点给出权威默认判定（`answer`、必要时 `branch`、非空 `reason`）。
2. WHERE AI 未提交覆盖，THE DecisionNodeEngine SHALL 直接采纳程序判定，AI 无需重复输出该节点。
3. WHEN AI 提交一个覆盖，THE 覆盖 SHALL 包含被覆盖节点的 `node_id`、AI 主张的新 `answer`（必要时新 `branch`）、以及非空的 `override_reason`。
4. IF AI 提交的覆盖缺少 `override_reason` 或 `override_reason` 为空，THEN THE DecisionNodeEngine SHALL 拒绝该覆盖并保留程序原始判定。
5. IF AI 试图覆盖锁定节点（§1.1、§9.1），THEN THE DecisionNodeEngine SHALL 忽略 AI 提供的值并以程序自身判定为准。
6. WHEN AI 对可受控覆盖节点（§2.3、§2.4、§9.2、§9.3、§11.1–§11.4）提交带非空 `override_reason` 的覆盖，THE DecisionNodeEngine SHALL 接受该覆盖并以 AI 主张的 `answer`/`branch` 替换程序判定。
7. WHEN 一个覆盖被接受，THE DecisionNodeEngine SHALL 在该 trace 节点留痕：记录程序原始判定值（`program_answer`、必要时 `program_branch`）、AI 覆盖后的值、`override_reason`，并将节点标记 `overridden_by_ai=true`。
8. WHEN AI 覆盖方向相关节点（§2.3），THE DecisionNodeEngine SHALL 使覆盖整体生效（`direction` 字段随 §2.3 `branch` 一并更新）或整体被拒绝，使 `direction`、§2.3 `branch`/`answer` 与 `validate_stage1_coherence` 仍然自洽，不得产生半生效的矛盾状态。
9. WHERE 覆盖目标为安全闸门相关结论，THE DecisionNodeEngine SHALL 仅接受朝更保守方向的覆盖（如将下单类结论改为 `不下单`/`等待`）。
10. IF AI 试图将安全闸门的保守结论改为更激进（如将「数据不足报错」改为「足够、下单」，或将「不下单」改为任一下单类型），THEN THE DecisionNodeEngine SHALL 拒绝该覆盖并保持原保守结论。
11. WHEN 渲染合并后的 `gate_trace`/`decision_trace`，THE DecisionFlowUI SHALL 使被覆盖节点可识别，显示程序原始值（`program_answer`/`program_branch`）、AI 覆盖后的值与 `override_reason`，以便用户事后审计 AI 推翻了哪些判定及是否正确。

### Requirement 12：数据不足前置闸门（Pre-flight Data Gate）

**User Story:** 作为成本与风控负责人，我希望在调用阶段一 AI 之前先做一道确定性数据校验，以便数据不足/质量不足时根本不把数据上传给 AI 分析，直接返回明确的「数据不足」错误，既节省 token 与时间，又避免对垃圾数据产出误导性分析。

> 真实缺陷背景：经核对 `pa_agent/orchestrator/two_stage.py` 的 `submit()` 调用链，改造前 §1.1「数据是否足够」的判定发生在 `normalize_stage1`（阶段一 AI 已返回结果之后），导致数据不足时阶段一 AI 仍被白白调用一次，随后程序才把结果改成等待。本需求要求将该硬性前置校验前移到 AI 调用之前。

#### Acceptance Criteria

1. THE PreflightDataGate SHALL 作为阶段一 AI 调用前的第一道数据校验执行：在 `submit()` 的 Pre-Stage-1 取消检查之后、构建阶段一消息（`build_stage1`）与调用阶段一 AI 之前。
2. THE PreflightDataGate SHALL 校验 `frame.bars` 非空且每根 K 线含合法 OHLC（开/高/低/收字段存在且为合法数值）。
3. THE PreflightDataGate SHALL 校验已收盘 K 线数量不小于 BarCountThreshold（20）。
4. THE PreflightDataGate SHALL 校验 EMA20 与 ATR14 至少有一项含有效（非全 NaN）值。
5. IF 第 2、3 或 4 项校验中任一项失败，THEN THE PreflightDataGate SHALL 终止流水线，不调用阶段一 AI，也不调用阶段二 AI，并返回数据不足错误 record（InsufficientDataError）。
6. WHEN PreflightDataGate 终止流水线，THE submit() SHALL 发出一个可被 DecisionFlowUI 识别为「数据不足」的事件信号（参考 `OrchestratorEvent`，如复用 `Stage1Failed` 或新增专用数据不足事件——具体事件枚举为设计细节）。
7. THE 数据不足错误 record SHALL 携带独立的错误类型标识（如 `exception.type="insufficient_data"` 或等价 `reason`），使其可与 `network_error`（网络错误）、`validation_error`（校验错误）相区分，便于 DecisionFlowUI 展示与历史记录过滤。
8. THE PreflightDataGate SHALL 在任何校验失败路径下都不调用阶段一 AI、也不调用阶段二 AI（绝不向任何 AI 上传数据）。
9. THE PreflightDataGate SHALL 为确定性纯校验：对相同的 `frame` 必得相同结论，不引入随机性或外部状态。
10. WHERE 全部校验通过，THE PreflightDataGate SHALL 放行，使 `submit()` 按既有流程构建阶段一消息并调用阶段一 AI。
