# OrgClaw for OpenClaw

让 OpenClaw 自动收集和沉淀经验。

## 快速安装

### 方式 1: 一行命令 (推荐)

```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/conpera/orgclaw/main/setup.py)
```

### 方式 2: 手动安装

```bash
cd ~/.openclaw/skills
git clone https://github.com/conpera/orgclaw.git
python3 orgclaw/setup.py
```

### 方式 3: PyPI (即将支持)

```bash
pip install orgclaw
```

## 验证安装

```bash
orgclaw --version    # 应显示版本
orgclaw stats        # 查看经验统计
```

## 使用

安装完成后，**无需任何配置**，正常使用 OpenClaw 即可：

```bash
# 运行任意 OpenClaw 任务
openclaw run "Fix memory leak in cache"

# 你会看到:
# [OpenClaw] Task completed successfully!
# [OrgClaw] ✅ Experience auto-saved (quality: 0.52)
```

经验会自动保存到 `~/.orgclaw/personal/`。

## 查看收集的经验

```bash
# 统计
orgclaw stats

# 搜索
orgclaw search "memory leak"

# 查看模式
orgclaw patterns "api"
```

## 工作原理

```
OpenClaw 任务完成
    ↓
自动触发 OrgClaw Hook
    ↓
提取经验 → 质量评分 → 自动保存
    ↓
存储到 ~/.orgclaw/personal/
```

## 配置

编辑 `~/.openclaw/config.yaml`:

```yaml
skills:
  orgclaw:
    enabled: true
    auto_extract: true           # 自动提取
    quality_threshold: 0.4       # 保存阈值 (0-1)
    min_lines_changed: 5         # 最小变更行数
```

## 项目结构

```
~/.openclaw/
├── skills/
│   └── orgclaw/          # 本仓库代码
├── config.yaml           # OpenClaw 配置
└── hooks/
    └── post_task.py      # 自动触发钩子

~/.orgclaw/
└── personal/             # 你的经验库
    └── exp-xxx.json
```

## 功能特性

- ✅ **全自动**: 任务完成后自动提取，无需干预
- ✅ **质量评分**: 4 维度评分，筛选高价值经验
- ✅ **智能分类**: 自动识别 bug_fix/refactor/feature/optimization
- ✅ **模式关联**: 关联 conpera-patterns 最佳实践
- ✅ **语义搜索**: 向量存储，支持相似度检索

## 卸载

```bash
rm -rf ~/.openclaw/skills/orgclaw
rm -rf ~/.orgclaw
# 从 ~/.openclaw/config.yaml 中删除 orgclaw 配置
```

## 相关项目

- [conpera-patterns](https://github.com/conpera/conpera-patterns) - 团队模式库
- [OpenClaw](https://github.com/openclaw/openclaw) - Agent 运行时

## 许可证

MIT
