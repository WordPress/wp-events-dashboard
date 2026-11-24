# Recipes

Each recipe gives the helper command, then the route without code.

## Which US meetup groups met in person in the last 6 to 8 months?

```
python3 scripts/wpcd.py meetups --country USA --months 8 --in-person
python3 scripts/wpcd.py meetups --country USA --months 6 --in-person --format json
```

The first command gives the list. The second gives the count for the lower bound in its `count` field.

Without code: fetch the dashboard JSON. Keep the `meetups.allGroups` entries where `country` is `USA` and `lastInPerson` is on or after today minus 8 months.

Answer shape: a table of group, city, last in-person date, and link. Add a one-line count such as "41 of 152 US groups", the "as of" date, and any caveat that applies.

## Which communities held in-person WordCamps between 2022 and 2026?

```
python3 scripts/wpcd.py wordcamps --country US --from 2022 --to 2026 --in-person --by-community
```

Without code: page through the Central API. Keep events whose start timestamp falls in 2022 to 2026, whose `_venue_country_code` is `US`, whose `Virtual event only` is blank, and whose title contains "WordCamp". Group them by city.

The helper lists local communities first and flagships after them, marked in the `kind` column. WordCamp US moves to a new city each year, so report the flagships as a separate group. Say that the current year can include upcoming (`scheduled`) events, and that events still in planning aren't listed.

## Is a specific group still active? Who runs it?

```
python3 scripts/wpcd.py meetups --group austin --organizers
```

`--group` matches part of a group name or city, and it finds the group however long ago it met. Report `status`, `last_any`, `last_in_person`, the organizers, and the link.

Without code: find the group in `meetups.allGroups` by `group` or `city`. Report `cat`, `last`, `lastInPerson`, the `n` value of each entry in `leaders`, and `url`.

## Which big groups went quiet?

```
python3 scripts/wpcd.py meetups --country USA --status Inactive
```

Rows come sorted by members, largest first.

Without code: use `meetups.deadBig`, or filter `meetups.allGroups` for `cat` equal to `Inactive` and sort by `members`.

## What WordCamps are coming up?

```
python3 scripts/wpcd.py wordcamps --upcoming --all-types --country Canada
```

Drop `--country` for every country. Drop `--all-types` for WordCamps only.

Without code: fetch the Central API with `&status=wcpt-scheduled`, and keep events whose start date is today or later.

## What meetups are coming up near a place?

The helper doesn't cover this. Fetch `https://api.wordpress.org/events/1.0/?location=Austin`, with the place name in place of Austin. It returns a few upcoming meetups and WordCamps near that place, or none. `references/sources.md` section 3 has the details.

## Hand it to a spreadsheet

Add `--format csv > answer.csv` to any helper command. The person can open the file in Google Sheets or Numbers.
