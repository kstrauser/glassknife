"""Common stuff for glassknife."""

import datetime as dt
import logging
import re
from pathlib import Path
from typing import List, Tuple

LOG = logging.getLogger(__name__)
NOTE_FILENAME_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.md$")


def daily_note_files(daily_notes_dir: Path) -> List[Tuple[Path, dt.date]]:
    """Return a list of Daily Notes and their dates."""

    notes = []

    for note in daily_notes_dir.glob("*-*-*.md"):
        name = note.name
        if not (match := NOTE_FILENAME_PATTERN.match(name)):
            LOG.debug("%r matches the filename glob but not the validation regex", name)
            continue

        year, month, day = match.groups()
        notes.append((note, dt.date(int(year), int(month), int(day))))

    return sorted(notes)


def logging_verbosity(verbose: int):
    """As `verbose` increases, increase the amount of logging details."""

    if verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level)
