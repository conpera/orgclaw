# OrgClaw Skill Package

## 目录结构

```
orgclaw-skill/
├── SKILL.md                  # Skill 定义文档
├── install.py               # 自动安装脚本
├── config.yaml              # 默认配置
├── hooks/
│   └── post_task.py         # 任务后处理钩子
├── orgclaw/
│   ├── __init__.py
│   ├── analyzer/
│   ├── storage/
│   ├── auto_extract.py
│   └── cli/
└── tests/
    └── test_skill.py
```

## 使用方式

### 方法 1: 自动安装（推荐）
```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/conpera/orgclaw/main/install.py | python3

# 或本地安装
python3 install.py
```

### 方法 2: OpenClaw 安装
```bash
openclaw skill install conpera/orgclaw
```

### 方法 3: 手动安装
```bash
git clone https://github.com/conpera/orgclaw.git ~/.openclaw/skills/orgclaw
cd ~/.openclaw/skills/orgclaw
pip install -e .
```

## 配置

安装后自动创建 `~/.openclaw/config.yaml`:
```yaml
skills:
  orgclaw:
    enabled: true
    auto_extract: true
    quality_threshold: 0.4
    min_lines_changed: 5
    personal_dir: ~/.orgclaw/personal
```

## 验证安装
```bash
openclaw skill list          # 查看已安装 skills
orgclaw --version           # 查看版本
orgclaw stats               # 查看统计
```
