# 实现任务：确定性决策节点（deterministic-decision-nodes）

## 任务列表

- [x] 1. 基础数据结构与常量（decision_nodes.py 骨架）
  - [x] 1.1 创建 pa_agent/ai/decision_nodes.py，定义 PreflightResult、NodeFill 数据类
  - [x] 1.2 定义常量：BAR_COUNT_THRESHOLD=20、DIRECTION_WINDOW=20、ALWAYS_IN_WINDOW=20、ALWAYS_IN_SAME_SIDE_RATIO=0.7、SIGNAL_BAR_LONG_ATR_RATIO=2.0、EMA_SLOPE_LOOKBACK=10
  - [x] 1.3 定义覆盖权限集合：LOCKED_NODES、OVERRIDABLE_NODES、SAFETY_GATE_NODES

- [x] 2. PreflightDataGate（check_preflight_data 纯函数）
  - [x] 2.1 实现 check_preflight_data(frame) -> PreflightResult，按顺序执行三项校验：bars 非空且 OHLC 合法、已收盘 K 线数 ≥ 20、EMA20/ATR14 至少一项含非 NaN 值
  - [x] 2.2 实现健壮性降级：畸形输入不崩溃，倾向于判定数据不足（保守）
  - [x] 2.3 编写单元测试：三类数据不足各触发对应 failed_check，充足合格帧 → ok=True，边界 n=19/n=20
  - [x] 2.4 编写 hypothesis 属性测试（Property 1）：前置数据闸门边界与确定性

- [x] 3. Orchestrator 集成 PreflightDataGate
  - [x] 3.1 在 pa_agent/util/threading.py 的 OrchestratorEvent 枚举中新增 InsufficientData = auto()
  - [x] 3.2 在 pa_agent/orchestrator/two_stage.py 的 submit() 中、Step 2 取消检查之后、Step 3 on_event(Stage1Started) 之前插入 PreflightDataGate 调用
  - [x] 3.3 命中数据不足时：写 exception={type:"insufficient_data", stage:"preflight", failed_check, message}，save_partial(record, "insufficient_data")，on_event(InsufficientData)，return record
  - [x] 3.4 编写集成测试（Property 1b）：数据不足时 AI client 零调用，返回 record.exception.type=="insufficient_data"，stage1_response is None

- [x] 4. DecisionNodeEngine 阶段一判定器
  - [x] 4.1 实现 judge_data_sufficiency(frame) -> NodeFill：数据已充足前提下填充 §1.1=是
  - [x] 4.2 实现 judge_direction(frame) -> tuple[str, NodeFill]：EMA20 斜率 + 收盘重心 + 波段结构三信号投票，score≥+2→bullish，≤-2→bearish，否则 neutral；填充 §2.3 节点
  - [x] 4.3 实现 judge_always_in(frame) -> NodeFill：近 N 根同侧收盘占比 ≥ 0.7 + EMA 斜率，判定 AIL/AIS/否；填充 §2.4 节点；**增加短窗口（近5根）背离预警：全窗口 AIL/AIS 但近5根同侧占比<40% 时，在 reason 中追加 ⚠️ 预警文本，供 AI 提交覆盖时引用**
  - [x] 4.4 实现 build_program_trace_node(fill, tree) -> dict：question 取自 node_label，保证所有必填字段合法
  - [x] 4.5 实现 DecisionNodeEngine.apply_stage1(out, frame)：调用三个判定器，填充 §1.1/§2.3/§2.4，写入 direction 字段
  - [x] 4.6 编写单元测试（Property 2/3/4/5）：方向映射、§2.3 与 direction 一致性、归一化幂等、Always In 映射

- [x] 5. DecisionNodeEngine 阶段二判定器
  - [x] 5.1 实现 SignalBarJudge：§9.1 恒=是；§9.2 依 bar_type 与 order_direction 比对；§9.3 依 range_atr_ratio > 2.0 判过长（NaN 保守置是）
  - [x] 5.2 实现 FollowThroughJudge：§9.5 依 follow_through_1_2 映射（yes→是，failed/no→否，pending→等待）
  - [x] 5.3 实现 OrderMethodRouter：cycle_position → 下单方式映射表；不交易优先；突破单保全与 basis 校验；不凭空造突破单
  - [x] 5.4 实现 DecisionNodeEngine.apply_stage2(out, frame, stage1_json)：调用 §9/§11 判定器，gate_shortcircuited 时直接返回
  - [x] 5.5 编写单元测试（Property 6/7/8/9/10）：§9.2 方向映射、§9.3 边界、§9.5 映射、§11 路由映射、安全保持

- [x] 6. OverrideArbiter（受控覆盖裁决）
  - [x] 6.1 实现 _conservativeness_rank(node_id, answer) -> int：为安全闸门定义保守度偏序
  - [x] 6.2 实现 write_override_trace(node, override)：写留痕字段 program_answer/program_branch/override_reason/overridden_by_ai=True
  - [x] 6.3 实现 merge_program_nodes(trace, program_nodes) -> list：按 node_id 覆盖合并，程序节点覆盖 AI 节点
  - [x] 6.4 实现 apply_overrides(program_nodes, node_overrides, out, stage)：六条裁决规则（结构校验→锁定→缺理由→安全闸门→§2.3 一致性→接受）；§2.3 覆盖被接受时同步 out["direction"]；**§2.4 覆盖被接受时调用 _sync_always_in_from_24_override 同步 bar_analysis.always_in（AIL→"long"/AIS→"short"/否→"neutral"），消除字段自相矛盾**
  - [x] 6.5 将 apply_overrides 集成到 apply_stage1/apply_stage2 中（程序判定 → 应用覆盖 → 合并）
  - [x] 6.6 编写单元测试（Property 15–22）：无覆盖恒等、锁定不可覆盖、缺理由拒绝、接受即替换+留痕、§2.3 整体一致性、安全单向、畸形降级、覆盖幂等

- [x] 7. 归一化器集成
  - [x] 7.1 修改 pa_agent/ai/stage1_normalizer.py：在 normalize_stage1 中、route_strategy_files 之前调用 DecisionNodeEngine.apply_stage1(out, kline_frame)；移除旧的 §1.1 数据不足分支（n<20→wait→截断 gate_trace）
  - [x] 7.2 修改 pa_agent/ai/stage2_normalizer.py：为 normalize_stage2 增加 stage1_json 形参（默认 None）；在 _coerce_decision_when_trade_metrics_fail 之后、normalize_stage2_traces 之前调用 DecisionNodeEngine.apply_stage2(out, kline_frame, stage1_json)
  - [x] 7.3 修改 pa_agent/ai/json_validator.py：normalize_stage2 调用处增加 stage1_json=stage1_json 实参
  - [x] 7.4 编写单元测试（Property 11/12/13/14）：程序填充节点结构合法、全流程校验零错误、判定确定性、归一化幂等

- [x] 8. 校验器与 UI 更新
  - [x] 8.1 修改 pa_agent/ai/coherence_checks.py：STAGE1_MANDATORY_GATE_NODES 移除 "0.1"/"0.2"，最终为 ("1.1","1.2","1.3","2.1","2.2","2.3","2.4","2.5")
  - [x] 8.2 修改 pa_agent/ai/decision_tree.py：_BRANCH_DISPLAY_ZH 增加 "AIL":"Always In 多头"、"AIS":"Always In 空头"
  - [x] 8.3 修改 pa_agent/ai/prompts/schemas.py：新增 _NODE_OVERRIDE_ITEM；STAGE1_SCHEMA/STAGE2_SCHEMA 增加可选 node_overrides 数组；_TRACE_ITEM 增加可选留痕字段（program_answer/program_branch/override_reason/overridden_by_ai）
  - [x] 8.4 修改 pa_agent/gui/decision_flow_viz.py：被覆盖节点（overridden_by_ai=True）显示 AI 覆盖徽标/区别色边框，tooltip 含 program_answer/override_reason；数据不足 record（exception.type=="insufficient_data"）显示「数据不足，无法分析」并与网络/校验错误区分
  - [x] 8.5 编写单元测试：STAGE1_MANDATORY_GATE_NODES 等于新集合；_BRANCH_DISPLAY_ZH 含 AIL/AIS；schema 含 node_overrides 且不破坏现有校验；UI 渲染被覆盖节点与数据不足 record

- [x] 9. 提示词文本更新
  - [x] 9.1 修改 pa_agent/ai/prompt_assembler.py：删除 JSON 示例中的 0.1 节点，换成 1.2 节点示例
  - [x] 9.2 更新「必须包含节点 0.1、0.2、1.1…2.5 共 10 条」→「必须包含节点 1.2、1.3、2.1、2.2、2.5 共 5 条（§1.1/§2.3/§2.4 由程序判定，AI 不输出）」
  - [x] 9.3 修正《二元决策_闸门.txt》引用为实际存在的 二元决策.txt 与内置提示文本
  - [x] 9.4 移除阶段一提示中 §0.1/§0.2 强制评估要求；标注 §1.1/§2.3/§2.4「由程序判定，勿输出」
  - [x] 9.5 移除阶段二提示中 §9.1/§9.2/§9.3/§9.5 与 §11.1–§11.4 的输出要求；保留 §9.0/§9.4/§9.6/§9.7 与 §10 由 AI 判定
  - [x] 9.6 新增 node_overrides 提示说明（默认不输出被改造节点；覆盖时提交带 override_reason 的条目；锁定节点不可覆盖；安全闸门仅更保守；§2.3 自洽；§11 横向切换）；JSON 示例加入可选 node_overrides（注明可省略）；**收紧 §2.3/§2.4 覆盖门槛：各列出三项全部满足才允许提交的具体条件，§2.4 要求先确认 reason 中是否有 ⚠️ 背离预警，override_reason 须含具体根数数据和推翻全窗口判定的理由；_render_program_prefill_hint 末尾提示同步更新**
  - [x] 9.7 更新增量分析文本（0.1–2.5 → 改造后集合）
  - [x] 9.8 编写单元测试：assemble 后断言「共 5 条」、无《二元决策_闸门.txt》引用、含 node_overrides 说明

- [x] 10. 端到端回归测试
  - [x] 10.1 运行既有测试套件（pytest），记录因节点来源变更需更新的断言
  - [x] 10.2 更新受影响的现有测试断言（gate_trace 节点来源、STAGE1_MANDATORY_GATE_NODES 等）
  - [x] 10.3 新增程序填充节点的回归测试：§1.1/§2.3/§2.4 在 gate_trace 中恒存在且结构合法；§9.1/§9.2/§9.3/§9.5/§11.x 在 decision_trace 中恒存在且结构合法
  - [x] 10.4 新增数据不足前置拦截的端到端测试：三类数据不足帧 → record.exception.type=="insufficient_data"，stage1_response is None，无交易决策
