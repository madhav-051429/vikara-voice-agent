import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')


def get_calendar_service():
    """Builds and returns the Google Calendar API client."""
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

    if os.path.exists(creds_path):
        # local dev — use the JSON file directly
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    else:
        # deployed (Railway) — credentials stored as env var
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            raise Exception("No Google credentials found. Set GOOGLE_CREDENTIALS_JSON or place credentials.json")
        creds_info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

    return build('calendar', 'v3', credentials=creds)


def parse_date(date_str):
    """Try common date formats, fall back to dateutil."""
    formats = ['%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%d/%m/%Y', '%m/%d/%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    # fallback
    from dateutil import parser
    return parser.parse(date_str)


def parse_time(time_str):
    """Try common time formats, fall back to dateutil."""
    formats = ['%H:%M', '%I:%M %p', '%I:%M%p', '%I %p', '%I%p']
    for fmt in formats:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except ValueError:
            continue
    from dateutil import parser
    return parser.parse(time_str)


def create_event(name: str, date: str, time: str, title: str = None) -> dict:
    """
    Creates a Google Calendar event.
    Returns a dict with success status, event details, or error message.
    """
    service = get_calendar_service()

    try:
        parsed_date = parse_date(date)
        parsed_time = parse_time(time)

        start = parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)
        end = start + timedelta(hours=1)
    except Exception as e:
        return {"success": False, "error": f"Couldn't parse date/time: {e}"}

    meeting_title = title if title else f"Meeting with {name}"

    event_body = {
        'summary': meeting_title,
        'description': f'Scheduled by {name} via Voice Agent',
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {'useDefault': True},
    }

    # check if the slot is already taken
    try:
        freebusy = service.freebusy().query(body={
            'timeMin': start.isoformat() + '+05:30',
            'timeMax': end.isoformat() + '+05:30',
            'items': [{'id': CALENDAR_ID}]
        }).execute()

        busy = freebusy.get('calendars', {}).get(CALENDAR_ID, {}).get('busy', [])
        if busy:
            return {"success": False, "error": "That time slot is already booked. Please choose a different time."}
    except Exception as e:
        logger.warning(f"FreeBusy check failed (proceeding anyway): {e}")

    # create the event
    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event_body).execute()
        return {
            "success": True,
            "event_id": event['id'],
            "event_link": event.get('htmlLink', ''),
            "summary": event['summary'],
            "start": event['start']['dateTime'],
            "end": event['end']['dateTime'],
            "message": f"Created '{meeting_title}' on {start.strftime('%B %d, %Y at %I:%M %p')}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
