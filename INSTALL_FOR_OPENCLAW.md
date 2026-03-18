# OrgClaw for OpenClaw - 简化安装方案

## 目标
让 OpenClaw 用户**一行命令**启用经验自动收集。

## 方案对比

### 方案 1: setup.py (当前实现)

```bash
cd ~/.openclaw/skills
git clone https://github.com/conpera/orgclaw.git
python3 orgclaw/setup.py
```

**优点**: 简单直接  
**缺点**: 需要手动 clone

### 方案 2: PyPI + 自动注册 (推荐)

```bash
pip install orgclaw
```

安装后自动：
- 复制代码到 ~/.openclaw/skills/orgclaw/
- 修改 ~/.openclaw/config.yaml
- 创建 CLI 命令

**优点**: 最标准的 Python 方式  
**缺点**: 需要发布到 PyPI

### 方案 3: OpenClaw 内置检测

OpenClaw 启动时自动检测：

```python
# openclaw 启动时
if orgclaw_installed():
    enable_auto_extract()
```

用户只需：
```bash
pip install orgclaw
# 然后正常使用 openclaw
```

**优点**: 零配置  
**缺点**: 需要 OpenClaw 支持

## 推荐: 方案 2 (PyPI)

### 发布到 PyPI

1. **准备 setup.py**

```python
from setuptools import setup, find_packages

setup(
    name="orgclaw",
    version="0.1.0",
    description="Organization knowledge federation for OpenClaw",
    author="Conpera",
    packages=find_packages(),
    install_requires=[
        "GitPython>=3.1.40",
        "chromadb>=0.4.18",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "click>=8.1.7",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "orgclaw=orgclaw.cli.claw:main",
        ],
        "openclaw.plugins": [
            "orgclaw=orgclaw.openclaw_plugin:register",
        ],
    },
    post_install="orgclaw.install:setup_openclaw",
)
```

2. **安装后自动配置**

```python
# orgclaw/install.py
def setup_openclaw():
    """Called after pip install."""
    # 1. 找到 OpenClaw 目录
    openclaw_dir = Path.home() / ".openclaw"
    
    # 2. 创建 hook
    hook_dir = openclaw_dir / "hooks"
    hook_dir.mkdir(exist_ok=True)
    
    # 3. 复制 post_task.py
    import shutil
    from orgclaw import __path__ as orgclaw_path
    shutil.copy(
        Path(orgclaw_path[0]) / "hooks" / "post_task.py",
        hook_dir / "post_task.py"
    )
    
    # 4. 更新 config
    update_openclaw_config()
    
    print("✅ OrgClaw installed! Auto-extraction enabled.")
```

3. **用户使用**

```bash
# 安装
pip install orgclaw

# 完成！自动集成到 OpenClaw

# 使用 OpenClaw 正常运行任务
openclaw run "Fix bug"
# → [OrgClaw] ✅ Experience auto-saved

# 查看收集的经验
orgclaw stats
```

## 备选: 一行命令安装

如果不发布 PyPI，可以用：

```bash
# 方式 1: pip 直接安装 git
pip install git+https://github.com/conpera/orgclaw.git

# 方式 2: curl (当前)
curl -fsSL .../install.py | python3

# 方式 3: wget
wget -qO- .../install.py | python3
```

## 当前推荐

**现在可用**:
```bash
# 下载并运行 setup
python3 <(curl -fsSL https://raw.githubusercontent.com/conpera/orgclaw/main/setup.py)
```

**发布后可用**:
```bash
pip install orgclaw
```

## 实现清单

- [ ] 发布 orgclaw 到 PyPI
- [ ] 添加 setup_openclaw() 自动配置
- [ ] 更新 README 安装说明
- [ ] 测试 pip install 流程
