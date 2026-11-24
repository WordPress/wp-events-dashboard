---
name: wp-community-data
description: Answer questions about WordPress community events from public data. Covers Meetup groups (which met recently, in person or online, members, organizers, activity status) and WordCamps and other WordCamp Central events (by year, place, in person or virtual). Use when someone asks things like "which US meetup groups met in person in the last 6 months", "which cities held WordCamps from 2022 to 2026", "is the Austin group still active", or "what WordCamps are coming up".
---

# WordPress community data

Answer questions about WordPress meetups and WordCamps from public data. No logins or API keys are needed. Paths in this skill are relative to the folder that holds this file.

If you were handed this skill as a .zip, do the steps in the last section first.

## How to answer

1. **Pick the source.** Meetup groups come from the events dashboard JSON. WordCamps and other organized events come from WordCamp Central.
2. **If you can run Python, use the helper.** It needs only the standard library.
   ```
   python3 scripts/wpcd.py meetups   --country USA --months 8 --in-person
   python3 scripts/wpcd.py meetups   --group austin --organizers
   python3 scripts/wpcd.py wordcamps --country US --from 2022 --to 2026 --in-person --by-community
   python3 scripts/wpcd.py wordcamps --upcoming --all-types
   ```
   Each command prints a note before the table with the "as of" date and any data warning. Pass the note on. Add `--format csv` for a spreadsheet or `--format json` to process the rows further. `-h` lists every option.
3. **If you can't run code, fetch the URLs under "Sources"** and filter them yourself with the field guide in `references/sources.md`. The WordCamp API returns 100 records per page. Read the `X-WP-TotalPages` header and fetch every page, or the answer will be incomplete.
4. **State the caveats that apply** and the "as of" date.
5. **Answer in the shape the person asked for**, such as a list, a count, or a table. Say which source each part came from. `references/recipes.md` has a worked example for each common question.

## Sources

| What | URL | Refreshed |
|---|---|---|
| Every Meetup group in the WordPress chapter program (about 720) | https://wordpress.github.io/wp-events-dashboard/dashboard_data.json | Nightly, around 03:15 UTC |
| WordCamps and other events on WordCamp Central | https://central.wordcamp.org/wp-json/wp/v2/wordcamps | Live |
| Human-friendly dashboard, for linking people to it | https://wordpress.github.io/wp-events-dashboard/ | Nightly |

Field details and gotchas are in `references/sources.md`.

## Caveats to state when they apply

- **In person vs online for Meetups.** `last` is the most recent meeting of any kind, online included. Never present it as an in-person date. In-person dates (`lastInPerson`) start at 2025-11-24, so the data can't say whether a meeting before then was in person. If the helper's note starts with "NOT IN-PERSON DATA", or no group has a `lastInPerson` value, open the answer with this sentence, before any list: "The data can't separate in-person from online meetings yet, so this is every group that met at all."
- **Hybrid meetings count as in person.**
- **Ranges like "6 to 8 months".** List with the upper bound, and also give the count for the lower bound.
- **WordCamp "in person"** means the `Virtual event only` field is blank. Status `closed` means the event happened, and `scheduled` means it's upcoming. Cancelled events are left out unless the person asks for them.
- **Event types.** `wordcamps` returns WordCamps only by default. If the question says "events" rather than "WordCamps", add `--all-types` to include Campus Connect, WordPress Days, and other community events, and say that you did.
- **Community names** come from event titles, so one community can appear under slightly different names across years. The helper merges the common variants, such as state suffixes, "USA", and years. If a community looks split, check the `titles` column.
- **Countries.** The dashboard writes country names such as `USA`, `Canada`, and `Mexico`. Central uses two-letter codes such as `US`. The helper accepts `US` or `USA` for both commands. Before you report "none", check the country spelling.
- **Completeness.** Central lists an event publicly only after it's scheduled, so WordCamps still in planning are missing. If recent years look thin, say the list covers publicly listed events only.

## Privacy

Organizer names are public on meetup.com. Handle them with these rules:

- Include organizer names (`--organizers`) only when the question needs them, for example to say who to contact about one group. Don't build bulk name lists for outreach unless the person asks and it serves a community purpose.
- Don't combine this data with private sources, such as internal tools, CRM notes, or where people live, in anything shared outside the person's own team.
- Leave out any name tied to an event that isn't public yet.

## When the data can't answer it

Say so, and name what's missing. The data has no meetup attendance, no attendee names, nothing about private Meetup groups, and nothing about events that were never listed on meetup.com or WordCamp Central. Don't fill the gap by scraping meetup.com. Point the person to the dashboard repo, https://github.com/WordPress/wp-events-dashboard, to ask for new data.

## If you were handed this as a .zip

1. Unzip it, and keep the `wp-community-data/` folder whole. `SKILL.md` refers to `scripts/` and `references/`.
2. If your harness has a skills folder, you can install the skill there. You can also run everything from the unzipped folder.
   - Claude Code: `~/.claude/skills/wp-community-data/`
   - Cursor: `~/.cursor/skills/wp-community-data/`
   - Claude.ai or the Claude desktop app: the person uploads the .zip, still zipped, under **Skills** in settings. You can't do that step, so tell them.
   - Any other agent: skip the install. Follow this file for the rest of the conversation.
3. Run `python3 scripts/wpcd.py freshness` to confirm the sources are reachable. If you can't run code, fetch the first two URLs under "Sources" instead.
4. Tell the person the skill is ready, and offer two example questions from `START-HERE.md`.
