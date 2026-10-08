import sys
import typer
from typing import Optional, List
from app.db.database import init_db
from app.domain.capture import capture_engine
from app.domain.enrichment import enrichment_engine
from app.domain.retrieval import retrieval_engine
from app.domain.obsidian_sync import obsidian_sync_engine
from app.domain.output_builder import output_builder_engine

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = typer.Typer(help="Domain Content Manager CLI — Voice-First Knowledge System")

@app.callback()
def callback():
    init_db()

@app.command("capture")
def capture_cmd(
    text: str = typer.Argument(..., help="Text note or source URL to capture"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Title override"),
    domain: str = typer.Option("general", "--domain", "-d", help="Primary domain: health, hair, diet, garden, foraging, culinary"),
    source_url: Optional[str] = typer.Option(None, "--url", "-u", help="Source URL")
):
    """
    Captures text, link, or note into the inbox.
    """
    rec = capture_engine.capture_text_or_url(
        title=title,
        content_text=text,
        source_url=source_url,
        primary_domain=domain
    )
    obsidian_sync_engine.export_record_to_markdown(rec)
    typer.echo(f"Captured Record [{rec.id[:8]}]: {rec.title} (Domain: {rec.primary_domain})")
    typer.echo("Exported to Obsidian Vault: vault/00 Inbox/")

@app.command("capture-voice")
def capture_voice_cmd(
    transcript: str = typer.Argument(..., help="Voice transcription text")
):
    """
    Simulates voice capture input with STT transcription.
    """
    rec = capture_engine.capture_voice(voice_text=transcript)
    obsidian_sync_engine.export_record_to_markdown(rec)
    typer.echo(f"Captured Voice Note [{rec.id[:8]}]: {rec.title} (Domain: {rec.primary_domain})")
    typer.echo("Voice Feedback: Record captured and tagged successfully.")

@app.command("search")
def search_cmd(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
    risk: Optional[str] = typer.Option(None, "--risk", "-r", help="Filter by risk level")
):
    """
    Searches records by metadata, keywords, or domain.
    """
    results = retrieval_engine.search(query=query, domain=domain, risk_level=risk)
    typer.echo(f"\nFound {len(results)} records:")
    for r in results:
        typer.echo(f" - [{r.id[:8]}] [{r.primary_domain.upper()}] {r.title} (Status: {r.status}, Risk: {r.risk_level})")
    
    voice_res = retrieval_engine.speak_results_summary(results)
    typer.echo(f"\nVoice Readout: {voice_res['voice_script']}")

@app.command("sync")
def sync_cmd():
    """
    Syncs all database records to Obsidian Vault Markdown files.
    """
    count = obsidian_sync_engine.sync_all()
    typer.echo(f"Synced {count} records to Obsidian Vault.")

@app.command("build-output")
def build_output_cmd(
    record_ids: List[str] = typer.Argument(..., help="List of ContentRecord IDs to combine"),
    output_type: str = typer.Option("post", "--type", "-t", help="Output type: post, guide, protocol, lecture"),
    title: str = typer.Option("תוצר חדש", "--title", "-n", help="Output title")
):
    """
    Assembles selected records into a new structured post/guide/protocol output.
    """
    res = output_builder_engine.assemble_output(record_ids=record_ids, output_type=output_type, target_title=title)
    typer.echo(f"Created Output: {res['title']} ({res['sources_count']} sources)")
    typer.echo(f"Output file saved to: {res['output_path']}")
    typer.echo(f"Voice Readout: {res['voice_script']}")

if __name__ == "__main__":
    app()
