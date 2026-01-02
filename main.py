#!/usr/bin/env python3
"""WHOOP Training Planner - CLI for climbing, running, gym, sauna"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

from whoop_client import WhoopClient, authenticate
from training_planner import TrainingPlanner, print_recommendation


def main():
    load_dotenv()
    
    client_id = os.getenv("WHOOP_CLIENT_ID")
    client_secret = os.getenv("WHOOP_CLIENT_SECRET")
    redirect_uri = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback")
    
    if not client_id or not client_secret:
        print("❌ Missing credentials!")
        print("\n1. Go to https://developer.whoop.com")
        print("2. Create an app and get your Client ID and Secret")
        print("3. Copy .env.example to .env and fill in your credentials")
        sys.exit(1)
    
    # Authenticate
    print("🏃 WHOOP Training Planner")
    print("-" * 30)
    
    client = authenticate(client_id, client_secret, redirect_uri)
    
    # Show user info
    profile = client.get_profile()
    print(f"\n👤 {profile['first_name']} {profile['last_name']}")
    
    # Get body measurements
    body = client.get_body_measurements()
    print(f"   Max HR: {body['max_heart_rate']} bpm")
    
    # Get today's recommendation
    planner = TrainingPlanner(client)
    recommendation = planner.get_todays_recommendation()
    print_recommendation(recommendation)
    
    # Get weekly data
    weekly = planner.get_weekly_plan()
    
    print("="*60)
    print("WEEKLY OVERVIEW")
    print("="*60)
    
    summary = weekly["weekly_summary"]
    print(f"\n📊 Last 7 days:")
    print(f"   🧗 Climbing sessions: {summary['climbing']}")
    print(f"   🏃 Running sessions:  {summary['running']}")
    print(f"   🏋️ Gym sessions:      {summary['gym']}")
    print(f"\n   Avg recovery: {weekly['avg_recovery_7d']:.0f}%")
    print(f"   Trend: {weekly['trend']}")
    print(f"\n💡 {weekly['suggestion']}")
    
    # Show recent workouts
    print("\n" + "-"*60)
    print("RECENT ACTIVITY")
    print("-"*60)
    
    workouts = client.get_recent_workouts(days=7)
    for w in workouts[:8]:
        if w.get("score_state") == "SCORED" and w.get("score"):
            score = w["score"]
            date = datetime.fromisoformat(w["start"].replace("Z", "+00:00")).strftime("%a %d")
            sport = w.get("sport_name", "activity")[:20]
            print(f"   {date}: {sport:<20} strain {score['strain']:.1f}")
    
    # Show recent sleep
    print("\n" + "-"*60)
    print("RECENT SLEEP")
    print("-"*60)
    
    sleep_records = client.get_sleep(limit=5)
    for s in sleep_records:
        if s.get("score_state") == "SCORED" and s.get("score"):
            score = s["score"]
            perf = score.get("sleep_performance_percentage", 0)
            eff = score.get("sleep_efficiency_percentage", 0)
            date = datetime.fromisoformat(s["start"].replace("Z", "+00:00")).strftime("%a %d")
            nap = " (nap)" if s.get("nap") else ""
            print(f"   {date}{nap}: {perf:.0f}% performance, {eff:.0f}% efficiency")
    
    print()


if __name__ == "__main__":
    main()
