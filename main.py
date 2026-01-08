"""Job Application Tracker - Main entry point."""

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import SPREADSHEET_ID, GMAIL_SEARCH_DAYS
from gmail.fetcher import EmailFetcher
from gmail.parser import EmailParser
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
def main(days: int, dry_run: bool):
    """Job Application Tracker - Automatically track job applications from Gmail."""
    console.print("\n[bold blue]Job Application Tracker[/bold blue]", justify="center")
    console.print("[dim]Scanning Gmail for job-related emails...[/dim]\n")

    if dry_run:
        console.print("[yellow]Running in DRY RUN mode - no changes will be made[/yellow]\n")

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

            # Step 3: Detect job-related emails
            progress.update(task, description="Detecting job-related emails...")
            detector = JobEmailDetector()
            job_emails = detector.detect_batch(emails)

            if not job_emails:
                console.print(
                    "[yellow]No job-related emails found in the specified time period.[/yellow]"
                )
                return

            console.print(f"[green]Found {len(job_emails)} job-related emails[/green]\n")

            # Step 4: Extract information
            progress.update(task, description="Extracting company and position info...")
            extractor = InfoExtractor()
            classifier = EmailClassifier()

            for email in job_emails:
                email.company, email.position = extractor.extract_all(email)
                email.email_type, email.status = classifier.classify(email)

            # Step 5: Load existing applications
            progress.update(task, description="Loading existing applications...")
            if not dry_run:
                manager = ApplicationManager()
                existing_apps = manager.get_all_applications()
            else:
                existing_apps = []

            # Step 6: Match and update
            progress.update(task, description="Matching emails to applications...")
            matcher = ApplicationMatcher()

            new_applications = 0
            updated_applications = 0
            skipped_emails = 0

            for email in job_emails:
                # Find match
                match, confidence = matcher.find_match(email, existing_apps)

                if match:
                    # Update existing application
                    if not dry_run:
                        manager.update_application(match, email)
                        # Update thread_id if not set
                        if not match.thread_id:
                            match.thread_id = email.thread_id
                    updated_applications += 1
                else:
                    # Create new application
                    if not dry_run:
                        new_app = manager.create_application(email)
                        existing_apps.append(new_app)
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
