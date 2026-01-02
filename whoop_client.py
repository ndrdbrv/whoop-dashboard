"""WHOOP API Client - handles OAuth and all API calls"""

import os
import json
import webbrowser
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests
from flask import Flask, request

BASE_URL = "https://api.prod.whoop.com/developer"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

SCOPES = [
    "read:recovery",
    "read:cycles", 
    "read:workout",
    "read:sleep",
    "read:profile",
    "read:body_measurement"
]


class WhoopClient:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self._load_tokens()

    def _load_tokens(self):
        """Load saved tokens if they exist"""
        try:
            with open(".whoop_tokens.json", "r") as f:
                data = json.load(f)
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.token_expiry = datetime.fromisoformat(data["expiry"]) if data.get("expiry") else None
        except FileNotFoundError:
            pass

    def _save_tokens(self):
        """Persist tokens to disk"""
        with open(".whoop_tokens.json", "w") as f:
            json.dump({
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expiry": self.token_expiry.isoformat() if self.token_expiry else None
            }, f)

    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": "whoop_training"
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str):
        """Exchange authorization code for access token"""
        resp = requests.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        resp.raise_for_status()
        data = resp.json()
        
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 3600))
        self._save_tokens()

    def _refresh_if_needed(self):
        """Refresh token if expired"""
        if self.token_expiry and datetime.now() >= self.token_expiry and self.refresh_token:
            resp = requests.post(TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            resp.raise_for_status()
            data = resp.json()
            self.access_token = data["access_token"]
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            self.token_expiry = datetime.now() + timedelta(seconds=data.get("expires_in", 3600))
            self._save_tokens()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make authenticated GET request"""
        self._refresh_if_needed()
        headers = {"Authorization": f"Bearer {self.access_token}"}
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def _get_all_pages(self, endpoint: str, params: dict = None, limit: int = 25) -> list:
        """Fetch all pages of a paginated endpoint"""
        params = params or {}
        params["limit"] = limit
        all_records = []
        
        while True:
            data = self._get(endpoint, params)
            records = data.get("records", [])
            all_records.extend(records)
            
            next_token = data.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token
        
        return all_records

    # ─── User Endpoints ───────────────────────────────────────────────────────
    
    def get_profile(self) -> dict:
        """Get basic user profile (name, email)"""
        return self._get("/v2/user/profile/basic")

    def get_body_measurements(self) -> dict:
        """Get height, weight, max heart rate"""
        return self._get("/v2/user/measurement/body")

    # ─── Recovery Endpoints ───────────────────────────────────────────────────
    
    def get_recovery(self, start: datetime = None, end: datetime = None, limit: int = 10) -> list:
        """Get recovery records"""
        params = {"limit": limit}
        if start:
            params["start"] = start.isoformat() + "Z"
        if end:
            params["end"] = end.isoformat() + "Z"
        return self._get("/v2/recovery", params).get("records", [])

    def get_latest_recovery(self) -> dict:
        """Get the most recent recovery score"""
        records = self.get_recovery(limit=1)
        return records[0] if records else None

    # ─── Cycle Endpoints ──────────────────────────────────────────────────────
    
    def get_cycles(self, start: datetime = None, end: datetime = None, limit: int = 10) -> list:
        """Get physiological cycles (daily strain)"""
        params = {"limit": limit}
        if start:
            params["start"] = start.isoformat() + "Z"
        if end:
            params["end"] = end.isoformat() + "Z"
        return self._get("/v2/cycle", params).get("records", [])

    # ─── Sleep Endpoints ──────────────────────────────────────────────────────
    
    def get_sleep(self, start: datetime = None, end: datetime = None, limit: int = 10) -> list:
        """Get sleep records"""
        params = {"limit": limit}
        if start:
            params["start"] = start.isoformat() + "Z"
        if end:
            params["end"] = end.isoformat() + "Z"
        return self._get("/v2/activity/sleep", params).get("records", [])

    def get_latest_sleep(self) -> dict:
        """Get the most recent sleep"""
        records = self.get_sleep(limit=1)
        return records[0] if records else None

    # ─── Workout Endpoints ────────────────────────────────────────────────────
    
    def get_workouts(self, start: datetime = None, end: datetime = None, limit: int = 25) -> list:
        """Get workout records"""
        params = {"limit": limit}
        if start:
            params["start"] = start.isoformat() + "Z"
        if end:
            params["end"] = end.isoformat() + "Z"
        return self._get("/v2/activity/workout", params).get("records", [])

    def get_recent_workouts(self, days: int = 7) -> list:
        """Get workouts from last N days"""
        start = datetime.now() - timedelta(days=days)
        return self.get_workouts(start=start, limit=25)


def authenticate(client_id: str, client_secret: str, redirect_uri: str) -> WhoopClient:
    """Run OAuth flow and return authenticated client"""
    client = WhoopClient(client_id, client_secret, redirect_uri)
    
    # Check if we already have valid tokens
    if client.access_token:
        try:
            client.get_profile()  # Test the token
            print("✓ Using saved authentication")
            return client
        except:
            pass  # Token expired or invalid, need to re-auth
    
    # Start OAuth flow
    app = Flask(__name__)
    auth_code = {"code": None}
    
    @app.route("/callback")
    def callback():
        auth_code["code"] = request.args.get("code")
        return "<h1>Authentication successful!</h1><p>You can close this window.</p>"
    
    print(f"\n→ Opening browser for WHOOP authorization...")
    webbrowser.open(client.get_auth_url())
    
    # Run Flask server to catch the callback
    import threading
    server = threading.Thread(target=lambda: app.run(port=8080, debug=False, use_reloader=False))
    server.daemon = True
    server.start()
    
    # Wait for the callback
    print("Waiting for authorization...")
    while not auth_code["code"]:
        pass
    
    client.exchange_code(auth_code["code"])
    print("✓ Authentication complete!")
    return client

