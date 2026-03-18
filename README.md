# OrgClaw

**OpenClaw 的组织知识联邦系统**

支持多层级经验沉淀：个人 → 团队 → 组织 → 社区

---

## 🎯 核心能力

### 1. 自动经验提取
```python
from orgclaw import ExperienceExtractor

extractor = ExperienceExtractor(repo_path=".")
experience = extractor.extract_from_task(
    task_id="task-123",
    task_description="Fixed memory leak in user service",
    commit_hash="abc123",
)
```

### 2. 质量评分
```python
from orgclaw import ExperienceScorer

scorer = ExperienceScorer()
score = scorer.score(experience)

print(f"Overall: {score.overall}")
print(f"Completeness: {score.completeness}")
print(f"Reusability: {score.reusability}")
```

### 3. 语义存储与检索
```python
from orgclaw import KnowledgeStore

store = KnowledgeStore()
store.add_experience(experience)

# Semantic search
results = store.query("memory leak debugging", n_results=5)
```

### 4. OpenClaw 集成
```python
# Automatically triggered when Agent task completes
skill = OrgClawSkill()
result = skill.on_task_complete(task_result)
```

---

## 📦 安装

```bash
# Install as OpenClaw skill
openclaw skill install orgclaw

# Or manually
git clone https://github.com/conpera/orgclaw.git
cd orgclaw
pip install -e .
```

---

## 🚀 使用

### CLI

```bash
# Extract experience from task
orgclaw extract task-123 \
  --description "Fixed race condition in cache" \
  --commit abc123

# Search knowledge base
orgclaw search "memory leak" --limit 5

# View stats
orgclaw stats
```

### OpenClaw Integration

```yaml
# .openclaw/config.yaml
skills:
  claw-engine:
    auto_extract: true
    quality_threshold: 0.75
```

---

## 🏗️ 架构

```
orgclaw/
├── orgclaw/               # 核心引擎
│   ├── analyzer/          # 经验分析
│   │   ├── extractor.py       # 从任务提取
│   │   └── quality_scorer.py  # 质量评分
│   ├── storage/           # 存储层
│   │   └── vector_store.py    # 向量存储
│   └── cli/               # 命令行
│       └── claw.py
├── .openclaw/
│   └── skill.py           # OpenClaw 集成
└── tests/
```

---

## 🔄 工作流程

```
Agent 完成任务
    ↓
Claw Engine 自动分析
    ├── 提取 git diff
    ├── 识别解决模式
    ├── 生成结构化经验
    └── 质量评分 (0-1)
    ↓
Quality >= 0.75?
    ├── Yes → 存入知识库
    └── No  → 返回改进建议
    ↓
后续 Agent 可检索相关经验
```

---

## 📊 经验质量维度

| 维度 | 说明 | 权重 |
|------|------|------|
| Completeness | 信息完整性 | 25% |
| Specificity | 具体程度 | 25% |
| Actionability | 可执行性 | 25% |
| Reusability | 可复用性 | 25% |

---

## 🤝 知识联邦层级

```
个人经验 (Personal)
    ↓ 分享
团队知识 (Team)
    ↓ 验证
组织模式 (Organization) ← orgclaw 核心
    ↓ 开源
社区共享 (Community)
```

- **orgclaw**: 组织知识联邦引擎（本仓库）
- **个人层**: `~/.orgclaw/personal/`
- **项目层**: `项目/.orgclaw/`
- **组织层**: 跨项目共享模式

---

## 📝 License

MIT
