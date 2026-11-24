# WordPress community data: start here

This is a **skill**: a small folder of instructions your AI agent reads so it can answer questions about WordPress meetups and WordCamps for you. There's no new dashboard to learn. You ask your own agent, and it reads the data and answers.

Everything it uses is public. No logins, no keys.

## What you can ask

- "Which US meetup groups have met in person in the last 6 months?"
- "Which communities held in-person WordCamps between 2022 and 2026?"
- "Is the Austin WordPress meetup still active? Who organizes it?"
- "Which big US groups went quiet in the last year?"
- "What WordCamps are coming up in Canada?"
- "Give me that as a spreadsheet."

## What to do with the .zip

Pick the agent you use.

No .zip? If your agent can browse or run commands, point it at https://github.com/WordPress/wp-events-dashboard/tree/main/skill/wp-community-data and say: "Install this skill." Or ask the person who shared it for the .zip.

**Claude (claude.ai or the desktop app)**
1. Open Claude's settings and find **Skills** (under Capabilities or Customize, depending on your version).
2. Upload the .zip as-is. Don't unzip it.
3. Start a new chat and ask a question. Claude picks the skill up on its own.

If you don't see Skills, start a chat, attach the .zip, and say: "Read SKILL.md in this zip and use it to answer my questions."

**Claude Code**
Give it the .zip and say: "Install this skill in my skills folder." Then start a new session.

**Cursor**
Same idea, but the folder is `~/.cursor/skills/`. Or attach the .zip in a chat and say "install this skill."

**ChatGPT, Gemini, or anything else**
Attach the .zip (or just `SKILL.md`) and say: "Read SKILL.md and use it for the rest of this chat." If your agent can't run code, that's fine. The skill tells it how to read the data directly.

## What it can't do (yet)

- **In-person dates before November 24, 2025.** Tracking started on November 24, 2026 and reached back one year. For earlier meetings there's only a "last met" date, which doesn't say whether the meeting was in person.
- **Attendance.** It knows member counts and organizer estimates, not who came.
- **Anything not on meetup.com or WordCamp Central**, and nothing from internal tools.

## Using it well

- Ask for the format you want: a table, a count, a spreadsheet. Spreadsheets need an agent that can run code (Claude, Claude Code and Cursor can). Otherwise ask for a table you can paste.
- Your agent should tell you how fresh the data is and which caveats apply. If it doesn't, ask.
- Organizer names are public on meetup.com, but ask for them only when you need them.

## What's inside

| File | For |
|---|---|
| `START-HERE.md` | You (this page) |
| `SKILL.md` | Your agent: how to answer, the sources, the caveats |
| `references/sources.md` | Your agent: every field and gotcha |
| `references/recipes.md` | Your agent: worked examples |
| `scripts/wpcd.py` | Your agent: a small helper it runs if it can run Python |

Questions or something wrong? Open an issue at https://github.com/WordPress/wp-events-dashboard/issues.
