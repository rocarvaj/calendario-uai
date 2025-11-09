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

    
    # Prepare data for CSV export
    csv_data = []
    for e in events:
        # Parse date (format: "DD MMM" or similar)
        date_match = date_pat.match(e['date'])
        if date_match:
            day = date_match.group(1).zfill(2)
            month_abbr = date_match.group(2).lower()
            
            # Map Spanish month abbreviations to numbers
            month_map = {
                'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
                'sep': '09', 'set': '09', 'sept': '09', 'oct': '10',
                'nov': '11', 'dic': '12'
            }
            month = month_map.get(month_abbr, '01')
            
            # Assume current or next year
            current_year = datetime.datetime.now().year
            if month == '12' and e['table'] == 0:
                current_year -= 1
            elif month == '01' and e['table'] > 1:
                current_year += 1
            formatted_date = f"{current_year}-{month}-{day}"
        else:
            formatted_date = e['date']
        
        category = ','.join(e['tags']) if e['tags'] else ''
        page = e['table']
        
        csv_data.append({
            'date': formatted_date,
            'title': e['event'],
            'category': category,
            'page': page
        })

    # Write to CSV file
    output_file = original_file.replace('.pdf', '_events.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'title', 'category', 'page']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"Events exported to {output_file}")
    

if __name__ == "__main__":
    main()
