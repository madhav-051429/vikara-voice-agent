import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

def get_calendar_service():
    """Create and return a Google Calendar API service instance."""
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')

    # Support both file path and JSON string (for deployment)
    if os.path.exists(creds_path):
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES
        )
    else:
        # If credentials are stored as env variable (for Railway deployment)
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            creds_info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_info, scopes=SCOPES
            )
        else:
            raise Exception("No Google credentials found")

    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_event(name: str, date: str, time: str, title: str = None) -> dict:
    """
    Create a Google Calendar event.

    Args:
        name: Name of the person scheduling
        date: Date string (e.g., "2026-03-05" or "March 5, 2026")
        time: Time string (e.g., "14:00" or "2:00 PM")
        title: Optional meeting title

    Returns:
        dict with event details and link
    """
    service = get_calendar_service()

    # Parse the date and time
    try:
        # Try multiple date formats
        for fmt in ['%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                parsed_date = datetime.strptime(date.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            # If no format matched, try a more flexible approach
            from dateutil import parser
            parsed_date = parser.parse(date)

        # Parse time
        for fmt in ['%H:%M', '%I:%M %p', '%I:%M%p', '%I %p', '%I%p']:
            try:
                parsed_time = datetime.strptime(time.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            from dateutil import parser
            parsed_time = parser.parse(time)

        # Combine date and time
        event_start = parsed_date.replace(
            hour=parsed_time.hour,
            minute=parsed_time.minute
        )
        event_end = event_start + timedelta(hours=1)  # 1 hour default duration

    except Exception as e:
        return {"success": False, "error": f"Could not parse date/time: {str(e)}"}

    # Build the event
    meeting_title = title if title else f"Meeting with {name}"
    event = {
        'summary': meeting_title,
        'description': f'Meeting scheduled by {name} via Vikara Voice Agent',
        'start': {
            'dateTime': event_start.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': event_end.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'attendees': [],
        'reminders': {
            'useDefault': True,
        },
    }

    try:
        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()

        return {
            "success": True,
            "event_id": created_event['id'],
            "event_link": created_event.get('htmlLink', ''),
            "summary": created_event['summary'],
            "start": created_event['start']['dateTime'],
            "end": created_event['end']['dateTime'],
            "message": f"Successfully created '{meeting_title}' on {event_start.strftime('%B %d, %Y at %I:%M %p')}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
