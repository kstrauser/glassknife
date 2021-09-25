#!/usr/bin/env python

"""Send items in your daily notes to other programs."""

import argparse
import datetime as dt
import logging
import re
import webbrowser
from typing import List, Tuple
from urllib.parse import quote

from glassknife.common import daily_note_files, logging_verbosity
from glassknife.config import Vault, load_config

LOG = logging.getLogger(__name__)
UNPROCESSED = "#unprocessed"

TO_DO = "- [ ]"
JOURNAL = "*"

LINK_PATTERN = re.compile(
    r"""
\[\[                # Opening brackets
    (?:[^\]]*?\|)?  # Optionally, anything but brackets up until "|"
    ([^]]*?)        # The rest of the string until...
\]\]                # Closing brackets
""",
    re.VERBOSE,
)


def cleaned(text: str, prefix: str) -> str:
    """Return the line, minus the leading flag character and surrounding whitespace.

    This replaces "[[Link]]" or "[[Link|alias]]" with "Link" and "alias", respectively.
    """

    unprefixed = text.removeprefix(prefix)
    unlinked = LINK_PATTERN.sub(r"\1", unprefixed)
    return unlinked.strip()


def process_daily_notes(vault: Vault, dry_run: bool):
    """Look for unprocessed notes, sent appropriate lines to various apps, and mark them done."""

    today = dt.date.today()

    for note, note_date in daily_note_files(vault.daily_notes_dir):
        content = note.read_text()
        if UNPROCESSED not in content:
            continue

        if note_date > today:
            LOG.debug("Not processing future note %r", note.name)
            continue

        LOG.info("Processing %r from %s", note.name, note_date)
        actions, journals, new_content = parse(content)

        if new_content == "\n":
            LOG.info("Deleting newly empty file")
            if not dry_run:
                note.unlink()
        else:
            LOG.info("Writing new content: %r", new_content)
            if not dry_run:
                note.write_text(new_content)

        for action in actions:
            send_to_omnifocus(action, dry_run)

        if journals:
            send_to_dayone("\n\n".join(journals), dry_run)


def parse(text: str) -> Tuple[List[str], List[str], str]:
    """Process the lines in the file.

    Return:
    - A list of to-do actions
    - A list of journal entries
    - The input text minus the processed lines, minus any newly emptied Markdown sections
    """

    lines = []
    actions = []
    journals = []

    for line in text.splitlines():
        if line.startswith(TO_DO):
            actions.append(cleaned(line, TO_DO))
        elif line.startswith(JOURNAL):
            journals.append(cleaned(line, JOURNAL))
        else:
            lines.append(line.replace(UNPROCESSED, "").rstrip())

    output_lines = remove_empty_sections(lines)
    out = "\n".join(output_lines).strip() + "\n"

    return actions, journals, out


def remove_empty_sections(lines: List[str]) -> List[str]:
    """Return a copy of the list of lines with any empty # Section parts removed."""

    section: List[str] = []
    sections = [section]
    for line in lines:
        if line.startswith("# "):
            section = [line]
            sections.append(section)
        else:
            section.append(line)

    output_lines = []
    for section in sections:
        if not section:
            continue
        section = remove_empty_lines(section)
        if len(section) > 1:
            output_lines.extend(section + [""])

    return output_lines


def remove_empty_lines(lines: List[str]) -> List[str]:
    """Return a copy of the list of lines without any trailing empty lines."""

    new_lines = lines[:]
    while new_lines and new_lines[-1] == "":
        new_lines.pop(-1)
    return new_lines


def send_to_dayone(text: str, dry_run: bool):
    """Create a Day One journal entry from the text."""

    LOG.info("Sending to Day One: %r", text)
    if not dry_run:
        webbrowser.open(f"dayone2://post?entry={quote(text)}")


def send_to_omnifocus(text: str, dry_run: bool):
    """Create an OmniFocus action from the text."""

    LOG.info("Sending to OmniFocus: %r", text)
    if not dry_run:
        webbrowser.open(f"omnifocus://x-callback-url/add?name={quote(text)}&autosave=true")


def handle_command_line():
    """Handle the command line."""

    parser = argparse.ArgumentParser("process-notes")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity")
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Only show what would have been done"
    )
    parser.add_argument("vault", help="The name of the vault to process")
    args = parser.parse_args()

    logging_verbosity(args.verbose)

    config = load_config()
    process_daily_notes(config.vaults[args.vault], args.dry_run)


if __name__ == "__main__":
    handle_command_line()
