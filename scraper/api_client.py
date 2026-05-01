"""Authenticated client for the OpenCaselist API."""

import sys
import time
import requests
from config.settings import OPENCASELIST_API_BASE, SCRAPE_DELAY_SECONDS


class CaselistAPIClient:
    def __init__(self, cookie: str = None):
        """Initialize the API client.

        Args:
            cookie: The caselist_token cookie value from a Tabroom login session.
            Required for downloading documents.
        """
        self.base_url = OPENCASELIST_API_BASE
        self.session = requests.Session()
        if cookie:
            self.session.cookies.set("caselist_token", cookie)
        self.delay = SCRAPE_DELAY_SECONDS

    def _get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a rate-limited GET request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, **kwargs)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            print(f"\nRate limited. Waiting {retry_after}s...", file=sys.stderr, flush=True)
            time.sleep(retry_after)
            response = self.session.get(url, **kwargs)

        response.raise_for_status()
        time.sleep(self.delay)
        return response

    def get_caselists(self) -> list[dict]:
        """Get all available caselists."""
        return self._get("/caselists").json()

    def get_schools(self, caselist: str) -> list[dict]:
        """Get all schools in a caselist."""
        return self._get(f"/caselists/{caselist}/schools").json()

    def get_teams(self, caselist: str, school: str) -> list[dict]:
        """Get all teams for a school."""
        return self._get(f"/caselists/{caselist}/schools/{school}/teams").json()

    def get_rounds(self, caselist: str, school: str, team: str) -> list[dict]:
        """Get all rounds for a team."""
        return self._get(f"/caselists/{caselist}/schools/{school}/teams/{team}/rounds").json()

    def get_recent(self, caselist: str) -> list[dict]:
        """Get recently updated rounds for a caselist.

        Returns a list of dicts with round_id, team info, tournament,
        side, opensource path, etc. Sorted by most recently updated.
        """
        return self._get(f"/caselists/{caselist}/recent").json()

    def get_bulk_downloads(self, caselist: str) -> list[dict]:
        """Get direct download URLs for all files in a caselist.

        Returns a list of dicts with 'name' and 'url' keys.
        Much faster than crawling schools/teams/rounds individually.
        """
        return self._get(f"/caselists/{caselist}/downloads").json()

    def download_document(self, file_path: str) -> bytes:
        """Download a Word document by its file path."""
        response = self._get("/download", params={"path": file_path})
        return response.content
