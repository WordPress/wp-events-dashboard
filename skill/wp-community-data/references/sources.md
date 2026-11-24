# Sources and fields

## 1. Events dashboard JSON (Meetup groups)

URL: https://wordpress.github.io/wp-events-dashboard/dashboard_data.json
Code and issues: https://github.com/WordPress/wp-events-dashboard

Top level:

- `asOf`: the date the file was built.
- `dates`: when each source was last refreshed (`meetups`, `events`, `pipelineCounts`, `pipelineDetail`, `momentum`). Quote `dates.meetups` as the "as of" date for Meetup answers.
- `meetups`: the Meetup side. Use `meetups.allGroups` for nearly everything.
- `events`: a summary of WordCamp Central events. Its `map.eventList` covers the **current year only**. Use the Central API for anything earlier.
- `pipeline`: WordCamp applications in progress (stage, title, start date, location). It has no people. Don't try to get names from it.

`meetups.allGroups[]`, one object per group:

| Field | Meaning |
|---|---|
| `group` | Group name |
| `city`, `country` | Location. Country is a display name: `USA`, `Canada`, `Mexico`, `United Kingdom` and so on |
| `members` | Members on meetup.com |
| `last` | Date of the most recent meeting of **any** kind (online or in person). `""` means the group has never met |
| `cat` | `Active` (met within 90 days), `Fading` (91 to 365), `Inactive` (over 365), `Never` |
| `url` | The group's meetup.com page |
| `leaders[]` | Local organizers: `n` is the name, `u` is the meetup.com profile. Public on meetup.com |
| `lastInPerson` | Date of the most recent in-person or hybrid meeting since 2025-11-24. Empty means none since then. Published since 2026-11-24 |
| `lastOnline` | Date of the most recent online meeting since 2025-11-24 |
| `inPerson365`, `online365` | Number of in-person and online meetings in the last 365 days. The window rolls forward each night. `null` means not known |

Other useful pieces: `meetups.us` (US group count and how many met in the last 90 days), `meetups.reactivation` (groups that came back since the baseline), `meetups.deadBig` (large groups that went quiet).

## 2. WordCamp Central REST API (WordCamps and other organized events)

URL: https://central.wordcamp.org/wp-json/wp/v2/wordcamps

- Paging: `?per_page=100&page=N`. The `X-WP-TotalPages` header gives the page count (about 16 pages).
- Status filter: `&status=wcpt-closed` (happened), `wcpt-scheduled` (upcoming), `wcpt-cancelled`. Without a status you get closed and scheduled together. Pre-public stages aren't readable without a login.

Fields per event:

| Field | Meaning |
|---|---|
| `title.rendered` | Event name (HTML entities escaped) |
| `Start Date (YYYY-mm-dd)` | Despite its name, a **Unix timestamp** string. Convert it to a date |
| `End Date (YYYY-mm-dd)` | Same format |
| `Location` | Free text, for example "Rochester, NY, USA" |
| `Virtual event only` | Blank means in person. Any value means online only |
| `_venue_city`, `_venue_state`, `_venue_country_code`, `_venue_country_name` | Structured venue location. The country code is ISO two-letter, uppercase, for example `US` |
| `Venue Name`, `Physical Address` | Venue |
| `Number of Anticipated Attendees` | The organizers' estimate, not actual attendance |
| `URL` | The event's own site |
| `link` | Its Central page |
| `status` | `wcpt-closed`, `wcpt-scheduled` or `wcpt-cancelled` |

Event type isn't a field. It comes from the title: "WordCamp US/Europe/Asia" are flagships, "Campus Connect", "WordPress Day", "Women WordPress Day", everything else with "WordCamp" is a local WordCamp, and the rest are other community events.

## 3. WordPress.org Events API (upcoming events near a place)

The WordPress.org Events API lists upcoming events near a location:
`https://api.wordpress.org/events/1.0/?location=Austin`, or `?latitude=..&longitude=..` for a point. It returns a few upcoming meetups and WordCamps near that place, and can return none. An event whose location starts with "Online" is online. It doesn't cover past events.
