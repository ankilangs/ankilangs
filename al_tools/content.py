"""Content generation for AnkiLangs decks.

Handles parsing of changelog files and generation of website pages and AnkiWeb descriptions.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from al_tools.registry import Deck, DeckRegistry
from al_tools.i18n import (
    get_ui_string,
    get_apkg_filename,
    get_language_name,
)


@dataclass
class ChangelogEntry:
    """Represents a single changelog entry."""

    version: str
    date: Optional[datetime]
    changes: List[str]
    raw_text: str

    def __repr__(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d") if self.date else "no date"
        return f"ChangelogEntry({self.version!r}, date={date_str}, changes={len(self.changes)})"


class ChangelogParser:
    """Parses markdown changelog files."""

    # Pattern: ## X.Y.Z - YYYY-MM-DD or ## X.Y.Z
    VERSION_HEADER_PATTERN = re.compile(
        r"^##\s+(\d+\.\d+\.\d+)(?:\s+-\s+(\d{4}-\d{2}-\d{2}))?$"
    )

    @classmethod
    def parse(cls, changelog_path: Path) -> List[ChangelogEntry]:
        """Parse a changelog file and extract all version entries.

        Returns entries in order of appearance (newest first, typically).
        """
        if not changelog_path.exists():
            raise FileNotFoundError(f"Changelog not found: {changelog_path}")

        with open(changelog_path, "r") as f:
            content = f.read()

        entries = []
        lines = content.split("\n")
        current_entry = None
        current_changes = []
        current_raw_lines = []

        for line in lines:
            match = cls.VERSION_HEADER_PATTERN.match(line)

            if match:
                # Save previous entry if it exists
                if current_entry:
                    current_entry.changes = current_changes
                    current_entry.raw_text = "\n".join(current_raw_lines).strip()
                    entries.append(current_entry)

                # Start new entry
                version = match.group(1)
                date_str = match.group(2)
                date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None

                current_entry = ChangelogEntry(
                    version=version, date=date, changes=[], raw_text=""
                )
                current_changes = []
                current_raw_lines = []
            elif current_entry:
                # Collect changes (bullet points)
                stripped = line.strip()
                if stripped.startswith("-") or stripped.startswith("*"):
                    current_changes.append(stripped[1:].strip())

                # Collect raw text (everything except the header)
                if line.strip():
                    current_raw_lines.append(line)

        # Save last entry
        if current_entry:
            current_entry.changes = current_changes
            current_entry.raw_text = "\n".join(current_raw_lines).strip()
            entries.append(current_entry)

        return entries

    @classmethod
    def get_version_entry(
        cls, changelog_path: Path, version: str
    ) -> Optional[ChangelogEntry]:
        """Get a specific version entry from the changelog."""
        entries = cls.parse(changelog_path)
        for entry in entries:
            if entry.version == version:
                return entry
        return None

    @classmethod
    def get_latest_entry(cls, changelog_path: Path) -> Optional[ChangelogEntry]:
        """Get the most recent changelog entry."""
        entries = cls.parse(changelog_path)
        return entries[0] if entries else None


def generate_deck_overview_page(registry: DeckRegistry) -> str:
    """Generate the main deck overview page that lists all decks grouped by source language.

    Args:
        registry: Deck registry containing all decks

    Returns:
        Markdown content for the overview page
    """
    # Group decks by source language
    decks_by_source: Dict[str, List[Deck]] = defaultdict(list)
    for deck in registry.all():
        # Only include 625-word decks in the overview (not minimal pairs)
        if deck.deck_type == "625":
            decks_by_source[deck.source_locale].append(deck)

    # Build frontmatter and introductory content
    frontmatter = [
        "---",
        'title: "Decks"',
        "weight: 5",
        "bookCollapseSection: true",
        "---",
        "",
        "# Decks",
        "",
        "> [!NOTE]",
        "> **Note:** All decks are currently in development and may not yet contain all 625 words.",
        "> See individual deck pages for current status.",
        "",
    ]

    sections = []

    # Sort source languages alphabetically (using English names for consistency)
    sorted_source_locales = sorted(
        decks_by_source.keys(), key=lambda loc: get_language_name("en_us", loc)
    )

    for source_locale in sorted_source_locales:
        decks = decks_by_source[source_locale]

        # Get section header in source language
        section_header = get_ui_string(source_locale, "source_language_decks_header")
        sections.append(f"## {section_header}")
        sections.append("")

        # Get intro text in source language
        intro_text = get_ui_string(source_locale, "learn_other_languages_intro")
        sections.append(intro_text + ".")
        sections.append("")

        # Sort decks by target language name (in the source language)
        sorted_decks = sorted(
            decks, key=lambda d: get_language_name(source_locale, d.target_locale)
        )

        # Generate list items for each deck
        for deck in sorted_decks:
            # Extract full deck name (remove " | AnkiLangs.org" suffix)
            deck_display_name = deck.name.replace(" | AnkiLangs.org", "")

            # Get latest release version and date
            latest_version = registry.get_latest_release_version(deck.deck_id)

            if latest_version:
                # Try to get the date from the changelog
                changelog_path = Path(deck.content_dir) / "changelog.md"
                try:
                    entry = ChangelogParser.get_version_entry(
                        changelog_path, latest_version
                    )
                    if entry and entry.date:
                        date_str = entry.date.strftime("%Y-%m-%d")
                        version_info = f"{latest_version} - {date_str}"
                    else:
                        version_info = latest_version
                except (FileNotFoundError, Exception):
                    version_info = latest_version
            else:
                version_info = "unreleased"

            # Create link to deck page (relative path)
            deck_link = deck.website_slug
            sections.append(f"- [{deck_display_name}]({deck_link}) ({version_info})")

        sections.append("")

    return "\n".join(frontmatter + sections)


class ContentGenerator:
    """Generates website pages and AnkiWeb descriptions from source content."""

    def __init__(self, deck: Deck, github_repo: str = "ankilangs/ankilangs"):
        """Initialize content generator for a deck.

        Args:
            deck: Deck to generate content for
            github_repo: GitHub org/repo for raw URLs (e.g., "ankilangs/ankilangs")
        """
        self.deck = deck
        self.github_repo = github_repo
        self.content_dir = Path(deck.content_dir)

    def generate_website_page(self) -> str:
        """Generate complete website page markdown from source content.

        Returns the full markdown content for the deck page.
        """
        # Read source content
        description = self._read_description()
        changelog = self._read_changelog_markdown()
        notes = self._read_notes()

        # Get localized UI strings
        locale = self.deck.source_locale
        download_text = get_ui_string(locale, "download_deck")
        installation_text = get_ui_string(locale, "installation_instructions")
        learning_tips_text = get_ui_string(locale, "learning_tips")
        screenshots_text = get_ui_string(locale, "screenshots")
        changelog_text = get_ui_string(locale, "changelog")
        notes_text = get_ui_string(locale, "notes")
        see_text = get_ui_string(
            locale,
            "see_x_and_y",
            f'[{installation_text}]({{{{< ref "/installation" >}}}})',
            f'[{learning_tips_text}]({{{{< ref "/learning-tips" >}}}})',
        )

        # Build frontmatter
        frontmatter = self._generate_frontmatter()

        # Build page sections
        # Extract title without the AnkiLangs.org suffix
        title = self.deck.name.replace(" | AnkiLangs.org", "")

        sections = [
            frontmatter,
            "",  # Empty line after frontmatter
            f"# {title}",
            "",
        ]

        # Check if deck has been released and add release info banner
        from al_tools.registry import DeckRegistry

        registry = DeckRegistry()
        latest_version = registry.get_latest_release_version(self.deck.deck_id)

        if latest_version:
            # Try to get the date from the changelog
            changelog_path = self.content_dir / "changelog.md"
            try:
                entry = ChangelogParser.get_version_entry(
                    changelog_path, latest_version
                )
                if entry and entry.date:
                    date_str = entry.date.strftime("%Y-%m-%d")
                    release_info = f"**Latest release:** {latest_version} ({date_str})"
                else:
                    release_info = f"**Latest release:** {latest_version}"
            except (FileNotFoundError, Exception):
                release_info = f"**Latest release:** {latest_version}"
        else:
            release_info = "**Status:** Unreleased"

        sections.extend([release_info, ""])

        # Add description
        sections.extend([description, ""])

        if latest_version:
            # Deck has releases - show download link
            sections.extend(
                [
                    f"[{download_text}]({{{{< param download_url >}}}})",
                    "",
                ]
            )

            # Add AnkiWeb link with rating encouragement if available
            if self.deck.ankiweb_id:
                ankiweb_text = get_ui_string(
                    locale,
                    "ankiweb_also_available",
                    "{{< param ankiweb_url >}}",
                )
                sections.extend([ankiweb_text, ""])

            sections.append(see_text)
        else:
            # Deck is unreleased - show note
            unreleased_note = get_ui_string(locale, "unreleased_note")
            sections.extend(
                [
                    f"**{unreleased_note}**",
                    "",
                ]
            )

        # Add screenshots section
        if self._has_screenshots():
            sections.extend(["", f"## {screenshots_text}", ""])
            sections.extend(self._generate_screenshot_markdown())

        # Add notes section if exists
        if notes:
            sections.extend(["", f"## {notes_text}", "", notes])

        # Add changelog section
        if changelog:
            sections.extend(["", f"## {changelog_text}", "", changelog])

        return "\n".join(sections) + "\n"

    def generate_description_file_content(self, version: str) -> str:
        """Generate full HTML content for the description file shown inside Anki.

        Args:
            version: Version string to display (e.g., "1.0.0" or "1.0.1-dev")

        Returns:
            Complete HTML content for the description file.
        """
        description = self._read_description()
        locale = self.deck.source_locale
        version_label = get_ui_string(locale, "version")

        # Build deck page URL
        deck_url = f"https://ankilangs.org/decks/{self.deck.website_slug}/"

        check_deck_page = get_ui_string(locale, "check_deck_page_html", deck_url)
        check_more_decks = get_ui_string(locale, "check_more_decks_html")

        lines = [
            description,
            check_deck_page,
            check_more_decks,
            f"<b>{version_label}: </b>{version}",
            "",  # trailing newline
        ]

        return "\n".join(lines)

    def generate_ankiweb_description(self) -> str:
        """Generate AnkiWeb description from source content.

        Returns formatted HTML/markdown suitable for AnkiWeb.
        """
        description = self._read_description()
        latest_changelog = self._get_latest_changelog_entry()
        locale = self.deck.source_locale

        # Get localized strings
        version_text = get_ui_string(locale, "version")
        changelog_text = get_ui_string(locale, "changelog")
        whats_new_text = get_ui_string(
            locale, "whats_new_in", latest_changelog.version if latest_changelog else ""
        )
        screenshots_text = get_ui_string(locale, "screenshots")

        ankiweb_rate_text = get_ui_string(locale, "ankiweb_rate_review")

        sections = [
            description,
            "",
            ankiweb_rate_text,
            "",
            f"See [ankilangs.org/decks/{self.deck.website_slug}](https://ankilangs.org/decks/{self.deck.website_slug}/) for full documentation, learning tips, and to report issues.",
            "",
            "Check [AnkiLangs.org](https://ankilangs.org/) for more decks and to help improve this deck.",
        ]

        # Add screenshots with HTML
        if self._has_screenshots():
            sections.extend(["", "<div>"])
            # Show first 4 screenshots (pronunciation Q&A and listening Q&A)
            screenshot_types = [
                ("pronunciation", "Pronunciation"),
                ("listening", "Listening"),
            ]
            for card_type, label in screenshot_types:
                q_url = self._get_screenshot_url(f"{card_type}_q.png")
                a_url = self._get_screenshot_url(f"{card_type}_a.png")
                sections.append(
                    f'  <img src="{q_url}" width="400" alt="{label} card - Question">'
                )
                sections.append(
                    f'  <img src="{a_url}" width="400" alt="{label} card - Answer">'
                )
            sections.extend(
                [
                    "</div>",
                    "",
                    f"[View all {screenshots_text.lower()}](https://ankilangs.org/decks/{self.deck.website_slug}/#screenshots)",
                ]
            )

        # Add version and latest changes
        if latest_changelog:
            # Format version with date if available
            if latest_changelog.date:
                date_str = latest_changelog.date.strftime("%Y-%m-%d")
                version_display = f"{latest_changelog.version} ({date_str})"
            else:
                version_display = latest_changelog.version

            sections.extend(
                [
                    "",
                    f"**{version_text}: {version_display}** ([{changelog_text.lower()}](https://ankilangs.org/decks/{self.deck.website_slug}/#changelog))",
                    "",
                    f"### {whats_new_text}",
                    "",
                ]
            )
            for change in latest_changelog.changes:
                sections.append(f"- {change}")

        return "\n".join(sections) + "\n"

    def generate_github_release_notes(self, version: str) -> str:
        """Generate GitHub release notes for a specific version.

        Args:
            version: Version to generate notes for (e.g., "0.3.0")

        Returns formatted markdown for GitHub release.
        """
        changelog_path = self.content_dir / "changelog.md"
        entry = ChangelogParser.get_version_entry(changelog_path, version)

        if not entry:
            raise ValueError(f"No changelog entry found for version {version}")

        sections = [
            "## What's Changed",
            "",
        ]

        for change in entry.changes:
            sections.append(f"- {change}")

        sections.extend(
            [
                "",
                "## Installation",
                "",
                "Download the `.apkg` file below and import into Anki (File → Import).",
            ]
        )

        if self.deck.ankiweb_id:
            ankiweb_url = f"https://ankiweb.net/shared/info/{self.deck.ankiweb_id}"
            sections.extend(
                [
                    "",
                    f"Also available on [AnkiWeb]({ankiweb_url}). If you like this deck, please rate and review it there!",
                ]
            )

        sections.extend(
            [
                "",
                f"**Full changelog & documentation:** https://ankilangs.org/decks/{self.deck.website_slug}/",
            ]
        )

        return "\n".join(sections)

    def _read_description(self) -> str:
        """Read deck description from source file."""
        desc_path = self.content_dir / "description.md"
        if not desc_path.exists():
            raise FileNotFoundError(f"Description file not found: {desc_path}")

        with open(desc_path, "r") as f:
            return f.read().strip()

    def _read_changelog_markdown(self) -> str:
        """Read and return formatted changelog markdown."""
        changelog_path = self.content_dir / "changelog.md"
        if not changelog_path.exists():
            return ""

        entries = ChangelogParser.parse(changelog_path)
        if not entries:
            return ""

        # Format entries with ### headers
        sections = []
        for entry in entries:
            if entry.date:
                date_str = entry.date.strftime("%Y-%m-%d")
                sections.append(f"### {entry.version} - {date_str}")
            else:
                sections.append(f"### {entry.version}")

            sections.append("")

            for change in entry.changes:
                sections.append(f"- {change}")

            sections.append("")

        return "\n".join(sections).strip()

    def _read_notes(self) -> str:
        """Read deck notes from source file if it exists."""
        notes_path = self.content_dir / "notes.md"
        if not notes_path.exists():
            return ""

        with open(notes_path, "r") as f:
            return f.read().strip()

    def _get_latest_changelog_entry(self) -> Optional[ChangelogEntry]:
        """Get the latest changelog entry."""
        changelog_path = self.content_dir / "changelog.md"
        if not changelog_path.exists():
            return None

        return ChangelogParser.get_latest_entry(changelog_path)

    def _has_screenshots(self) -> bool:
        """Check if screenshots directory exists and has files."""
        screenshot_dir = self.content_dir / "screenshots"
        if not screenshot_dir.exists():
            return False

        # Check for at least one screenshot
        return any(screenshot_dir.glob("*.png"))

    def _generate_screenshot_markdown(self) -> List[str]:
        """Generate markdown for screenshot section."""
        card_types = [
            ("pronunciation", "Pronunciation"),
            ("listening", "Listening"),
            ("reading", "Reading"),
            ("spelling", "Spelling"),
        ]

        lines = []
        for card_type, label in card_types:
            q_file = f"{card_type}_q.png"
            a_file = f"{card_type}_a.png"

            q_path = self.content_dir / "screenshots" / q_file
            a_path = self.content_dir / "screenshots" / a_file

            if q_path.exists():
                lines.append(f"![{label} - Question](screenshots/{q_file})")
            if a_path.exists():
                lines.append(f"![{label} - Answer](screenshots/{a_file})")

        return lines

    def _get_screenshot_url(self, filename: str) -> str:
        """Get raw GitHub URL for a screenshot."""
        return f"https://raw.githubusercontent.com/{self.github_repo}/main/{self.deck.content_dir}/screenshots/{filename}"

    def _generate_frontmatter(self) -> str:
        """Generate Hugo frontmatter for deck page."""
        # Determine download URL based on whether this is a dev version
        if self.deck.is_dev_version:
            # For dev versions, use latest release version
            from al_tools.registry import DeckRegistry

            registry = DeckRegistry()
            latest_version = registry.get_latest_release_version(self.deck.deck_id)
            if latest_version:
                version_for_url = latest_version
            else:
                # No release yet, use placeholder
                version_for_url = "0.1.0"
        else:
            version_for_url = self.deck.version

        # Generate proper .apkg filename
        filename = get_apkg_filename(
            self.deck.source_locale,
            self.deck.target_locale,
            self.deck.deck_type,
            version_for_url,
        )

        # Build download URL
        encoded_tag = f"{self.deck.tag_name}%2F{version_for_url}"
        download_url = f"https://github.com/{self.github_repo}/releases/download/{encoded_tag}/{filename}"

        # Build AnkiWeb URL if ID exists
        ankiweb_url = ""
        if self.deck.ankiweb_id:
            ankiweb_url = f"https://ankiweb.net/shared/info/{self.deck.ankiweb_id}"

        # Extract title from name (remove " | AnkiLangs.org" suffix if present)
        title = self.deck.name.replace(" | AnkiLangs.org", "")

        # Determine weight based on source language
        source_locale_weights = {
            "en_us": 10,
            "de_de": 20,
            "es_es": 30,
        }
        weight = source_locale_weights.get(self.deck.source_locale, 99)

        frontmatter_lines = [
            "---",
            f'title: "{title}"',
            "aliases:",
            f"  - /docs/decks/{self.deck.website_slug}/",
            f"deck_id: {self.deck.deck_id}",
            f'version: "{version_for_url}"',
            f'download_url: "{download_url}"',
            f'ankiweb_url: "{ankiweb_url}"',
            f"weight: {weight}",
            "---",
        ]

        return "\n".join(frontmatter_lines)
