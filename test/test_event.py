import json
from datetime import datetime, timedelta

# your events list here
f = open('test.json',)

events =  json.load(f)

def extract_all_dates(events):
    dates = set()

    for ev in events:
        s = ev.get('start', {})
        e = ev.get('end', {})

        # Determine if this is an all-day event or a timed event
        if 'date' in s and 'date' in e:
            # all-day: end.date is exclusive
            start_date = datetime.fromisoformat(s['date']).date()
            end_date   = datetime.fromisoformat(e['date']).date()
            exclusive  = True
        elif 'dateTime' in s and 'dateTime' in e:
            # timed: include the end date if it differs
            start_date = datetime.fromisoformat(s['dateTime']).date()
            end_date   = datetime.fromisoformat(e['dateTime']).date()
            exclusive  = False
        else:
            # skip events without a clear start/end
            continue

        # iterate dates
        cur = start_date
        if exclusive:
            while cur < end_date:
                dates.add(cur)
                cur += timedelta(days=1)
        else:
            # inclusive of end_date
            while cur <= end_date:
                dates.add(cur)
                cur += timedelta(days=1)

    # return a sorted list
    return sorted(dates)

from datetime import datetime, timezone
from typing import List, Dict

def get_first_n_upcoming_events(events: List[Dict], n: int = 5) -> List[Dict]:
    """
    Return the first `n` upcoming events based on the current UTC time.
    
    Args:
        events: List of event dictionaries (as from Google Calendar API).
        n: Number of upcoming events to return (default 5).
        
    Returns:
        A list of up to `n` event dicts that start on or after now.
    """
    now = datetime.now(timezone.utc)
    upcoming = []
    
    for ev in events:
        start = ev.get('start', {})
        dt = None
        
        # parse dateTime (timed events) or date (all-day)
        if 'dateTime' in start:
            dt_parsed = datetime.fromisoformat(start['dateTime'])
            # ensure UTC
            dt = dt_parsed.astimezone(timezone.utc)
        elif 'date' in start:
            # treat all-day as start of the day UTC
            dt_parsed = datetime.fromisoformat(start['date'])
            dt = datetime(dt_parsed.year, dt_parsed.month, dt_parsed.day, tzinfo=timezone.utc)
        
        if dt and dt >= now:
            upcoming.append((dt, ev))
    
    # sort by start datetime and return first n events
    upcoming.sort(key=lambda x: x[0])
    return [ev for _, ev in upcoming[:n]]


# Example usage:
all_dates = extract_all_dates(events)
first_5 = get_first_n_upcoming_events(events, 5)
print([e["summary"] for e in first_5])
# print(all_dates)
#print(type(all_dates[0]))
