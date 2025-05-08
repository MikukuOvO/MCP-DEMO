"""FastMCP server exposing advanced Google Calendar tools.

Features
--------
* Search events across one or many calendars with rich text query.
* Filter by time window (``time_min`` / ``time_max`` in ISO‑8601).
* Optional pagination (``nextPageToken``).
* Optionally return full event description.
* Retrieve a single event with all details decoded.
* Minimal error handling & token/scopes configurable via env vars.
* Structured JSON outputs optimised for LLMs / agents.

Notes
-----
* The server is **read‑only** by default (scope ``calendar.readonly``).
  To enable creation or edits, set the ``CALENDAR_SCOPES`` env‑var to a
  write scope, e.g. ``https://www.googleapis.com/auth/calendar`` and add
  tools below.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCOPES = os.getenv(
    "CALENDAR_SCOPES",
    "https://www.googleapis.com/auth/calendar.readonly",
).split(",")
TOKEN_FILE = os.getenv("CALENDAR_TOKEN_PATH", "token.json")
DEFAULT_CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")


# ---------------------------------------------------------------------------
# Calendar service factory
# ---------------------------------------------------------------------------

def get_calendar_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


cal = get_calendar_service()

# FastMCP server instance ----------------------------------------------------
mcp = FastMCP("calendar-tools-advanced")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event_summary(evt: dict) -> dict:
    return {
        "id": evt.get("id"),
        "calendarId": evt.get("organizer", {}).get("email", DEFAULT_CALENDAR_ID),
        "summary": evt.get("summary", "(no title)"),
        "start": evt.get("start", {}).get("dateTime", evt.get("start", {}).get("date")),
        "end": evt.get("end", {}).get("dateTime", evt.get("end", {}).get("date")),
        "location": evt.get("location", ""),
    }


def _iso(dt: datetime | str | None) -> str | None:
    """Return ISO‑8601 string in UTC or None."""
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Exposed tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="calendar_search_events",
    description=(
        "Search Google Calendar events. Supports text query over summary, "
        "description and location. Filter by ISO‑8601 time window with "
        "``time_min`` / ``time_max``. Pagination via ``page_token``. Set "
        "``include_description=True`` to include event descriptions."
    ),
)

def calendar_search_events(
    query: str = "",  # empty string = no text filter
    time_min: Optional[str | datetime] = None,
    time_max: Optional[str | datetime] = None,
    max_results: int = 10,
    include_description: bool = False,
    page_token: Optional[str] = None,
    calendar_id: str = DEFAULT_CALENDAR_ID,
) -> dict:
    """Return list of events plus nextPageToken if more."""
    params = {
        "calendarId": calendar_id,
        "q": query or None,
        "maxResults": max_results,
        "pageToken": page_token,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min := _iso(time_min):
        params["timeMin"] = time_min
    if time_max := _iso(time_max):
        params["timeMax"] = time_max

    try:
        res = cal.events().list(**{k: v for k, v in params.items() if v is not None}).execute()
    except HttpError as e:
        return {"error": str(e)}

    events_out: List[Dict[str, str]] = []
    for evt in res.get("items", []):
        item = _event_summary(evt)
        if include_description:
            item["description"] = evt.get("description", "")
        events_out.append(item)

    return {
        "events": events_out,
        "nextPageToken": res.get("nextPageToken"),
    }


@mcp.tool(
    name="calendar_get_event",
    description="Retrieve full Google Calendar event metadata including description.",
)

def calendar_get_event(event_id: str, calendar_id: str = DEFAULT_CALENDAR_ID) -> dict:
    try:
        evt = cal.events().get(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as e:
        return {"error": str(e)}

    info = _event_summary(evt)
    info.update(
        {
            "description": evt.get("description", ""),
            "attendees": [a.get("email") for a in evt.get("attendees", []) if a.get("email")],
            "hangoutLink": evt.get("hangoutLink", ""),
        }
    )
    return info


# ---------------------------------------------------------------------------
# CLI entry‑point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
