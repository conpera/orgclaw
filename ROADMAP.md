# OrgClaw Roadmap & TODO

## 已完成 ✅

### Phase 1: 核心引擎 (v0.1.0)
- [x] 经验自动提取
- [x] 质量评分系统 (4维度)
- [x] 模式检测 (bug_fix/refactor/feature/optimization)
- [x] 语义存储 (ChromaDB)
- [x] OpenClaw 集成 (Hook)
- [x] CLI 工具

### Phase 2: 团队层 (v0.2.0)
- [x] TeamManager 团队管理
- [x] 审核工作流 (pending → approved/rejected)
- [x] 团队成员投票
- [x] 团队 CLI 命令
- [x] 团队统计

---

## 待办事项 📋

### Phase 3: 组织层 (v0.3.0) - **暂缓**

**状态**: 低优先级，已创建 GitHub Issue 跟踪

**说明**:
- 组织层通过 [conpera-patterns](https://github.com/conpera/conpera-patterns) 仓库已存在
- 团队库 → 组织库的流程可以手动进行（PR 到 patterns 仓库）
- 不需要在 orgclaw 核心中实现

**GitHub Issue**: [#1 - Organization Layer Integration](https://github.com/conpera/orgclaw/issues/1)

**可能功能** (未来考虑):
- [ ] 自动将高质量团队经验提交到 conpera-patterns
- [ ] 组织级经验搜索
- [ ] 跨团队经验共享

---

## 当前优先级

### 高优先级
- [ ] 真实场景测试 - 在实际 Agent 任务中验证
- [ ] Bug 修复 - 根据测试反馈
- [ ] 文档完善 - 用户使用指南

### 中优先级
- [ ] Web UI - 可视化浏览经验
- [ ] 经验导出/导入
- [ ] 团队邀请系统

### 低优先级
- [ ] 组织层自动集成 (#1)
- [ ] LLM 增强提取
- [ ] 机器学习评分优化

---

## 已知问题

| Issue | 严重程度 | 状态 |
|-------|---------|------|
| 依赖安装复杂 (chromadb/gitpython) | 中 | 待优化 |
| 评分阈值可能需要调优 | 低 | 观察中 |
| Hook 需要 OpenClaw 支持 | 高 | 依赖外部 |

---

## 发布计划

### v0.1.0 (当前)
- ✅ 个人经验自动收集
- ✅ CLI 工具
- ✅ OpenClaw 集成

### v0.2.0 (近期)
- ✅ 团队共享
- 📋 测试验证
- 📋 文档完善

### v0.3.0 (未来)
- 📋 Web UI
- 📋 组织层集成 (#1)
- 📋 PyPI 发布

---

## 贡献指南

想参与开发？查看 [CONTRIBUTING.md](CONTRIBUTING.md)

**当前最需要**:
1. 真实场景测试反馈
2. 文档改进
3. Bug 报告

---

*Last updated: 2026-03-18*
