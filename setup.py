#!/usr/bin/env python3
"""
OrgClaw Quick Setup for OpenClaw Users
One command to enable automatic experience extraction.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║            OrgClaw Quick Setup for OpenClaw               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if running in OpenClaw environment
    openclaw_dir = Path.home() / ".openclaw"
    if not openclaw_dir.exists():
        print("⚠️  OpenClaw not detected. Please install OpenClaw first.")
        print("   https://github.com/openclaw/openclaw")
        sys.exit(1)
    
    print("✅ OpenClaw detected")
    
    # Setup paths
    skill_dir = openclaw_dir / "skills" / "orgclaw"
    config_file = openclaw_dir / "config.yaml"
    personal_dir = Path.home() / ".orgclaw" / "personal"
    
    # Create directories
    skill_dir.mkdir(parents=True, exist_ok=True)
    personal_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directories created")
    
    # Download orgclaw
    if not (skill_dir / "orgclaw").exists():
        print("\n📦 Downloading OrgClaw...")
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/conpera/orgclaw.git",
            str(skill_dir)
        ], check=True, capture_output=True)
        print("✅ OrgClaw downloaded")
    else:
        print("✅ OrgClaw already exists")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    req_file = skill_dir / "requirements.txt"
    if req_file.exists():
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"
        ], check=False)
    print("✅ Dependencies installed")
    
    # Update OpenClaw config
    print("\n⚙️  Configuring OpenClaw...")
    
    orgclaw_config = """
# OrgClaw - Automatic experience extraction
skills:
  orgclaw:
    enabled: true
    auto_extract: true
    quality_threshold: 0.4
    min_lines_changed: 5
    personal_dir: ~/.orgclaw/personal

hooks:
  post_task: ~/.openclaw/skills/orgclaw/hooks/post_task.py
"""
    
    if config_file.exists():
        content = config_file.read_text()
        if "orgclaw:" not in content:
            with open(config_file, "a") as f:
                f.write(orgclaw_config)
            print("✅ Config appended to existing file")
        else:
            print("✅ Config already exists")
    else:
        config_file.write_text(orgclaw_config.lstrip())
        print("✅ Config file created")
    
    # Create CLI wrapper
    cli_wrapper = skill_dir / "orgclaw"
    cli_content = f"""#!/bin/bash
export PYTHONPATH="{skill_dir}:$PYTHONPATH"
{sys.executable} -m orgclaw.cli.claw "$@"
"""
    cli_wrapper.write_text(cli_content)
    cli_wrapper.chmod(0o755)
    
    # Add to PATH
    shell_rc = None
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        shell_rc = Path.home() / ".zshrc"
    elif "bash" in shell:
        shell_rc = Path.home() / ".bashrc"
    
    if shell_rc and shell_rc.exists():
        rc_content = shell_rc.read_text()
        path_line = f'export PATH="{skill_dir}:$PATH"'
        if path_line not in rc_content:
            with open(shell_rc, "a") as f:
                f.write(f"\n# OrgClaw CLI\n{path_line}\n")
            print(f"✅ Added to PATH in {shell_rc}")
    
    # Done
    print("""
╔═══════════════════════════════════════════════════════════╗
║                    ✅ Setup Complete!                      ║
╚═══════════════════════════════════════════════════════════╝

OrgClaw is now integrated with OpenClaw!

📍 Locations:
   Skill:    ~/.openclaw/skills/orgclaw/
   Config:   ~/.openclaw/config.yaml
   Storage:  ~/.orgclaw/personal/

🚀 Usage:
   1. Run any OpenClaw task
   2. Watch for: [OrgClaw] ✅ Experience auto-saved
   3. View: orgclaw stats

📝 Manual commands:
   orgclaw stats              # View statistics
   orgclaw search "keyword"   # Search experiences
   orgclaw patterns "api"     # View related patterns

💡 Tips:
   - Experiences are automatically extracted from tasks
   - High quality ones (≥0.4) are saved automatically
   - Check ~/.orgclaw/personal/ for your knowledge base

Need help? https://github.com/conpera/orgclaw
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
