#!/usr/bin/env python3
"""OrgClaw CLI."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

# Add parent to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orgclaw import ExperienceExtractor, ExperienceScorer, KnowledgeStore, PatternsClient


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """OrgClaw - Organization knowledge federation for OpenClaw."""
    pass


@cli.command()
@click.argument("task_id")
@click.option("--description", "-d", required=True, help="Task description")
@click.option("--commit", "-c", help="Git commit hash")
@click.option("--repo", "-r", default=".", help="Repository path")
def extract(task_id: str, description: str, commit: str, repo: str):
    """Extract experience from a completed task."""
    console.print(Panel(f"Extracting experience for task: {task_id}", style="blue"))
    
    extractor = ExperienceExtractor(repo_path=repo)
    scorer = ExperienceScorer()
    
    experience = extractor.extract_from_task(
        task_id=task_id,
        task_description=description,
        commit_hash=commit,
    )
    
    if not experience:
        console.print("[red]Failed to extract experience[/red]")
        sys.exit(1)
    
    # Score
    score = scorer.score(experience)
    experience.quality_score = score.overall
    
    # Display
    console.print(f"\n[bold]Title:[/bold] {experience.title}")
    console.print(f"[bold]Category:[/bold] {experience.category}")
    console.print(f"[bold]Quality Score:[/bold] {score.overall:.2f}")
    
    console.print("\n[bold]Score Breakdown:[/bold]")
    console.print(f"  Completeness: {score.completeness:.2f}")
    console.print(f"  Specificity: {score.specificity:.2f}")
    console.print(f"  Actionability: {score.actionability:.2f}")
    console.print(f"  Reusability: {score.reusability:.2f}")
    
    if experience.solution_steps:
        console.print("\n[bold]Solution Steps:[/bold]")
        for i, step in enumerate(experience.solution_steps, 1):
            console.print(f"  {i}. {step}")
    
    # Save to file for inspection
    output_file = Path(f"experience-{task_id}.json")
    import dataclasses
    with open(output_file, "w") as f:
        json.dump(dataclasses.asdict(experience), f, indent=2, default=str)
    console.print(f"\n[green]Saved to {output_file}[/green]")


@cli.command()
@click.argument("query")
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-n", default=5, help="Number of results")
def search(query: str, category: str, limit: int):
    """Search the knowledge base."""
    console.print(Panel(f"Searching: {query}", style="blue"))
    
    store = KnowledgeStore()
    results = store.query(
        query_text=query,
        n_results=limit,
        category=category,
    )
    
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    table = Table(title=f"Found {len(results)} experiences")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Category", style="green")
    table.add_column("Quality", justify="right")
    
    for exp in results:
        table.add_row(
            exp.id[:20],
            exp.title[:50],
            exp.category,
            f"{exp.quality_score:.2f}",
        )
    
    console.print(table)


@cli.command()
@click.argument("query")
@click.option("--category", "-c", help="Filter by category")
@click.option("--tag", "-t", help="Filter by tag")
def patterns(query: str, category: str, tag: str):
    """Search conpera-patterns."""
    console.print(Panel(f"Searching patterns: {query}", style="blue"))
    
    client = PatternsClient()
    
    if category:
        results = client.search_by_category(category)
    elif tag:
        results = client.search_by_tag(tag)
    else:
        # Try as tag
        results = client.search_by_tag(query)
    
    if not results:
        console.print("[yellow]No patterns found[/yellow]")
        return
    
    table = Table(title=f"Found {len(results)} patterns")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Category", style="green")
    table.add_column("Status", style="yellow")
    
    for pattern in results:
        table.add_row(
            pattern.id[:30],
            pattern.title[:40],
            pattern.category,
            pattern.status,
        )
    
    console.print(table)


@cli.command()
def stats():
    """Show knowledge base statistics."""
    store = KnowledgeStore()
    
    all_exp = store.list_all()
    
    if not all_exp:
        console.print("[yellow]Knowledge base is empty[/yellow]")
        return
    
    # Calculate stats
    categories = {}
    for exp in all_exp:
        categories[exp.category] = categories.get(exp.category, 0) + 1
    
    avg_quality = sum(e.quality_score for e in all_exp) / len(all_exp)
    
    # Display
    console.print(Panel("Knowledge Base Statistics", style="blue"))
    console.print(f"Total Experiences: {len(all_exp)}")
    console.print(f"Average Quality: {avg_quality:.2f}")
    
    console.print("\n[bold]By Category:[/bold]")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        console.print(f"  {cat}: {count}")


@cli.command()
@click.argument("json_file")
def add(json_file: str):
    """Add an experience from JSON file to knowledge base."""
    import dataclasses
    import json
    
    path = Path(json_file)
    if not path.exists():
        console.print(f"[red]File not found: {json_file}[/red]")
        sys.exit(1)
    
    with open(path) as f:
        data = json.load(f)
    
    # Reconstruct Experience
    from orgclaw.analyzer.extractor import Experience, CodeChange
    
    code_changes = [CodeChange(**cc) for cc in data.get("code_changes", [])]
    
    experience = Experience(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        category=data["category"],
        context=data.get("context", {}),
        code_changes=code_changes,
        solution_steps=data.get("solution_steps", []),
        lessons_learned=data.get("lessons_learned", []),
        applicable_scenarios=data.get("applicable_scenarios", []),
        quality_score=data.get("quality_score", 0.0),
        source_task_id=data.get("source_task_id"),
        created_at=data.get("created_at"),
    )
    
    store = KnowledgeStore()
    doc_id = store.add_experience(experience)
    
    console.print(f"[green]Added experience with ID: {doc_id}[/green]")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
