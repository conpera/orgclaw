#!/usr/bin/env python3
"""
OrgClaw Skill Auto-Installer
Usage: python3 install.py [--user|--global]
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from urllib.request import urlretrieve
import tempfile
import zipfile


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_step(step, message):
    print(f"\n{Colors.BLUE}[{step}]{Colors.END} {message}")


def print_success(message):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def print_error(message):
    print(f"{Colors.RED}✗{Colors.END} {message}")


def run_command(cmd, check=True):
    """Run shell command."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def install_orgclaw(install_type="user"):
    """Main installation process."""
    
    print(f"""
{Colors.GREEN}╔═══════════════════════════════════════════════════════════╗
║                 OrgClaw Skill Installer                    ║
║            Knowledge Federation for OpenClaw              ║
╚═══════════════════════════════════════════════════════════╝{Colors.END}
""")
    
    # Step 1: Check Python version
    print_step("1/7", "Checking Python version...")
    if sys.version_info < (3, 11):
        print_error("Python 3.11+ required")
        sys.exit(1)
    print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Step 2: Determine installation paths
    print_step("2/7", "Setting up installation paths...")
    
    if install_type == "user":
        # User installation
        home = Path.home()
        skill_dir = home / ".openclaw" / "skills" / "orgclaw"
        config_dir = home / ".openclaw"
        personal_dir = home / ".orgclaw" / "personal"
    else:
        # Global installation (not recommended)
        print_error("Global installation not yet supported")
        sys.exit(1)
    
    print_success(f"Skill directory: {skill_dir}")
    print_success(f"Config directory: {config_dir}")
    
    # Step 3: Download/Copy orgclaw source
    print_step("3/7", "Installing OrgClaw source...")
    
    if skill_dir.exists():
        print_warning(f"Existing installation found at {skill_dir}")
        response = input("Overwrite? [y/N]: ").lower()
        if response == 'y':
            shutil.rmtree(skill_dir)
        else:
            print("Installation cancelled")
            sys.exit(0)
    
    # Check if running from source directory
    current_dir = Path(__file__).parent
    if (current_dir / "orgclaw").exists():
        # Local installation
        print("Installing from local source...")
        shutil.copytree(current_dir, skill_dir, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', '.DS_Store', 'venv'
        ))
    else:
        # Download from GitHub
        print("Downloading from GitHub...")
        url = "https://github.com/conpera/orgclaw/archive/refs/heads/main.zip"
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "orgclaw.zip"
            urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            
            extracted_dir = Path(tmpdir) / "orgclaw-main"
            shutil.copytree(extracted_dir, skill_dir)
    
    print_success(f"Installed to {skill_dir}")
    
    # Step 4: Install Python dependencies
    print_step("4/7", "Installing dependencies...")
    
    req_file = skill_dir / "requirements.txt"
    if req_file.exists():
        success, stdout, stderr = run_command(
            f"{sys.executable} -m pip install -r {req_file} --user -q"
        )
        if success:
            print_success("Dependencies installed")
        else:
            print_warning(f"Some dependencies may have failed: {stderr}")
    else:
        # Create minimal requirements
        minimal_reqs = [
            "GitPython>=3.1.0",
            "chromadb>=0.4.0",
            "requests>=2.28.0",
            "pyyaml>=6.0",
            "click>=8.0",
            "rich>=13.0",
        ]
        req_file.write_text("\n".join(minimal_reqs))
        print_warning("Created minimal requirements.txt")
    
    # Step 5: Create directories
    print_step("5/7", "Creating directories...")
    
    personal_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "hooks").mkdir(parents=True, exist_ok=True)
    
    print_success(f"Personal storage: {personal_dir}")
    
    # Step 6: Setup OpenClaw configuration
    print_step("6/7", "Configuring OpenClaw...")
    
    config_file = config_dir / "config.yaml"
    
    orgclaw_config = """
# OrgClaw Skill Configuration
skills:
  orgclaw:
    enabled: true
    auto_extract: true           # Auto-extract experience on task completion
    quality_threshold: 0.4       # Minimum quality to save (0.0-1.0)
    min_lines_changed: 5         # Minimum lines changed to trigger extraction
    enable_patterns: true        # Link with conpera-patterns
    personal_dir: ~/.orgclaw/personal
    notifications:
      console: true              # Show console notifications
      
# Hook configuration
hooks:
  post_task: ~/.openclaw/skills/orgclaw/hooks/post_task.py
"""
    
    if config_file.exists():
        # Merge with existing config
        existing = config_file.read_text()
        if "orgclaw:" not in existing:
            # Append orgclaw config
            with open(config_file, "a") as f:
                f.write(orgclaw_config)
            print_success("Appended to existing config")
        else:
            print_warning("OrgClaw config already exists, skipping")
    else:
        # Create new config
        config_file.write_text(orgclaw_config)
        print_success("Created new config file")
    
    # Step 7: Install CLI command
    print_step("7/7", "Setting up CLI...")
    
    # Create wrapper script
    cli_wrapper = skill_dir / "orgclaw"
    cli_content = f"""#!/bin/bash
# OrgClaw CLI wrapper
export PYTHONPATH="{skill_dir}:$PYTHONPATH"
{sys.executable} -m orgclaw.cli.claw "$@"
"""
    cli_wrapper.write_text(cli_content)
    cli_wrapper.chmod(0o755)
    
    # Add to PATH if not already
    shell_rc = None
    if "zsh" in os.environ.get("SHELL", ""):
        shell_rc = Path.home() / ".zshrc"
    elif "bash" in os.environ.get("SHELL", ""):
        shell_rc = Path.home() / ".bashrc"
    
    if shell_rc and shell_rc.exists():
        rc_content = shell_rc.read_text()
        if str(skill_dir) not in rc_content:
            with open(shell_rc, "a") as f:
                f.write(f'\n# OrgClaw CLI\nexport PATH="{skill_dir}:$PATH"\n')
            print_success(f"Added to PATH in {shell_rc}")
    
    # Summary
    print(f"""
{Colors.GREEN}╔═══════════════════════════════════════════════════════════╗
║              Installation Complete! 🎉                     ║
╚═══════════════════════════════════════════════════════════╝{Colors.END}

OrgClaw Skill has been installed successfully!

📁 Installation Location:
   Skill:  {skill_dir}
   Config: {config_file}
   Data:   {personal_dir}

🚀 Quick Start:
   1. Reload shell or run: source ~/.zshrc (or ~/.bashrc)
   2. Test: orgclaw --version
   3. Check status: orgclaw stats
   4. Run an Agent task and watch for [OrgClaw] output!

📖 Documentation:
   GitHub: https://github.com/conpera/orgclaw
   Help:   orgclaw --help

💡 Next Steps:
   - Run an OpenClaw task
   - Check extracted experiences: orgclaw stats
   - View patterns: orgclaw patterns "api"

{Colors.YELLOW}Note:{Colors.END} If PATH changes don't take effect, restart your terminal.
""")


def verify_installation():
    """Verify the installation."""
    print("\n" + "=" * 60)
    print("Verifying Installation...")
    print("=" * 60)
    
    checks = [
        ("Config file", Path.home() / ".openclaw" / "config.yaml"),
        ("Skill directory", Path.home() / ".openclaw" / "skills" / "orgclaw"),
        ("Personal storage", Path.home() / ".orgclaw" / "personal"),
        ("Hook file", Path.home() / ".openclaw" / "skills" / "orgclaw" / "hooks" / "post_task.py"),
    ]
    
    all_ok = True
    for name, path in checks:
        if path.exists():
            print_success(f"{name}: {path}")
        else:
            print_error(f"{name}: {path} (MISSING)")
            all_ok = False
    
    return all_ok


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Install OrgClaw Skill")
    parser.add_argument(
        "--user", action="store_true", default=True,
        help="Install for current user (default)"
    )
    parser.add_argument(
        "--global", dest="global_install", action="store_true",
        help="Install system-wide (requires sudo)"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Verify existing installation"
    )
    
    args = parser.parse_args()
    
    try:
        if args.verify:
            if verify_installation():
                print("\n✅ All checks passed!")
                sys.exit(0)
            else:
                print("\n❌ Some checks failed")
                sys.exit(1)
        
        install_type = "global" if args.global_install else "user"
        install_orgclaw(install_type)
        
        # Run verification
        if verify_installation():
            print("\n✅ Installation verified successfully!")
        else:
            print_warning("Installation may have issues, please check")
            
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
