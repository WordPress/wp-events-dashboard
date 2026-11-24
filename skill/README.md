# wp-community-data skill

A skill that lets anyone's AI agent answer questions about WordPress meetup groups and WordCamps from this dashboard's public data, instead of building a new dashboard for every question. It reads `dashboard_data.json` from the live page and the public WordCamp Central API. No logins, no keys.

It answers questions like "Which US meetup groups met in person in the last 6 months?" or "Which communities held in-person WordCamps from 2022 to 2026?"

## Using it

- **People:** start with [`wp-community-data/START-HERE.md`](wp-community-data/START-HERE.md).
- **Agents:** read [`wp-community-data/SKILL.md`](wp-community-data/SKILL.md).

Claude.ai takes the skill as a .zip. Build one with `bash skill/build-zip.sh`, which writes `~/Downloads/wp-community-data.zip`.

## Changing it

- `wp-community-data/scripts/wpcd.py` is the helper agents run. Python 3 standard library only.
- `bash skill/check.sh` runs every command named in `SKILL.md` and `references/recipes.md` against live data. Run it after any change to the skill or to the shape of `dashboard_data.json`.
- If you add or rename a field in `assemble.py`, update `wp-community-data/references/sources.md` too.
