import pickle
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

CREDENTIALS_FILE = os.getenv("GOOGLE_CALENDAR_CREDENTIAL_FILE")
SECRET_FOLDER = os.getenv("SECRET_FOLDER")

def get_calendar_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(SECRET_FOLDER + 'token.pickle'):
        with open(SECRET_FOLDER + 'token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(SECRET_FOLDER + 'token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

class EventsProvider:
    def __init__(self):
        self._cached_events = []
        
    def _get_list_of_calendars(self, service):
        print('Getting list of calendars')
        calendars_result = service.calendarList().list().execute()

        calendars = calendars_result.get('items', [])
        calendar_ids = [] 
        if not calendars:
            print('No calendars found.')
        for calendar in calendars:
            summary = calendar['summary']
            id = calendar['id']
            calendar_ids.append(id)
            primary = "Primary" if calendar.get('primary') else ""

            print("%s\t%s\t%s" % (summary, id, primary))

        return calendar_ids
    
    def _get_this_month_events(self, service, calendar_id):
        if len(self._cached_events) > 0:
            return self._cached_events
        
        # 1) Compute UTC bounds for “this month”
        now = datetime.datetime.utcnow()
        start_of_month = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        # roll over into next month
        if now.month == 12:
            start_of_next = datetime.datetime(now.year+1, 1, 1, 0, 0, 0)
        else:
            start_of_next = datetime.datetime(now.year, now.month+1, 1, 0, 0, 0)

        timeMin = start_of_month.isoformat() + "Z"   # e.g. "2025-05-01T00:00:00Z"
        timeMax = start_of_next.isoformat() + "Z"    # e.g. "2025-06-01T00:00:00Z"

        print(f"Getting events from {timeMin} to {timeMax}")
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            print('No events found this month.')
        else:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event.get('summary', '(no title)'))

        return events
    
    def extract_all_dates(events):
        dates = set()

        for ev in events:
            s = ev.get('start', {})
            e = ev.get('end', {})

            # Determine if this is an all-day event or a timed event
            if 'date' in s and 'date' in e:
                # all-day: end.date is exclusive
                start_date = datetime.datetime.fromisoformat(s['date']).date()
                end_date   = datetime.datetime.fromisoformat(e['date']).date()
                exclusive  = True
            elif 'dateTime' in s and 'dateTime' in e:
                # timed: include the end date if it differs
                start_date = datetime.datetime.fromisoformat(s['dateTime']).date()
                end_date   = datetime.datetime.fromisoformat(e['dateTime']).date()
                exclusive  = False
            else:
                # skip events without a clear start/end
                continue

            # iterate dates
            cur = start_date
            if exclusive:
                while cur < end_date:
                    dates.add(cur)
                    cur += datetime.timedelta(days=1)
            else:
                # inclusive of end_date
                while cur <= end_date:
                    dates.add(cur)
                    cur += datetime.timedelta(days=1)

        # return a sorted list
        return sorted(dates)
    
    def get_events(self):
        service = get_calendar_service()
        calendars = self._get_list_of_calendars(service)
        
        events = []
        for calendar in calendars:
            event = self._get_this_month_events(service, calendar)
            if event is not None:
                events.extend(event)
        print("#######################")
        print(json.dumps(events, indent=2, ensure_ascii=False))
        return events
