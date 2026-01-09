"""Job Application Tracker - Main entry point."""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import SPREADSHEET_ID, GMAIL_SEARCH_DAYS
from gmail.fetcher import EmailFetcher
from gmail.parser import EmailParser
from llm.email_analyzer import LLMEmailAnalyzer
from detection.detector import JobEmailDetector
from detection.extractor import InfoExtractor
from detection.classifier import EmailClassifier
from sheets.manager import ApplicationManager
from matching.matcher import ApplicationMatcher

console = Console()


@click.command()
@click.option(
    "--days",
    default=GMAIL_SEARCH_DAYS,
    help="Number of days to search back for emails",
    type=int,
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run without updating the spreadsheet (preview mode)",
)
@click.option(
    "--mode",
    default="llm",
    type=click.Choice(["llm", "rules"], case_sensitive=False),
    help="Analysis mode: 'llm' for AI-powered analysis (default), 'rules' for traditional rule-based",
)
@click.option(
    "--reset-tracking",
    is_flag=True,
    help="Delete tracking files (processed_emails.json, false_positives.json) and exit. Use when switching spreadsheets.",
)
def main(days: int, dry_run: bool, mode: str, reset_tracking: bool):
    """Job Application Tracker - Automatically track job applications from Gmail."""

    # Handle reset tracking flag first (early exit)
    if reset_tracking:
        from config.settings import PROCESSED_EMAILS_FILE, FALSE_POSITIVES_FILE

        console.print("\n[bold yellow]Resetting tracking files...[/bold yellow]\n")

        files_deleted = []
        files_not_found = []

        # Delete processed_emails.json
        if PROCESSED_EMAILS_FILE.exists():
            PROCESSED_EMAILS_FILE.unlink()
            files_deleted.append("processed_emails.json")
        else:
            files_not_found.append("processed_emails.json")

        # Delete false_positives.json
        if FALSE_POSITIVES_FILE.exists():
            FALSE_POSITIVES_FILE.unlink()
            files_deleted.append("false_positives.json")
        else:
            files_not_found.append("false_positives.json")

        # Display results
        if files_deleted:
            console.print("[green]✓ Deleted:[/green]")
            for file in files_deleted:
                console.print(f"  - {file}")

        if files_not_found:
            console.print("\n[dim]Not found (already clean):[/dim]")
            for file in files_not_found:
                console.print(f"  - {file}")

        console.print("\n[green]✓ Tracking reset complete![/green]")
        console.print("[dim]Note: llm_cache.json was preserved (contains cached analysis results)[/dim]\n")

        return  # Exit without processing emails

    console.print("\n[bold blue]Job Application Tracker[/bold blue]", justify="center")
    console.print("[dim]Scanning Gmail for job-related emails...[/dim]\n")

    if dry_run:
        console.print("[yellow]Running in DRY RUN mode - no changes will be made[/yellow]\n")

    mode_display = "LLM (AI-powered)" if mode == "llm" else "Rules-based"
    console.print(f"[cyan]Analysis mode: {mode_display}[/cyan]\n")

    try:
        # Initialize components
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Authenticate and fetch emails
            task = progress.add_task("Authenticating with Gmail...", total=None)
            fetcher = EmailFetcher()
            progress.update(task, description="Fetching recent emails...")

            message_metadata = fetcher.fetch_recent_emails(days_back=days)

            if not message_metadata:
                console.print("[yellow]No emails found in the specified time period.[/yellow]")
                return

            progress.update(
                task, description=f"Fetching details for {len(message_metadata)} emails..."
            )
            messages = fetcher.fetch_messages_batch(
                [msg["id"] for msg in message_metadata]
            )

            # Step 2: Parse emails
            progress.update(task, description="Parsing emails...")
            parser = EmailParser()
            emails = parser.parse_messages(messages)

            # Sort emails by date (oldest first) to ensure natural status progression
            emails.sort(key=lambda e: e.date)

            # Step 3: Analyze emails (LLM or rules-based)
            if mode == "llm":
                progress.update(task, description="Analyzing emails with LLM...")
                analyzer = LLMEmailAnalyzer()
                job_emails = analyzer.analyze_batch(emails)
            else:
                # Rules-based approach
                progress.update(task, description="Detecting job-related emails...")
                detector = JobEmailDetector()
                job_emails = detector.detect_batch(emails)

                if job_emails:
                    progress.update(task, description="Extracting company and position info...")
                    extractor = InfoExtractor()
                    classifier = EmailClassifier()

                    for email in job_emails:
                        email.company, email.position = extractor.extract_all(email)
                        email.email_type, email.status = classifier.classify(email)

            if not job_emails:
                console.print(
                    "[yellow]No job-related emails found in the specified time period.[/yellow]"
                )
                return

            console.print(f"[green]Found {len(job_emails)} job-related emails[/green]\n")

            # Step 4: Load existing applications
            progress.update(task, description="Loading existing applications...")
            if not dry_run:
                manager = ApplicationManager()
                existing_apps = manager.get_all_applications()
            else:
                existing_apps = []

            # Step 5: Match and update
            progress.update(task, description="Matching emails to applications...")
            matcher = ApplicationMatcher()

            new_applications = 0
            updated_applications = 0
            skipped_false_positives = 0

            for email in job_emails:
                # Find match
                match, confidence = matcher.find_match(email, existing_apps)

                if match:
                    # Update existing application
                    if not dry_run:
                        updated = manager.update_application(match, email)
                        if updated:
                            # Update thread_id if not set
                            if not match.thread_id:
                                match.thread_id = email.thread_id
                            updated_applications += 1
                    else:
                        updated_applications += 1
                else:
                    # Create new application
                    if not dry_run:
                        new_app = manager.create_application(email)
                        if new_app:
                            existing_apps.append(new_app)
                            new_applications += 1
                        else:
                            # False positive detected
                            skipped_false_positives += 1
                    else:
                        new_applications += 1

        # Display summary
        console.print("\n[bold green]Summary:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="green")

        table.add_row("Total emails scanned", str(len(emails)))
        table.add_row("Job-related emails found", str(len(job_emails)))
        table.add_row("New applications created", str(new_applications))
        table.add_row("Applications updated", str(updated_applications))
        if skipped_false_positives > 0:
            table.add_row("Skipped (false positives)", str(skipped_false_positives))

        console.print(table)

        if dry_run:
            console.print("\n[yellow]DRY RUN: No changes were made to the spreadsheet[/yellow]")
        else:
            console.print(
                f"\n[green]✓ Successfully updated spreadsheet:[/green] {SPREADSHEET_ID}"
            )

        # Show sample of detected applications
        if job_emails:
            console.print("\n[bold]Sample of detected job emails:[/bold]")
            sample_table = Table(show_header=True, header_style="bold blue")
            sample_table.add_column("Company", style="cyan")
            sample_table.add_column("Position", style="yellow")
            sample_table.add_column("Status", style="green")
            sample_table.add_column("Date", style="dim")

            for email in job_emails[:5]:  # Show first 5
                sample_table.add_row(
                    email.company or "Unknown",
                    email.position or "Unknown",
                    email.status or "Applied",
                    email.date.strftime("%Y-%m-%d"),
                )

            console.print(sample_table)

    except FileNotFoundError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\n[yellow]Setup Instructions:[/yellow]")
        console.print("1. Download credentials.json from Google Cloud Console")
        console.print("2. Place it in the project root directory")
        console.print("3. Set SPREADSHEET_ID in .env file")
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")


if __name__ == "__main__":
    main()
