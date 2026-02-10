"""Release automation for AnkiLangs decks.

Handles version validation, pre-release checks, and version bumping.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from al_tools.content import ChangelogParser
from al_tools.registry import Deck


@dataclass
class Version:
    """Represents a semantic version."""

    major: int
    minor: int
    patch: int
    is_dev: bool

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse a version string like '1.2.3' or '1.2.3-dev'."""
        # Remove -dev suffix if present
        is_dev = version_str.endswith("-dev")
        clean_version = version_str.replace("-dev", "")

        # Parse X.Y.Z
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", clean_version)
        if not match:
            raise ValueError(
                f"Invalid version format: {version_str}. Expected X.Y.Z or X.Y.Z-dev"
            )

        major, minor, patch = map(int, match.groups())
        return cls(major=major, minor=minor, patch=patch, is_dev=is_dev)

    def __str__(self) -> str:
        """Convert back to string representation."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-dev" if self.is_dev else base

    def __lt__(self, other: "Version") -> bool:
        """Compare versions (dev versions are less than release versions)."""
        if (self.major, self.minor, self.patch) != (
            other.major,
            other.minor,
            other.patch,
        ):
            return (self.major, self.minor, self.patch) < (
                other.major,
                other.minor,
                other.patch,
            )
        # Same base version: dev < release
        return self.is_dev and not other.is_dev

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.is_dev == other.is_dev
        )

    def next_patch_dev(self) -> "Version":
        """Get next patch development version (e.g., 1.0.0 -> 1.0.1-dev)."""
        return Version(self.major, self.minor, self.patch + 1, is_dev=True)

    def next_minor_dev(self) -> "Version":
        """Get next minor development version (e.g., 1.0.0 -> 1.1.0-dev)."""
        return Version(self.major, self.minor + 1, 0, is_dev=True)

    def next_major_dev(self) -> "Version":
        """Get next major development version (e.g., 1.0.0 -> 2.0.0-dev)."""
        return Version(self.major + 1, 0, 0, is_dev=True)

    def to_release(self) -> "Version":
        """Convert development version to release (e.g., 1.0.0-dev -> 1.0.0)."""
        return Version(self.major, self.minor, self.patch, is_dev=False)


def validate_version_bump(current: str, target: str) -> Tuple[bool, Optional[str]]:
    """Validate a version bump is allowed.

    Returns (is_valid, error_message).

    Rules:
    - From X.Y.Z-dev: can release as X.Y.Z or bump to X.(Y+1).Z or (X+1).Y.Z
    - From X.Y.Z (release): must bump to dev version
    - Version must increase monotonically
    """
    try:
        current_ver = Version.parse(current)
        target_ver = Version.parse(target)
    except ValueError as e:
        return False, str(e)

    # From dev version
    if current_ver.is_dev:
        # Can release the current version (remove -dev)
        if target_ver == current_ver.to_release():
            return True, None

        # Or can bump to next version
        if target_ver in [
            current_ver.to_release(),
            Version(current_ver.major, current_ver.minor + 1, 0, is_dev=False),
            Version(current_ver.major + 1, 0, 0, is_dev=False),
            Version(
                current_ver.major,
                current_ver.minor,
                current_ver.patch + 1,
                is_dev=False,
            ),
        ]:
            return True, None

        return (
            False,
            f"Invalid bump from {current} to {target}. "
            f"From dev version, can release as {current_ver.to_release()} "
            f"or bump to {current_ver.next_patch_dev()}, {current_ver.next_minor_dev()}, or {current_ver.next_major_dev()}",
        )

    # From release version: must bump to dev
    if not target_ver.is_dev:
        return (
            False,
            f"Invalid bump from {current} to {target}. "
            f"From release version, must bump to dev version "
            f"({current_ver.next_patch_dev()}, {current_ver.next_minor_dev()}, or {current_ver.next_major_dev()})",
        )

    # Check if target is a valid next dev version
    if target_ver in [
        current_ver.next_patch_dev(),
        current_ver.next_minor_dev(),
        current_ver.next_major_dev(),
    ]:
        return True, None

    return (
        False,
        f"Invalid bump from {current} to {target}. "
        f"Expected one of: {current_ver.next_patch_dev()}, {current_ver.next_minor_dev()}, {current_ver.next_major_dev()}",
    )


@dataclass
class ValidationResult:
    """Result of pre-release validation."""

    errors: List[str]
    warnings: List[str]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def format(self) -> str:
        """Format validation results for display."""
        lines = []

        if self.errors:
            lines.append("❌ Validation failed:")
            for error in self.errors:
                lines.append(f"  • {error}")

        if self.warnings:
            if lines:
                lines.append("")
            lines.append("⚠ Warnings:")
            for warning in self.warnings:
                lines.append(f"  • {warning}")

        if not self.errors and not self.warnings:
            lines.append("✓ All validation checks passed")

        return "\n".join(lines)


def validate_release(deck: Deck, target_version: str) -> ValidationResult:
    """Validate that a release can proceed.

    Checks:
    - Version bump is valid
    - No uncommitted changes
    - Tag doesn't exist
    - Changelog entry exists
    - Description file exists
    - Screenshots exist (warning only)
    """
    errors = []
    warnings = []

    # Check version bump
    is_valid, error = validate_version_bump(deck.version, target_version)
    if not is_valid:
        errors.append(f"Version bump validation failed: {error}")

    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ["jj", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        # jj status outputs "The working copy has no changes" when clean
        if "no changes" not in result.stdout.lower():
            errors.append("Working copy has uncommitted changes (run 'jj status')")
    except FileNotFoundError:
        # Fall back to git if jj is not available
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip():
                errors.append("Working copy has uncommitted changes (run 'git status')")
        except (subprocess.CalledProcessError, FileNotFoundError):
            warnings.append("Could not check for uncommitted changes")

    # Check if tag already exists
    tag_name = f"{deck.tag_name}/{target_version}"
    try:
        result = subprocess.run(
            ["git", "tag", "--list", tag_name],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout.strip():
            errors.append(f"Git tag '{tag_name}' already exists")
    except (subprocess.CalledProcessError, FileNotFoundError):
        warnings.append("Could not check if git tag exists")

    # Check changelog entry
    changelog_path = Path(deck.content_dir) / "changelog.md"
    if not changelog_path.exists():
        errors.append(f"Changelog not found: {changelog_path}")
    else:
        try:
            entry = ChangelogParser.get_version_entry(changelog_path, target_version)
            if not entry:
                errors.append(
                    f"No changelog entry found for version {target_version} in {changelog_path}"
                )
        except Exception as e:
            errors.append(f"Error parsing changelog: {e}")

    # Check description file
    description_path = Path(deck.description_file)
    if not description_path.exists():
        errors.append(f"Description file not found: {description_path}")
    elif description_path.stat().st_size == 0:
        errors.append(f"Description file is empty: {description_path}")

    # Check description markdown (for website)
    description_md_path = Path(deck.content_dir) / "description.md"
    if not description_md_path.exists():
        warnings.append(f"Description markdown not found: {description_md_path}")
    elif description_md_path.stat().st_size == 0:
        warnings.append(f"Description markdown is empty: {description_md_path}")

    # Check screenshots (warning only)
    screenshot_dir = Path(deck.content_dir) / "screenshots"
    if not screenshot_dir.exists():
        warnings.append(
            f"No screenshots directory found: {screenshot_dir}. "
            "AnkiWeb description will lack images."
        )
    else:
        # Check for expected screenshot files
        card_types = ["pronunciation", "listening", "reading", "spelling"]
        missing = []
        for card_type in card_types:
            for side in ["q", "a"]:
                screenshot = screenshot_dir / f"{card_type}_{side}.png"
                if not screenshot.exists():
                    missing.append(screenshot.name)
        if missing:
            warnings.append(
                f"Some screenshots are missing: {', '.join(missing[:4])}"
                + (f" and {len(missing) - 4} more" if len(missing) > 4 else "")
            )

    # Check AnkiWeb ID (warning only)
    if not deck.ankiweb_id:
        warnings.append(
            "No AnkiWeb ID found. Remember to upload to AnkiWeb and add the ID to decks.yaml"
        )

    return ValidationResult(errors=errors, warnings=warnings)


def update_description_file_version(description_file: Path, new_version: str) -> None:
    """Update the version in a description HTML file.

    The file should contain a line like:
    <b>Version: </b>1.0.0-dev

    This function updates that line with the new version.
    """
    if not description_file.exists():
        raise FileNotFoundError(f"Description file not found: {description_file}")

    # Read the file
    content = description_file.read_text()
    lines = content.split("\n")

    # Find and update the version line
    version_pattern = re.compile(r"^<b>Version: </b>(.+)$")
    updated = False

    for i, line in enumerate(lines):
        match = version_pattern.match(line)
        if match:
            lines[i] = f"<b>Version: </b>{new_version}"
            updated = True
            break

    if not updated:
        raise ValueError(
            f"Could not find version line in {description_file}. "
            "Expected format: <b>Version: </b>X.Y.Z"
        )

    # Write back
    description_file.write_text("\n".join(lines))


def update_decks_yaml_version(
    registry_path: Path, deck_id: str, new_version: str
) -> None:
    """Update the version for a specific deck in decks.yaml.

    Uses a simple regex replacement to preserve file structure and formatting.
    """
    import yaml

    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")

    # Read the file
    content = registry_path.read_text()

    # First verify the deck exists by parsing YAML
    data = yaml.safe_load(content)
    if "decks" not in data or deck_id not in data["decks"]:
        raise ValueError(f"Deck '{deck_id}' not found in {registry_path}")

    # Find the deck section and update its version using regex
    # Pattern: match "deck_id:" followed by version line within that section
    # We need to be careful to only replace within the correct deck section

    # Split into lines and find the deck
    lines = content.split("\n")
    deck_found = False
    version_updated = False

    for i, line in enumerate(lines):
        # Check if this is the start of our deck section
        if line.strip() == f"{deck_id}:":
            deck_found = True
            continue

        # If we found our deck, look for the version line
        if deck_found:
            # Check if this is another deck (indentation returns to base level)
            if line and not line.startswith(" ") and line.strip():
                # We've moved to a new deck section without finding version
                break

            # Check if this is the version line
            if line.strip().startswith("version:"):
                # Update the version while preserving indentation
                indent = len(line) - len(line.lstrip())
                lines[i] = " " * indent + f"version: {new_version}"
                version_updated = True
                break

    if not version_updated:
        raise ValueError(
            f"Could not update version for deck '{deck_id}' in {registry_path}"
        )

    # Write back
    registry_path.write_text("\n".join(lines))


def create_release_commit(deck: Deck, version: str) -> None:
    """Create a release commit using jj or git.

    Commit message format: "release: TAG_NAME VERSION"
    Example: "release: EN_to_ES_625_Words 1.0.0"
    """
    commit_message = f"release: {deck.tag_name} {version}"

    # Try jj first
    try:
        subprocess.run(
            ["jj", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Created commit: {commit_message}")
        return
    except FileNotFoundError:
        pass  # jj not available, try git
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create commit with jj: {e.stderr}")

    # Fall back to git
    try:
        subprocess.run(
            ["git", "commit", "-a", "-m", commit_message],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Created commit: {commit_message}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create commit with git: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Neither jj nor git is available")


def create_git_tag(deck: Deck, version: str) -> None:
    """Create a git tag for the release.

    Tag format: TAG_NAME/VERSION
    Example: EN_to_ES_625_Words/1.0.0
    """
    tag_name = f"{deck.tag_name}/{version}"

    try:
        subprocess.run(
            ["git", "tag", tag_name],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Created tag: {tag_name}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create tag: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("git is not available")


def create_post_release_commit(deck: Deck, next_dev_version: str) -> None:
    """Create a post-release commit for the next dev version.

    Commit message format: "chore: bump DECK_ID to VERSION"
    Example: "chore: bump en_to_es_625 to 1.0.1-dev"
    """
    commit_message = f"chore: bump {deck.deck_id} to {next_dev_version}"

    # Try jj first
    try:
        subprocess.run(
            ["jj", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Created commit: {commit_message}")
        return
    except FileNotFoundError:
        pass  # jj not available, try git
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create post-release commit with jj: {e.stderr}")

    # Fall back to git
    try:
        subprocess.run(
            ["git", "commit", "-a", "-m", commit_message],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Created commit: {commit_message}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create post-release commit with git: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Neither jj nor git is available")
