"""Deck registry management for AnkiLangs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class Deck:
    """Represents an AnkiLangs deck."""

    deck_id: str
    name: str
    tag_name: str
    description_file: str
    content_dir: str
    version: str
    ankiweb_id: Optional[str]
    deck_type: str  # "625" or "minimal_pairs"
    source_locale: str
    target_locale: str

    @property
    def build_folder(self) -> Path:
        """Derived: build output folder."""
        return Path("build") / self.tag_name

    @property
    def website_slug(self) -> str:
        """Derived: URL slug for website."""
        return self.deck_id.replace("_", "-")

    @property
    def github_download_url(self) -> str:
        """Derived: GitHub release download URL."""
        # URL encode the tag name (/ becomes %2F)
        encoded_tag = f"{self.tag_name}%2F{self.version.replace('-dev', '')}"
        return (
            f"https://github.com/ankilangs/ankilangs/releases/download/{encoded_tag}/"
        )

    @property
    def screenshot_urls(self) -> List[str]:
        """Derived: raw GitHub URLs for screenshots."""
        base_url = f"https://raw.githubusercontent.com/ankilangs/ankilangs/main/{self.content_dir}/screenshots"
        card_types = ["pronunciation", "listening", "reading", "spelling"]
        urls = []
        for card_type in card_types:
            urls.append(f"{base_url}/{card_type}_q.png")
            urls.append(f"{base_url}/{card_type}_a.png")
        return urls

    @property
    def is_dev_version(self) -> bool:
        """Check if this is a development version."""
        return self.version.endswith("-dev")

    @property
    def release_version(self) -> str:
        """Get the version without -dev suffix."""
        return self.version.replace("-dev", "")

    def __repr__(self) -> str:
        return f"Deck({self.deck_id!r}, version={self.version!r})"


class DeckRegistry:
    """Registry of all AnkiLangs decks."""

    def __init__(self, registry_path: Path = Path("decks.yaml")):
        """Load deck registry from YAML file."""
        self.registry_path = registry_path
        self.decks: Dict[str, Deck] = {}
        self._load()

    def _load(self):
        """Load decks from YAML file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Deck registry not found: {self.registry_path}")

        with open(self.registry_path, "r") as f:
            data = yaml.safe_load(f)

        if not data or "decks" not in data:
            raise ValueError(f"Invalid deck registry format in {self.registry_path}")

        for deck_id, deck_data in data["decks"].items():
            self.decks[deck_id] = Deck(
                deck_id=deck_id,
                name=deck_data["name"],
                tag_name=deck_data["tag_name"],
                description_file=deck_data["description_file"],
                content_dir=deck_data["content_dir"],
                version=deck_data["version"],
                ankiweb_id=deck_data.get("ankiweb_id"),
                deck_type=deck_data["deck_type"],
                source_locale=deck_data["source_locale"],
                target_locale=deck_data["target_locale"],
            )

    def get(self, deck_id: str) -> Optional[Deck]:
        """Get a deck by ID."""
        return self.decks.get(deck_id)

    def all(self) -> List[Deck]:
        """Get all decks."""
        return list(self.decks.values())

    def by_type(self, deck_type: str) -> List[Deck]:
        """Get all decks of a specific type."""
        return [d for d in self.decks.values() if d.deck_type == deck_type]

    def by_source_locale(self, source_locale: str) -> List[Deck]:
        """Get all decks with a specific source locale."""
        return [d for d in self.decks.values() if d.source_locale == source_locale]

    def get_latest_release_version(self, deck_id: str) -> Optional[str]:
        """Get the latest released version from git tags."""
        import subprocess

        deck = self.get(deck_id)
        if not deck:
            return None

        try:
            # Get all tags for this deck
            result = subprocess.run(
                ["git", "tag", "--list", f"{deck.tag_name}/*"],
                capture_output=True,
                text=True,
                check=True,
            )

            tags = result.stdout.strip().split("\n")
            if not tags or tags == [""]:
                return None

            # Extract versions and find the latest
            versions = []
            for tag in tags:
                # Tag format: TAG_NAME/VERSION
                if "/" in tag:
                    version = tag.split("/", 1)[1]
                    # Skip dev versions
                    if not version.endswith("-dev"):
                        versions.append(version)

            if not versions:
                return None

            # Sort versions (simple string sort works for semver)
            versions.sort(reverse=True)
            return versions[0]

        except subprocess.CalledProcessError:
            return None

    def __len__(self) -> int:
        return len(self.decks)

    def __iter__(self):
        return iter(self.decks.values())

    def __repr__(self) -> str:
        return f"DeckRegistry({len(self.decks)} decks)"
