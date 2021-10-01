#!/usr/bin/env python

"""Send items in your daily notes to other programs."""

import argparse
import datetime as dt
import logging
import re
import subprocess
import webbrowser
from typing import Callable, Dict, List, Tuple
from urllib.parse import quote

from glassknife.common import daily_note_files, logging_verbosity
from glassknife.config import Vault, load_config, ProcessNotes

LOG = logging.getLogger(__name__)
UNPROCESSED = "#unprocessed"

LINK_PATTERN = re.compile(
    r"""
\[\[                # Opening brackets
    (?:[^\]]*?\|)?  # Optionally, anything but brackets up until "|"
    ([^]]*?)        # The rest of the string until...
\]\]                # Closing brackets
""",
    re.VERBOSE,
)

ActionFunc = Callable[[str, bool], None]
ACTIONS: Dict[str, ActionFunc] = {}


def register(name):
    """Register a mapping of an action name to a function that implements it."""

    def outer(func):
        ACTIONS[name] = func
        return func

    return outer


@register("Day One")
def send_to_dayone(text: str, dry_run: bool):
    """Create a Day One journal entry from the text."""

    LOG.info("Sending to Day One: %r", text)
    if not dry_run:
        webbrowser.open(f"dayone2://post?entry={quote(text)}")


@register("OmniFocus")
def send_to_omnifocus(text: str, dry_run: bool):
    """Create an OmniFocus action from the text."""

    LOG.info("Sending to OmniFocus: %r", text)
    if not dry_run:
        webbrowser.open(f"omnifocus://x-callback-url/add?name={quote(text)}&autosave=true")


@register("Reminders")
def send_to_reminders(text: str, dry_run: bool):
    """Create a Reminders item from the text."""

    LOG.info("Sending to Reminders: %r", text)
    if not dry_run:
        # This uses the command line "reminders" tool from https://github.com/keith/reminders-cli
        subprocess.run(["/usr/local/bin/reminders", "add", "Inbox", text], check=True)


def cleaned(text: str, prefix: str) -> str:
    """Return the line, minus the leading flag character and surrounding whitespace.

    This replaces "[[Link]]" or "[[Link|alias]]" with "Link" and "alias", respectively.
    """

    unprefixed = text.removeprefix(prefix)
    unlinked = LINK_PATTERN.sub(r"\1", unprefixed)
    return unlinked.strip()


def process_daily_notes(vault: Vault, action_map: Dict[str, ActionFunc], dry_run: bool):
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
        actions, new_content = parse(content, action_map)

        if new_content == "\n":
            LOG.info("Deleting newly empty file")
            if not dry_run:
                note.unlink()
        else:
            LOG.info("Writing new content: %r", new_content)
            if not dry_run:
                note.write_text(new_content)

        for func, items in actions.items():
            if func is send_to_dayone:
                func("\n\n".join(items), dry_run)
            else:
                for item in items:
                    func(item, dry_run)


def parse(text: str, action_map: Dict[str, ActionFunc]) -> Tuple[Dict[ActionFunc, List[str]], str]:
    """Process the lines in the file.

    Return:
    - A list of to-do actions
    - A list of journal entries
    - The input text minus the processed lines, minus any newly emptied Markdown sections
    """

    lines = []

    actions: Dict[ActionFunc, List[str]] = {}
    prefixes = tuple(action_map.keys())

    for line in text.splitlines():
        if not line.startswith(prefixes):
            lines.append(line.replace(UNPROCESSED, "").rstrip())
            continue

        for prefix, func in action_map.items():
            if line.startswith(prefix):
                actions.setdefault(func, []).append(cleaned(line, prefix))
                break
        else:
            raise ValueError(f"{text} didn't match any of {prefixes}.")

    output_lines = remove_empty_sections(lines)
    out = "\n".join(output_lines).strip() + "\n"

    return actions, out


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


def make_action_map(process_notes: ProcessNotes) -> Dict[str, ActionFunc]:
    """Make a mapping of daily note line prefixes to the functions they should be sent to."""

    action_map: Dict[str, ActionFunc] = {
        prefix: ACTIONS[action_name] for prefix, action_name in process_notes.actions.items()
    }

    return action_map


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
    action_map = make_action_map(config.process_notes)
    process_daily_notes(config.vaults[args.vault], action_map, args.dry_run)


if __name__ == "__main__":
    handle_command_line()
