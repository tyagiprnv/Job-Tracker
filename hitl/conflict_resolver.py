"""Human-in-the-loop conflict resolution."""

from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel

from models.application import Application
from models.email import Email
from hitl.conflict_detector import FieldConflict
from tracking.conflict_resolutions import ConflictResolutionTracker


@dataclass
class ConflictResolution:
    """Result of conflict resolution."""

    company: str
    position: str
    user_modified: bool = False
    create_new_entry: bool = False  # If True, create separate entry instead of updating


class ConflictResolver:
    """Handles human-in-the-loop conflict resolution."""

    def __init__(self, interactive: bool = True):
        """Initialize resolver.

        Args:
            interactive: If False, always preserve spreadsheet values
        """
        self.interactive = interactive
        self.console = Console()
        self.resolution_tracker = ConflictResolutionTracker()

    def resolve_conflicts(
        self,
        application: Application,
        email: Email,
        conflicts: list[FieldConflict],
    ) -> ConflictResolution:
        """Resolve conflicts between spreadsheet and email.

        Args:
            application: Existing spreadsheet application
            email: Incoming email with potentially different values
            conflicts: List of detected conflicts

        Returns:
            ConflictResolution with final values to use
        """
        if not conflicts:
            # No conflicts - return current values
            return ConflictResolution(
                company=application.company,
                position=application.position,
                user_modified=False,
            )

        # Separate auto-upgrades from real conflicts
        auto_upgrades = [c for c in conflicts if c.is_upgrade]
        real_conflicts = [c for c in conflicts if not c.is_upgrade]

        # If non-interactive mode, only apply upgrades
        if not self.interactive:
            return self._resolve_non_interactive(
                application, email, auto_upgrades, real_conflicts
            )

        # If only upgrades (no real conflicts), apply silently
        if not real_conflicts:
            return self._apply_upgrades(application, email, auto_upgrades)

        # Real conflicts exist - prompt user
        return self._prompt_user(application, email, real_conflicts, auto_upgrades)

    def _apply_upgrades(
        self,
        application: Application,
        email: Email,
        upgrades: list[FieldConflict],
    ) -> ConflictResolution:
        """Apply auto-upgrades without prompting."""
        final_company = application.company
        final_position = application.position

        for upgrade in upgrades:
            if upgrade.field_name == "Company":
                final_company = upgrade.email_value
                self.console.print(
                    f"[dim]Auto-upgrade: Company '{upgrade.spreadsheet_value}' → '{upgrade.email_value}'[/dim]"
                )
            elif upgrade.field_name == "Position":
                final_position = upgrade.email_value
                self.console.print(
                    f"[dim]Auto-upgrade: Position '{upgrade.spreadsheet_value}' → '{upgrade.email_value}'[/dim]"
                )

        return ConflictResolution(
            company=final_company, position=final_position, user_modified=False
        )

    def _resolve_non_interactive(
        self,
        application: Application,
        email: Email,
        upgrades: list[FieldConflict],
        real_conflicts: list[FieldConflict],
    ) -> ConflictResolution:
        """Resolve in non-interactive mode (preserve spreadsheet, apply upgrades)."""
        final_company = application.company
        final_position = application.position

        # Apply upgrades
        for upgrade in upgrades:
            if upgrade.field_name == "Company":
                final_company = upgrade.email_value
            elif upgrade.field_name == "Position":
                final_position = upgrade.email_value

        # Log preserved conflicts
        if real_conflicts:
            self.console.print(
                f"[dim]Non-interactive: Preserving spreadsheet values for "
                f"{application.company} - {application.position}[/dim]"
            )

        return ConflictResolution(
            company=final_company, position=final_position, user_modified=False
        )

    def _prompt_user(
        self,
        application: Application,
        email: Email,
        conflicts: list[FieldConflict],
        upgrades: list[FieldConflict],
    ) -> ConflictResolution:
        """Show interactive prompt to resolve conflicts."""
        # Check if ALL conflicts have saved resolutions
        all_resolved = True
        resolved_values = {}

        for conflict in conflicts:
            saved = self.resolution_tracker.find_resolution(
                conflict.field_name,
                conflict.spreadsheet_value,
                conflict.email_value,
            )
            if saved:
                resolved_values[conflict.field_name] = saved["chosen_value"]
            else:
                all_resolved = False
                break

        # If all conflicts have saved resolutions, apply them
        if all_resolved:
            for conflict in conflicts:
                saved = self.resolution_tracker.find_resolution(
                    conflict.field_name,
                    conflict.spreadsheet_value,
                    conflict.email_value,
                )
                self.console.print(
                    f"[dim]Applied saved resolution: {conflict.field_name} → '{saved['chosen_value']}'[/dim]"
                )

            final_company = resolved_values.get("Company", application.company)
            final_position = resolved_values.get("Position", application.position)

            return ConflictResolution(
                company=final_company,
                position=final_position,
                user_modified=True,
            )

        # Otherwise, continue with normal prompt
        self.console.print()

        # Header panel
        title = "🔀 Conflict Detected"
        description = (
            f"A new email has different information than the spreadsheet\n"
            f"for: [cyan]{application.company}[/cyan] - [yellow]{application.position}[/yellow]"
        )
        panel = Panel(description, title=title, border_style="yellow")
        self.console.print(panel)
        self.console.print()

        # Comparison table
        table = Table(
            title="Field Comparison",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
        )
        table.add_column("Field", style="cyan", width=12)
        table.add_column("Spreadsheet (current)", style="green", width=30)
        table.add_column("Email (new)", style="yellow", width=30)

        for conflict in conflicts:
            table.add_row(
                conflict.field_name,
                conflict.spreadsheet_value,
                conflict.email_value,
            )

        self.console.print(table)
        self.console.print()

        # Email context
        self.console.print("[dim]Email Details:[/dim]")
        self.console.print(f"  • Date: {email.date.strftime('%Y-%m-%d')}")
        subject_display = (
            email.subject[:60] + "..." if len(email.subject) > 60 else email.subject
        )
        self.console.print(f"  • Subject: {subject_display}")
        self.console.print(f"  • From: {email.sender_email}")
        self.console.print()

        # Prompt options
        self.console.print("[bold]What would you like to do?[/bold]")
        self.console.print("  [1] Keep spreadsheet values", style="green")
        self.console.print("  [2] Use email values", style="yellow")
        self.console.print("  [3] Choose individually for each field", style="cyan")
        self.console.print("  [4] Create separate entry (treat as new application)", style="magenta")
        self.console.print("  [q] Skip this email (no changes)", style="dim")
        self.console.print()

        # Get user choice with error handling
        while True:
            try:
                choice = Prompt.ask(
                    "Choice", choices=["1", "2", "3", "4", "q"], default="1"
                )

                if choice == "q":
                    return ConflictResolution(
                        company=application.company,
                        position=application.position,
                        user_modified=False,
                    )
                elif choice == "1":
                    # Keep spreadsheet, but apply upgrades
                    # Save resolutions for conflicts
                    for conflict in conflicts:
                        self.resolution_tracker.save_resolution(
                            conflict.field_name,
                            conflict.spreadsheet_value,
                            conflict.email_value,
                            conflict.spreadsheet_value,  # Chosen value
                            "keep_spreadsheet",
                        )
                    return self._apply_choice_with_upgrades(
                        application.company, application.position, upgrades
                    )
                elif choice == "2":
                    # Use email values for conflicts, apply upgrades
                    return self._use_email_values(email, conflicts, upgrades)
                elif choice == "3":
                    # Individual field selection
                    return self._prompt_individual_fields(
                        application, email, conflicts, upgrades
                    )
                elif choice == "4":
                    # Create separate entry
                    return self._create_separate_entry(email)

            except KeyboardInterrupt:
                self.console.print(
                    "\n[yellow]Interrupted. Keeping spreadsheet values.[/yellow]"
                )
                return ConflictResolution(
                    company=application.company,
                    position=application.position,
                    user_modified=False,
                )
            except Exception as e:
                self.console.print(
                    f"[red]Invalid input: {e}. Please try again.[/red]"
                )
                continue

    def _use_email_values(
        self,
        email: Email,
        conflicts: list[FieldConflict],
        upgrades: list[FieldConflict],
    ) -> ConflictResolution:
        """Use email values for conflicts, apply upgrades."""
        final_company = email.company or "Unknown"
        final_position = email.position or "Unknown Position"

        # Apply upgrades if they're not already covered by conflicts
        for upgrade in upgrades:
            conflict_fields = {c.field_name for c in conflicts}
            if upgrade.field_name not in conflict_fields:
                if upgrade.field_name == "Company":
                    final_company = upgrade.email_value
                elif upgrade.field_name == "Position":
                    final_position = upgrade.email_value

        # Save resolutions for conflicts
        for conflict in conflicts:
            self.resolution_tracker.save_resolution(
                conflict.field_name,
                conflict.spreadsheet_value,
                conflict.email_value,
                conflict.email_value,  # Chosen value
                "use_email",
            )

        return ConflictResolution(
            company=final_company, position=final_position, user_modified=True
        )

    def _apply_choice_with_upgrades(
        self, company: str, position: str, upgrades: list[FieldConflict]
    ) -> ConflictResolution:
        """Keep base values but apply upgrades."""
        final_company = company
        final_position = position

        # Apply upgrades
        for upgrade in upgrades:
            if upgrade.field_name == "Company":
                final_company = upgrade.email_value
            elif upgrade.field_name == "Position":
                final_position = upgrade.email_value

        return ConflictResolution(
            company=final_company, position=final_position, user_modified=True
        )

    def _prompt_individual_fields(
        self,
        application: Application,
        email: Email,
        conflicts: list[FieldConflict],
        upgrades: list[FieldConflict],
    ) -> ConflictResolution:
        """Prompt for each conflicting field individually."""
        final_company = application.company
        final_position = application.position

        # First apply upgrades
        for upgrade in upgrades:
            if upgrade.field_name == "Company":
                final_company = upgrade.email_value
            elif upgrade.field_name == "Position":
                final_position = upgrade.email_value

        # Then prompt for each conflict
        for conflict in conflicts:
            self.console.print()
            self.console.print(f"[bold]{conflict.field_name} conflict:[/bold]")
            self.console.print(
                f"  Spreadsheet: [green]{conflict.spreadsheet_value}[/green]"
            )
            self.console.print(f"  Email: [yellow]{conflict.email_value}[/yellow]")
            self.console.print()

            choice = Prompt.ask(
                "Which value?", choices=["s", "e", "m"], default="s", show_choices=True
            )

            # Determine chosen value and resolution type
            chosen_value = None
            resolution_type = None

            if choice == "s":
                # Keep spreadsheet (already set from upgrades)
                chosen_value = conflict.spreadsheet_value
                resolution_type = "keep_spreadsheet"
            elif choice == "e":
                # Use email value
                chosen_value = conflict.email_value
                resolution_type = "use_email"
                if conflict.field_name == "Company":
                    final_company = conflict.email_value
                elif conflict.field_name == "Position":
                    final_position = conflict.email_value
            elif choice == "m":
                # Manual entry
                manual = Prompt.ask(f"Enter {conflict.field_name} manually").strip()
                if manual:
                    chosen_value = manual
                    resolution_type = "manual"
                    if conflict.field_name == "Company":
                        final_company = manual
                    elif conflict.field_name == "Position":
                        final_position = manual
                else:
                    # Empty input - keep spreadsheet
                    chosen_value = conflict.spreadsheet_value
                    resolution_type = "keep_spreadsheet"
                    self.console.print(
                        "[yellow]Empty input, keeping spreadsheet value[/yellow]"
                    )

            # Save resolution for this field
            self.resolution_tracker.save_resolution(
                conflict.field_name,
                conflict.spreadsheet_value,
                conflict.email_value,
                chosen_value,
                resolution_type,
            )

        return ConflictResolution(
            company=final_company, position=final_position, user_modified=True
        )

    def _create_separate_entry(self, email: Email) -> ConflictResolution:
        """Signal to create a separate entry instead of updating existing one.

        Args:
            email: Email with values for the new entry

        Returns:
            ConflictResolution with create_new_entry=True
        """
        self.console.print(
            f"\n[magenta]Creating separate entry for: {email.company} - {email.position}[/magenta]"
        )
        return ConflictResolution(
            company=email.company or "Unknown",
            position=email.position or "Unknown Position",
            user_modified=True,
            create_new_entry=True,
        )
