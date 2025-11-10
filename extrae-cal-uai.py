# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "camelot-py",
#   "matplotlib"
# ]
# ///

import sys
import re
import camelot
import datetime
from collections import defaultdict
import csv
import hashlib
import matplotlib.pyplot as plt

def main() -> None:

    original_file = sys.argv[1]

    print("Hello from extrae-cal-uai.py!")
    print(f"Parsing {original_file}")
    tables = camelot.read_pdf(original_file, 
                              strip_text='\n', 
                              pages='all', 
                              line_scale=100, 
                              copy_text=['h'])
    
    print(f"Found {len(tables)} tables")
    print(tables[0].df)
    
    #camelot.plot(tables[0], kind='grid')
    #plt.show()
    
    #exit(0)
    
    # Initialize events list; first row (headers) and first column (week labels) will be skipped later
    events = []

    date_pat = re.compile(
        r'^\s*(\d{1,2})\s*[-‐‑—–./]?\s*(ene|feb|mar|abr|may|jun|jul|ago|sep|set|sept|oct|nov|dic)\.?\s*$',
        re.IGNORECASE,
    )

    def is_date_cell(text: str) -> bool:
        if text is None:
            return False
        s = str(text).strip()
        if not s or s.lower() in {"nan", "none"}:
            return False
        return bool(date_pat.match(s))

    def clean_text(text: str) -> str:
        if text is None:
            return ""
        s = str(text)
        if s.lower() in {"nan", "none"}:
            return ""
        return re.sub(r"\s+", " ", s).strip()

    for t_idx, table in enumerate(tables):
        df = table.df
        rows, cols = df.shape

        for c in range(1, cols):
            r = 1  # ignore first row
            while r < rows:
                cell = clean_text(df.iat[r, c])
                print(f"Table {t_idx}, Row {r}, Col {c}: '{cell}', is_date_cell: {is_date_cell(cell)}")
                if is_date_cell(cell):
                    k = r + 1
                    collected = 0
                    while k < rows:
                        below = clean_text(df.iat[k, c])
                        if is_date_cell(below):
                            break
                        if below:
                            tags = []
                            for tag in ["B1", "B2", "B3", "B4", "S1", "S2"]:
                                if tag in below:
                                    tags.append(tag)
                            for part in re.split(r"[\n•]+", below):
                                part = clean_text(part)
                                if part:
                                    events.append({"date": cell, "event": part, "table": t_idx, "tags": tags})
                                    collected += 1
                        elif collected > 0:
                            break
                        k += 1
                    r = k
                else:
                    r += 1


    print(f"Extracted {len(events)} events")
    for e in events:
        print(f"{e['date']}: {e['event']}, (table {e['table']}), tags: {e['tags']}")

    
    # Export to ICS file, merging repeated continuous days into single all-day events

    # Helper: parse "DD MMM" to a date object with inferred year
    month_map = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'set': 9, 'sept': 9, 'oct': 10,
        'nov': 11, 'dic': 12
    }

    def parse_event_date(e):
        m = date_pat.match(e['date'])
        if not m:
            return None
        day = int(m.group(1))
        mon_abbr = m.group(2).lower()
        month = month_map.get(mon_abbr)
        if not month:
            return None
        current_year = datetime.datetime.now().year
        if month == 12 and e['table'] == 0:
            current_year -= 1
        elif month == 1 and e['table'] > 1:
            current_year += 1
        try:
            return datetime.date(current_year, month, day)
        except ValueError:
            return None

    def ics_escape(s: str) -> str:
        return (
            str(s)
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )

    def make_uid(summary: str, start: datetime.date, end: datetime.date) -> str:
        raw = f"{summary}|{start.isoformat()}|{end.isoformat()}".encode("utf-8")
        return hashlib.md5(raw).hexdigest() + "@extrae-cal-uai"

    # Group by normalized title; collect dates and tags per date
    grouped = {}
    for e in events:
        d = parse_event_date(e)
        if not d:
            continue
        title_orig = e['event'].strip()
        title_norm = re.sub(r"\s+", " ", title_orig).strip().lower()
        if title_norm not in grouped:
            grouped[title_norm] = {
                "dates": set(),
                "titles_by_date": {},
                "tags_by_date": defaultdict(set),
            }
        grouped[title_norm]["dates"].add(d)
        grouped[title_norm]["titles_by_date"][d] = title_orig
        for tag in e['tags']:
            grouped[title_norm]["tags_by_date"][d].add(tag)

    # Build ICS
    lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//extrae-cal-uai//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    total_vevents = 0
    for _, data in grouped.items():
        if not data["dates"]:
            continue
        sorted_dates = sorted(data["dates"])

        run = [sorted_dates[0]]
        for d in sorted_dates[1:]:
            if d == run[-1] + datetime.timedelta(days=1):
                run.append(d)
            else:
                # flush current run
                start = run[0]
                end = run[-1]
                summary = data["titles_by_date"].get(start, next(iter(data["titles_by_date"].values())))
                cats = set()
                for rd in run:
                    cats.update(data["tags_by_date"].get(rd, set()))
                lines.append("BEGIN:VEVENT")
                lines.append(f"UID:{make_uid(summary, start, end)}")
                lines.append(f"DTSTAMP:{dtstamp}")
                lines.append(f"SUMMARY:{ics_escape(summary)}")
                if cats:
                    lines.append(f"CATEGORIES:{','.join(sorted(cats))}")
                lines.append(f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}")
                lines.append(f"DTEND;VALUE=DATE:{(end + datetime.timedelta(days=1)).strftime('%Y%m%d')}")
                lines.append("END:VEVENT")
                total_vevents += 1
                run = [d]

        # flush last run
        if run:
            start = run[0]
            end = run[-1]
            summary = data["titles_by_date"].get(start, next(iter(data["titles_by_date"].values())))
            cats = set()
            for rd in run:
                cats.update(data["tags_by_date"].get(rd, set()))
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{make_uid(summary, start, end)}")
            lines.append(f"DTSTAMP:{dtstamp}")
            lines.append(f"SUMMARY:{ics_escape(summary)}")
            if cats:
                lines.append(f"CATEGORIES:{','.join(sorted(cats))}")
            lines.append(f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{(end + datetime.timedelta(days=1)).strftime('%Y%m%d')}")
            lines.append("END:VEVENT")
            total_vevents += 1

    lines.append("END:VCALENDAR")

    # Write ICS file
    output_file = original_file.replace(".pdf", "_events.ics")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")

    print(f"Events exported to {output_file} ({total_vevents} vevents)")
    

if __name__ == "__main__":
    main()
