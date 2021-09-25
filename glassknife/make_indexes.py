#!/usr/bin/env python

"""Create a set of yearly and monthly index files for daily notes files."""

import argparse
import datetime as dt
import logging
import os
from pathlib import Path
from typing import Dict, List

from glassknife.common import daily_note_files, logging_verbosity
from glassknife.config import Vault, load_config

LOG = logging.getLogger(__name__)


def template_contents(vault: Vault) -> str:
    """Return the contents of the Daily Note template file."""

    return (vault.templates_dir / vault.daily_template_name).read_text()


def valid_grouped_note_files(vault: Vault) -> Dict[int, Dict[int, List[str]]]:
    """Yield a series of note filenames and the year, month, and day of their creation."""

    empty_template = template_contents(vault).strip()

    grouped: Dict[int, Dict[int, List[str]]] = {}

    today = dt.date.today()

    for note, note_date in daily_note_files(vault.daily_notes_dir):
        name = note.name
        LOG.info("Found %s", name)

        if note_date < today and note.read_text().strip() == empty_template:
            LOG.info("%r is empty -- pruning", name)
            note.unlink()
            continue

        grouped.setdefault(note_date.year, {}).setdefault(note_date.month, []).append(note.stem)

    return grouped


def make_indexes(vault: Vault):
    """Create yearly and monthly index files for existing notes."""

    for year, months in valid_grouped_note_files(vault).items():
        yearname = f"Daily notes - {year}"
        yearpath = vault.path / f"{yearname}.md"

        LOG.info("Processing yearly MOC %r", yearpath.name)
        year_header = [f"Months in {year}:"]
        year_links = []

        for month, notes in sorted(months.items(), reverse=True):
            monthname = f"Daily notes - {year}-{month:02}"
            monthpath = vault.path / f"{monthname}.md"

            year_links.append(f"[[{monthname}]]")

            LOG.info("Processing monthly MOC %r", monthpath.name)
            month_header = [f"Days in {year}-{month:02}:"]
            month_links = [f"[[{note}]]" for note in sorted(notes, reverse=True)]

            write_index_file(monthpath, month_header, month_links, [])
            touch(monthpath, year, month)

        write_index_file(yearpath, year_header, year_links, [])
        touch(yearpath, year, 1)

    tomorrow = (dt.date.today() + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_file = vault.daily_notes_dir / f"{tomorrow}.md"
    if tomorrow_file.exists():
        LOG.debug("The tomorrow file %r already exists", tomorrow_file.name)
    else:
        LOG.debug("Creating the empty tomorrow file %r", tomorrow_file.name)
        tomorrow_file.write_text(template_contents(vault))


def touch(path: Path, year: int, month: int):
    """Set the mtime and atime of the file to 1st day of the year and month."""

    tstamp = dt.datetime(year, month, 1).timestamp()
    os.utime(path, times=(tstamp, tstamp))


def write_index_file(path, default_header, links, default_footer):
    """Create or update an index file."""

    if path.exists():
        LOG.debug("Editing existing file %r", path.name)
        with path.open() as infile:
            header = []
            footer = []
            for line in infile:
                if line == "---\n":
                    break
                header.append(line.rstrip("\n"))

            for line in infile:
                if line == "---\n":
                    break

            for line in infile:
                footer.append(line.rstrip("\n"))

        if header and not header[-1]:
            del header[-1]

        if footer and not footer[0]:
            del footer[0]

    else:
        LOG.debug("Writing new file %r", path.name)
        header = default_header
        footer = default_footer

    with path.open("w") as outfile:
        outfile.write("\n".join(header))
        outfile.write("\n\n---\n\n")
        outfile.write("\n".join(links))
        outfile.write("\n\n---\n\n")
        outfile.write("\n".join(footer))


def handle_command_line():
    """Handle the command line."""

    parser = argparse.ArgumentParser("make-indexes")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
    parser.add_argument("vault", help="The name of the vault to process")
    args = parser.parse_args()

    logging_verbosity(args.verbose)

    config = load_config()
    make_indexes(config.vaults[args.vault])


if __name__ == "__main__":
    handle_command_line()
