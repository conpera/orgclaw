#!/usr/bin/env python3
"""
OrgClaw Team Share - 团队经验共享系统

功能：
1. 将个人经验提交到团队库
2. 团队内经验审核流程
3. 团队成员间经验同步
4. 团队级经验检索
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TeamExperience:
    """团队级经验（经过审核的）"""
    id: str
    title: str
    description: str
    category: str
    author: str                          # 贡献者
    team: str                            # 所属团队
    status: str                          # pending | approved | rejected
    reviewers: List[str]                 # 审核人
    votes: Dict[str, str]                # {reviewer: approve/reject}
    quality_score: float
    source_experience_id: str            # 来源个人经验ID
    created_at: str
    updated_at: str
    version: int = 1


class TeamManager:
    """管理团队经验的中心类"""
    
    def __init__(self, team_name: str, base_dir: Optional[Path] = None):
        self.team_name = team_name
        
        if base_dir is None:
            base_dir = Path.home() / ".orgclaw" / "teams"
        
        self.team_dir = base_dir / team_name
        self.pending_dir = self.team_dir / "pending"
        self.approved_dir = self.team_dir / "approved"
        self.rejected_dir = self.team_dir / "rejected"
        
        # 创建目录
        for d in [self.pending_dir, self.approved_dir, self.rejected_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 成员列表
        self.members_file = self.team_dir / "members.json"
        if not self.members_file.exists():
            self._save_members({})
    
    def _save_members(self, members: Dict):
        """保存团队成员列表"""
        with open(self.members_file, 'w') as f:
            json.dump(members, f, indent=2)
    
    def _load_members(self) -> Dict:
        """加载团队成员列表"""
        with open(self.members_file) as f:
            return json.load(f)
    
    def add_member(self, user_id: str, role: str = "member"):
        """添加团队成员"""
        members = self._load_members()
        members[user_id] = {
            "role": role,
            "joined_at": datetime.utcnow().isoformat()
        }
        self._save_members(members)
    
    def submit_to_team(
        self,
        experience: Dict[str, Any],
        submitter: str
    ) -> str:
        """
        将个人经验提交到团队审核
        
        Args:
            experience: 个人经验字典
            submitter: 提交者ID
            
        Returns:
            team_experience_id
        """
        # 生成团队经验ID
        team_exp_id = f"team-{experience['id']}"
        
        # 创建团队经验对象
        team_exp = TeamExperience(
            id=team_exp_id,
            title=experience['title'],
            description=experience['description'],
            category=experience['category'],
            author=submitter,
            team=self.team_name,
            status="pending",
            reviewers=[],
            votes={},
            quality_score=experience.get('quality_score', 0),
            source_experience_id=experience['id'],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # 保存到 pending
        filepath = self.pending_dir / f"{team_exp_id}.json"
        with open(filepath, 'w') as f:
            json.dump(asdict(team_exp), f, indent=2, default=str)
        
        print(f"✅ 经验已提交到团队 '{self.team_name}' 审核队列")
        print(f"   ID: {team_exp_id}")
        print(f"   状态: pending (等待审核)")
        
        return team_exp_id
    
    def review(
        self,
        team_exp_id: str,
        reviewer: str,
        decision: str,  # approve | reject
        comment: str = ""
    ) -> bool:
        """
        审核团队经验
        
        Args:
            team_exp_id: 团队经验ID
            reviewer: 审核人ID
            decision: approve 或 reject
            comment: 审核意见
            
        Returns:
            是否审核完成（达到阈值）
        """
        # 加载待审核经验
        filepath = self.pending_dir / f"{team_exp_id}.json"
        if not filepath.exists():
            print(f"❌ 经验不存在: {team_exp_id}")
            return False
        
        with open(filepath) as f:
            data = json.load(f)
        
        # 更新投票
        data['votes'][reviewer] = decision
        data['reviewers'].append(reviewer)
        data['updated_at'] = datetime.utcnow().isoformat()
        
        # 检查是否达到审核阈值
        members = self._load_members()
        required_votes = max(2, len(members) // 2)  # 至少2票或半数
        
        if len(data['votes']) >= required_votes:
            # 统计投票
            approve_count = sum(1 for v in data['votes'].values() if v == 'approve')
            reject_count = sum(1 for v in data['votes'].values() if v == 'reject')
            
            if approve_count > reject_count:
                # 通过审核
                data['status'] = 'approved'
                self._move_experience(team_exp_id, 'pending', 'approved')
                print(f"✅ 经验已通过审核: {team_exp_id}")
                print(f"   票数: {approve_count} 赞同 / {reject_count} 反对")
            else:
                # 拒绝
                data['status'] = 'rejected'
                self._move_experience(team_exp_id, 'pending', 'rejected')
                print(f"❌ 经验被拒绝: {team_exp_id}")
        
        # 保存更新
        filepath = self.team_dir / data['status'] / f"{team_exp_id}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data['status'] != 'pending'
    
    def _move_experience(self, exp_id: str, from_status: str, to_status: str):
        """移动经验文件"""
        from_dir = self.team_dir / from_status
        to_dir = self.team_dir / to_status
        
        src = from_dir / f"{exp_id}.json"
        dst = to_dir / f"{exp_id}.json"
        
        if src.exists():
            src.rename(dst)
    
    def list_pending(self) -> List[Dict]:
        """列出待审核的经验"""
        pending = []
        for f in self.pending_dir.glob("*.json"):
            with open(f) as fp:
                pending.append(json.load(fp))
        return sorted(pending, key=lambda x: x['created_at'])
    
    def list_approved(self) -> List[Dict]:
        """列出已通过的经验"""
        approved = []
        for f in self.approved_dir.glob("*.json"):
            with open(f) as fp:
                approved.append(json.load(fp))
        return sorted(approved, key=lambda x: x['quality_score'], reverse=True)
    
    def get_stats(self) -> Dict:
        """获取团队统计"""
        return {
            "team": self.team_name,
            "members": len(self._load_members()),
            "pending": len(list(self.pending_dir.glob("*.json"))),
            "approved": len(list(self.approved_dir.glob("*.json"))),
            "rejected": len(list(self.rejected_dir.glob("*.json")))
        }


class TeamSync:
    """团队经验同步（用于共享给其他成员）"""
    
    def __init__(self, team_manager: TeamManager):
        self.team = team_manager
    
    def export_approved(self, output_path: Optional[Path] = None) -> Path:
        """
        导出已审核的经验（用于共享）
        
        Returns:
            导出文件路径
        """
        if output_path is None:
            output_path = self.team.team_dir / f"{self.team.team_name}-knowledge.json"
        
        approved = self.team.list_approved()
        
        export_data = {
            "team": self.team.team_name,
            "exported_at": datetime.utcnow().isoformat(),
            "experiences": approved
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ 团队知识库已导出: {output_path}")
        print(f"   包含 {len(approved)} 条经验")
        
        return output_path
    
    def import_team_knowledge(self, import_path: Path) -> int:
        """
        导入其他团队的知识库
        
        Args:
            import_path: 导入文件路径
            
        Returns:
            导入的经验数量
        """
        with open(import_path) as f:
            data = json.load(f)
        
        imported = 0
        for exp in data.get('experiences', []):
            # 标记为导入的
            exp['imported_from'] = data.get('team', 'unknown')
            exp['imported_at'] = datetime.utcnow().isoformat()
            
            # 保存到 approved（已审核，直接可用）
            filepath = self.team.approved_dir / f"imported-{exp['id']}.json"
            with open(filepath, 'w') as f:
                json.dump(exp, f, indent=2)
            imported += 1
        
        print(f"✅ 已导入 {imported} 条经验来自 {data.get('team', 'unknown')}")
        return imported


# CLI 命令
def main():
    """Team management CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OrgClaw Team Management")
    parser.add_argument("team", help="Team name")
    parser.add_argument("--action", choices=["stats", "pending", "approved", "submit", "review"], 
                       default="stats")
    parser.add_argument("--experience", help="Experience file path (for submit)")
    parser.add_argument("--exp-id", help="Experience ID (for review)")
    parser.add_argument("--decision", choices=["approve", "reject"], help="Review decision")
    parser.add_argument("--user", default="user", help="Current user ID")
    
    args = parser.parse_args()
    
    team = TeamManager(args.team)
    
    if args.action == "stats":
        stats = team.get_stats()
        print(f"\n📊 Team: {stats['team']}")
        print(f"   Members: {stats['members']}")
        print(f"   Pending: {stats['pending']}")
        print(f"   Approved: {stats['approved']}")
        print(f"   Rejected: {stats['rejected']}")
    
    elif args.action == "pending":
        pending = team.list_pending()
        print(f"\n⏳ Pending Reviews ({len(pending)}):")
        for exp in pending:
            print(f"   • {exp['id']}: {exp['title'][:50]}...")
            print(f"     Author: {exp['author']}, Votes: {len(exp['votes'])}")
    
    elif args.action == "approved":
        approved = team.list_approved()
        print(f"\n✅ Approved Experiences ({len(approved)}):")
        for exp in approved[:10]:  # 只显示前10条
            print(f"   • {exp['title'][:50]}... (quality: {exp['quality_score']:.2f})")
    
    elif args.action == "submit" and args.experience:
        with open(args.experience) as f:
            exp = json.load(f)
        team.submit_to_team(exp, args.user)
    
    elif args.action == "review" and args.exp_id and args.decision:
        team.review(args.exp_id, args.user, args.decision)


if __name__ == "__main__":
    main()
