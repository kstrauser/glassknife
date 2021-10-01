Glass Knife
===========

**Python utilities for working with Obsidian vaults.**

Obsidian_ is a pretty layer on top of a folder full of Markdown files. The contents of that folder are Obsidian's database and you can add, remove, and edit files inside it at will. This gives users incredible flexibility to manage those files and their contents outside of Obsidian, which they may want to do for a few reasons:

* Obsidian extensions are written in JavaScript and a user wants to develop tooling in their own preferred language. JavaScript is fine, but I like Python.
* Writing a standalone program outside Obsidian is way easier than writing an extension. Extensions are cool, but that can be a lot of overhead for a simple need.
* A user wants to run tasks on a schedule, even if Obsidian itself isn't running on their computer. Sometimes a simple cron job is exactly the right tool.
* The program they want to write wouldn't benefit from running inside Obsidian. Unix tools are *really good* at text processing.

Current status
==============

I wrote these tools for my own personal use. They might be useful for other people, too, so I'm releasing them although they're still pretty early-stage. They make a few assumptions:

* All of a vault's daily notes live in the same directory.
* All of a vault's templates live in the same directory.
* Daily notes use the default naming convention of ``YYYY-MM-DD.md``.
* You're using Reminders or OmniFocus_ to record your action items.
* You're using `Day One`_ as your journal.

It should be very easy to edit the code if your setup doesn't exactly match mine. While I intend to make this more configurable later, I haven't gotten around to that yet.

Installation
============

``pip install glassknife``

Configuration
=============

Make a file in your home directory called ``~/.config/glassknife/config.yaml`` (but using your own information)::

    vaults:
      Everything:
        path: /path/to/my/vault
        notes_subdir: "Daily notes go here"
        templates_subdir: "Templates are here"
        daily_template_name: "My daily note template.md"

    process_notes:
        actions:
            "- ": Reminders
            "* ": "Day One"
            "- [ ] ": OmniFocus

The tools
=========

These are the first tools in the collection.

make-indexes
------------

**Create a set of yearly and monthly index files for daily notes files.**

I have a ``Daily notes`` directory with a lot of unindexed notes in it. I wanted to have `Maps of Content`_ from calendar months to all the notes in each month, and MOCs from years to the monthly MOCs in each year. For instance, suppose I have these daily notes:

* ``2020-12-31.md``
* ``2021-01-01.md``
* ``2021-01-02.md``
* ``2021-02-02.md``

Then I'd want to have annual indexes like ``Daily notes - 2020.md``::

    Months in 2020:

    We stayed home a lot this year.

    ---

    [[Daily notes - 2020-12]]

    ---

and ``Daily notes - 2021.md``::

    Months in 2021:

    ---

    [[Daily notes - 2021-01]]
    [[Daily notes - 2021-02]]

    ---

    This is the year we went camping a lot!

Each month's index would look similar, like ``Daily notes - 2021-01.md``::

    Days in 2021-01:

    We made it to a grocery store this month.

    ---

    [[2021-01-01]]
    [[2021-01-02]]

    ---

``make-indexes Everything`` does this for me. Now it's easy to drill down to all the months in 2021, and from there all the days in September 2021. I run it from an hourly cron job like::

    0 * * * * /path/to/glassknife/.venv/bin/make-indexes Everything

Note that ``make-indexes`` "owns" the content between the two separator ``---`` lines. Your own notes above and below that block are yours to edit as you see fit.

process-notes
-------------

**Send items in your daily notes to other programs.**

I wrote a `Quick Journaling`_ extension for Drafts_. After finding Obsidian, I wanted something similar for it so that I could record actions I want to take and journal entries I'd like to make into applications other than Obsidian (which is brilliant for lots of things but still bested by special-purpose applications in some ways). This is the start of my answer to it. My daily notes template looks like::

    # Work

    # Personal

    #unprocessed

After adding things to a note all day, the note might end up looking like::

    # Work

    - [ ] Tell boss I'm going on vacation

    # Personal

    Worked on [[Glass Knife]] project.
    * Had dim sum for lunch.
    Watching [[Ted Lasso]]
    * Took the car for an oil change.
    - [ ] Buy coffee filters
    - Water the plant

    # unprocessed

Running ``process-notes Everything`` with the sample configuration given above will do a few things:

* Lines starting with ":literal:`- [ ] \ `" will turn into OmniFocus actions and be removed from the daily note.
* Lines starting with ":literal:`- \ `" will become actions in the Reminders.app Inbox.
* Lines starting with ":literal:`* \ `" will be collected together and turned into a Day One journal entry, and removed from the daily note.
* Since the ``# Work`` section is now empty, it will be removed from the daily note.
* The ``#unprocessed`` tag will be removed from the daily note.

The end result will look like::

    # Personal

    Worked on [[Glass Knife]] project.
    Watching [[Ted Lasso]]

If the resulting note is completely empty because all lines have been processed and there are no sections left, it will be deleted.

I run this nightly with a cron job::

    50 23 * * * /path/to/obsidian/.venv/bin/process-notes Stuff

Configuration
^^^^^^^^^^^^^

The example configuration file above had this block::

    process_notes:
        actions:
            "- ": Reminders
            "* ": "Day One"
            "- [ ] ": OmniFocus

That means that a line beginning with one those prefixes will be sent to the corresponding program. Feel free to alter this to your own preferences! If you don't use Day One, remove the ``"* ": "Day One"`` item. If you want lines starting with ```&&&`` to be sent to Reminders, add ``"&&&": Reminders`` to it.

As of this writing,

* Day One
* OmniFocus
* Reminders

are supported.

Contributing
============

Patches are welcome! Use Black_ to format them, and Pylint_, Flake8_, and mypy_ for linting.

Copyright
=========

Glass Knife is copyright 2021 `Kirk Strauser <mailto:kirk@strauser.com>`_, and distributed under the terms of the Apache-2.0 License.

.. _Black: https://pypi.org/project/black/
.. _Day One: https://dayoneapp.com/
.. _Drafts: https://getdrafts.com/
.. _Flake8: https://flake8.pycqa.org/en/latest/
.. _Maps of Content: https://publish.obsidian.md/lyt-kit/Umami/MOCs+(defn)
.. _mypy: http://mypy-lang.org/
.. _Obsidian: https://obsidian.md/
.. _OmniFocus: https://www.omnigroup.com/omnifocus/
.. _Pylint: https://pylint.org/
.. _Quick Journaling: https://actions.getdrafts.com/g/1Sd
