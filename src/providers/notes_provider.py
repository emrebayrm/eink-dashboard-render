from .events_provider import EventsProvider
from datetime import datetime, timezone
from typing import List, Dict


def get_formatted_dt_from_event(ev, key):
    not_parsed_key = ev.get(key, {})
    dt = None
    
    # parse dateTime (timed events) or date (all-day)
    if 'dateTime' in not_parsed_key:
        dt_parsed = datetime.fromisoformat(not_parsed_key['dateTime'])
        # ensure UTC
        dt = dt_parsed.astimezone(timezone.utc)
    elif 'date' in not_parsed_key:
        # treat all-day as start of the day UTC
        dt_parsed = datetime.fromisoformat(not_parsed_key['date'])
        dt = datetime(dt_parsed.year, dt_parsed.month, dt_parsed.day, tzinfo=timezone.utc)

    return dt
class NotesProvider:
    def __init__(self, event_provider : EventsProvider ):
        self.event_provider = event_provider

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
            dt = get_formatted_dt_from_event(ev, "start")           
            if dt and dt >= now:
                upcoming.append((dt, ev))
        
        # sort by start datetime and return first n events
        upcoming.sort(key=lambda x: x[0])
        return [ev for _, ev in upcoming[:n]]

    def get_notes_markdown(self):
        events_return_text = "## Upcoming Events\n"
        events = self.event_provider.get_events()
        first_5 = NotesProvider.get_first_n_upcoming_events(events)
        for ev in first_5:
            start = get_formatted_dt_from_event(ev, "start")
            end = get_formatted_dt_from_event(ev, "end")

            events_return_text += f"-  {ev["summary"]} \n"
            events_return_text += f"\n   {start.strftime("%-d %b")} / {end.strftime("%-d %b")} \n"
        return events_return_text
