import datetime
import os
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# This scope allows read/write access to calendars
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _load_dotenv(dotenv_path: Path):
  """A tiny dotenv loader: reads KEY=VALUE lines and sets os.environ if not set."""
  if not dotenv_path or not dotenv_path.exists():
    return
  with dotenv_path.open() as f:
    for raw in f:
      line = raw.strip()
      if not line or line.startswith("#"):
        continue
      if "=" not in line:
        continue
      key, val = line.split("=", 1)
      key = key.strip()
      val = val.strip().strip('"').strip("'")
      # Only set if not already in environment
      os.environ.setdefault(key, val)


def _build_client_config_from_env():
  """Return a client config dict for google-auth from environment variables.

  Expects at least OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET. Redirect URIs
  may be provided as JSON array or comma-separated list in OAUTH_REDIRECT_URIS.
  """
  client_id = os.environ.get("OAUTH_CLIENT_ID")
  client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
  if not client_id or not client_secret:
    return None

  # parse redirect URIs
  ru_env = os.environ.get("OAUTH_REDIRECT_URIS")
  redirect_uris = ["http://localhost"]
  if ru_env:
    try:
      redirect_uris = json.loads(ru_env)
      if not isinstance(redirect_uris, list):
        redirect_uris = [str(redirect_uris)]
    except Exception:
      # fallback to comma-separated
      redirect_uris = [u.strip() for u in ru_env.split(",") if u.strip()]

  auth_uri = os.environ.get(
    "OAUTH_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"
  )
  token_uri = os.environ.get(
    "OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token"
  )
  provider_url = os.environ.get(
    "OAUTH_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"
  )

  return {
    "installed": {
      "client_id": client_id,
      "project_id": os.environ.get("OAUTH_PROJECT_ID"),
      "auth_uri": auth_uri,
      "token_uri": token_uri,
      "auth_provider_x509_cert_url": provider_url,
      "client_secret": client_secret,
      "redirect_uris": redirect_uris,
    }
  }


def main():
  """Shows basic usage of the Google Calendar API.
  Creates an event on the user's primary calendar.
  """
  creds = None
  base_dir = Path(__file__).resolve().parent

  # Load .env in the same directory as this file if present
  dotenv_path = base_dir / ".env"
  _load_dotenv(dotenv_path)

  # token.json path absolute to this module's directory
  token_path = base_dir / "token.json"
  if token_path.exists():
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      # Prefer environment-based client config (from .env). Fall back to
      # credentials.json file if present for compatibility.
      credentials_file = base_dir / "credentials.json"
      client_config = _build_client_config_from_env()
      if client_config:
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
      elif credentials_file.exists():
        flow = InstalledAppFlow.from_client_secrets_file(
          str(credentials_file), SCOPES
        )
      else:
        raise RuntimeError(
          "No OAuth client configuration found. Put credentials in .env or provide credentials.json."
        )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with token_path.open("w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    start_time = datetime.datetime.now() + datetime.timedelta(days=1)
    end_time = start_time + datetime.timedelta(hours=1)

    event = {
      "summary": "My API Event",
      "location": "123 Main St, Anytown, USA",
      "description": "This is a test event created by the Google Calendar API.",
      "start": {
        "dateTime": start_time.isoformat() + "Z",  # 'Z' indicates UTC time
        "timeZone": "UTC",
      },
      "end": {
        "dateTime": end_time.isoformat() + "Z",
        "timeZone": "UTC",
      },
      # You can also add attendees
      # "attendees": [
      #     {"email": "friend1@example.com"},
      #     {"email": "friend2@example.com"},
      # ],
      "reminders": {
        "useDefault": False,
        "overrides": [
          {"method": "email", "minutes": 24 * 60},  # 1 day before
          {"method": "popup", "minutes": 10},  # 10 minutes before
        ],
      },
    }

    # Call the Calendar API to insert the event
    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()