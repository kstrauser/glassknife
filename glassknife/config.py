"""glassknife config handler."""

from functools import cache
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel
from xdg import xdg_config_home

CONFIG_FILE = xdg_config_home() / "glassknife" / "config.yaml"


class Vault(BaseModel):
    """Configuration for a single Obsidian vault."""

    path: Path
    notes_subdir: str
    templates_subdir: str
    daily_template_name: str

    @property
    def daily_notes_dir(self) -> Path:
        """Return the path to the daily notes directory."""

        return self.path / self.notes_subdir

    @property
    def templates_dir(self) -> Path:
        """Return the path to the templates directory."""

        return self.path / self.templates_subdir


class ProcessNotes(BaseModel):
    """Configuration for process-notes."""

    actions: Dict[str, str]


class Config(BaseModel):
    """glassknife configuration class."""

    process_notes: ProcessNotes
    vaults: Dict[str, Vault]


@cache
def load_config():
    """Fetch the stored config from its YAML file."""

    conf = yaml.safe_load(CONFIG_FILE.read_text())

    return Config.parse_obj(conf)
