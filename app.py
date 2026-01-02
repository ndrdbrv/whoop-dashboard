#!/usr/bin/env python3
"""WHOOP Training Dashboard - Sleek Ultra Design"""

import os
from datetime import datetime, timedelta
from flask import Flask, render_template_string, redirect, request, Response
from dotenv import load_dotenv

from whoop_client import WhoopClient, SCOPES, AUTH_URL, TOKEN_URL
from training_planner import TrainingPlanner
from workout_generator import WorkoutGenerator
from calendar_integration import generate_ics_content

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")

IS_PRODUCTION = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RENDER")
if IS_PRODUCTION:
    BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("RENDER_EXTERNAL_URL") or ""
    if BASE_URL and not BASE_URL.startswith("http"):
        BASE_URL = f"https://{BASE_URL}"
    REDIRECT_URI = f"{BASE_URL}/callback" if BASE_URL else "http://localhost:8080/callback"
else:
    REDIRECT_URI = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/callback")


def get_client() -> WhoopClient:
    client = WhoopClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    if not client.access_token:
        return None
    return client


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Dashboard</title>
    <meta name="theme-color" content="#000000">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        
        * { 
            box-sizing: border-box; 
            margin: 0; 
            padding: 0;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        :root {
            --black: #000;
            --gray-1: #0a0a0a;
            --gray-2: #111;
            --gray-3: #1a1a1a;
            --gray-4: #222;
            --gray-5: #333;
            --white: #fff;
            --white-60: rgba(255,255,255,0.6);
            --white-40: rgba(255,255,255,0.4);
            --white-20: rgba(255,255,255,0.2);
            --white-10: rgba(255,255,255,0.1);
            --white-05: rgba(255,255,255,0.05);
            --green: #34c759;
            --yellow: #ffcc00;
            --red: #ff3b30;
            --orange: #ff9500;
        }
        
        html, body {
            background: var(--black);
            color: var(--white);
            font-family: 'Inter', -apple-system, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Mountain Background */
        .mountain-bg {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 100vh;
            background: 
                linear-gradient(180deg, 
                    rgba(0,0,0,0) 0%,
                    rgba(0,0,0,0.3) 50%,
                    rgba(0,0,0,0.9) 75%,
                    rgba(0,0,0,1) 90%
                ),
                url('/static/mountain.jpg') center 30% / cover no-repeat;
            opacity: 0.45;
            pointer-events: none;
            z-index: 0;
        }
        
        .app {
            position: relative;
            z-index: 1;
            max-width: 440px;
            margin: 0 auto;
            padding: 0 24px 120px;
        }
        
        .setup-link {
            display: block;
            text-align: center;
            padding: 14px;
            margin: 16px 0;
            background: rgba(96, 165, 250, 0.1);
            border: 1px solid rgba(96, 165, 250, 0.2);
            border-radius: 12px;
            color: #60a5fa;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }
        
        .setup-link:hover {
            background: rgba(96, 165, 250, 0.15);
        }
        
        /* Header */
        .header {
            padding: 80px 0 60px;
            text-align: center;
        }
        
        .header-label {
            font-size: 12px;
            font-weight: 400;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--white-40);
            margin-bottom: 40px;
        }
        
        .score {
            font-size: 140px;
            font-weight: 200;
            letter-spacing: -0.05em;
            line-height: 0.9;
            margin-bottom: 12px;
        }
        
        .score.green { color: #4ade80; }
        .score.yellow { color: #fbbf24; }
        .score.red { color: #f87171; }
        
        .score-label {
            font-size: 14px;
            font-weight: 300;
            color: var(--white-40);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        
        .status {
            display: inline-block;
            margin-top: 32px;
            padding: 10px 24px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 100px;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--white-60);
            backdrop-filter: blur(10px);
        }
        
        /* Metrics */
        .metrics {
            display: flex;
            justify-content: center;
            gap: 56px;
            padding: 40px 0;
            border-top: 1px solid rgba(255,255,255,0.04);
            border-bottom: 1px solid rgba(255,255,255,0.04);
            margin-bottom: 56px;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: 300;
            color: var(--white);
            margin-bottom: 6px;
            letter-spacing: -0.02em;
        }
        
        .metric-label {
            font-size: 9px;
            font-weight: 500;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--white-20);
        }
        
        /* Section */
        .section {
            margin-bottom: 52px;
        }
        
        .section-title {
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--white-20);
            margin-bottom: 18px;
        }
        
        /* Workout Card */
        .workout {
            background: rgba(20,20,22,0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 14px;
        }
        
        .workout-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 14px;
        }
        
        .workout-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.06);
            border-radius: 12px;
            font-size: 22px;
        }
        
        .workout-meta {
            flex: 1;
        }
        
        .workout-title {
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 3px;
            letter-spacing: -0.01em;
        }
        
        .workout-time {
            font-size: 13px;
            color: #60a5fa;
            font-weight: 400;
        }
        
        .workout-desc {
            font-size: 13px;
            color: var(--white-40);
            line-height: 1.5;
            margin-bottom: 16px;
        }
        
        .workout-steps {
            list-style: none;
            margin-bottom: 20px;
        }
        
        .workout-steps li {
            font-size: 13px;
            color: var(--white-40);
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }
        
        .workout-steps li:last-child {
            border-bottom: none;
        }
        
        .workout-steps li::before {
            content: '';
            width: 4px;
            height: 4px;
            background: #60a5fa;
            border-radius: 50%;
            margin-top: 6px;
            flex-shrink: 0;
        }
        
        .btn {
            display: block;
            width: 100%;
            padding: 14px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
            color: var(--white-60);
            border-radius: 12px;
            font-size: 13px;
            font-weight: 400;
            text-align: center;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: rgba(255,255,255,0.12);
        }
        
        .btn:active {
            opacity: 0.8;
        }
        
        /* Week Grid */
        .week {
            display: flex;
            gap: 6px;
        }
        
        .day {
            flex: 1;
            text-align: center;
            padding: 14px 0;
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px;
        }
        
        .day.today {
            background: rgba(30,30,35,0.9);
            border-color: rgba(255,255,255,0.1);
        }
        
        .day-name {
            font-size: 9px;
            font-weight: 500;
            letter-spacing: 0.08em;
            color: var(--white-20);
            margin-bottom: 6px;
        }
        
        .day-score {
            font-size: 15px;
            font-weight: 400;
        }
        
        .day-score.green { color: #4ade80; }
        .day-score.yellow { color: #fbbf24; }
        .day-score.red { color: #f87171; }
        .day-score.empty { color: var(--white-10); }
        
        .day { cursor: pointer; transition: transform 0.1s; }
        .day:hover { transform: scale(1.05); }
        .day:active { transform: scale(0.98); }
        
        /* Day Modal */
        .day-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            backdrop-filter: blur(4px);
        }
        
        .day-modal-content {
            background: rgba(25,25,28,0.98);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            width: 90%;
            max-width: 320px;
            overflow: hidden;
        }
        
        .day-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .day-modal-header span {
            font-size: 18px;
            font-weight: 500;
        }
        
        .day-modal-close {
            background: none;
            border: none;
            color: var(--white-40);
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
        }
        
        .day-modal-body {
            padding: 16px 20px;
        }
        
        .day-modal-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        
        .day-modal-row:last-child { border-bottom: none; }
        
        .day-modal-label {
            font-size: 14px;
            color: var(--white-40);
        }
        
        .day-modal-value {
            font-size: 14px;
            font-weight: 500;
            color: var(--white);
        }
        
        .day-modal-value.green { color: #4ade80; }
        .day-modal-value.yellow { color: #fbbf24; }
        .day-modal-value.red { color: #f87171; }
        
        /* Insight */
        .insight {
            margin-top: 16px;
            padding: 18px 20px;
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px;
            font-size: 13px;
            color: var(--white-40);
            line-height: 1.6;
        }
        
        /* Activity */
        .activity-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .activity-card {
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 14px 16px;
        }
        
        .activity-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .activity-icon {
            font-size: 24px;
        }
        
        .activity-info {
            flex: 1;
        }
        
        .activity-name {
            font-size: 15px;
            font-weight: 500;
            color: var(--white);
            margin-bottom: 2px;
        }
        
        .activity-time {
            font-size: 12px;
            color: var(--white-40);
        }
        
        .activity-strain-badge {
            font-size: 16px;
            font-weight: 600;
            color: #60a5fa;
            background: rgba(96, 165, 250, 0.1);
            padding: 6px 12px;
            border-radius: 20px;
        }
        
        .activity-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.06);
        }
        
        .activity-stat {
            text-align: center;
        }
        
        .stat-value {
            display: block;
            font-size: 16px;
            font-weight: 500;
            color: var(--white);
        }
        
        .stat-label {
            font-size: 10px;
            color: var(--white-40);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Sleep Card */
        .sleep-card {
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 16px;
        }
        
        .sleep-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .sleep-icon {
            font-size: 28px;
        }
        
        .sleep-info {
            flex: 1;
        }
        
        .sleep-date {
            font-size: 15px;
            font-weight: 500;
            color: var(--white);
        }
        
        .sleep-total {
            font-size: 13px;
            color: var(--white-40);
        }
        
        .sleep-perf-badge {
            font-size: 16px;
            font-weight: 600;
            color: #a78bfa;
            background: rgba(167, 139, 250, 0.1);
            padding: 6px 12px;
            border-radius: 20px;
        }
        
        .sleep-stages {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 16px;
        }
        
        .sleep-stage {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .stage-bar {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .stage-bar.light { background: #94a3b8; }
        .stage-bar.rem { background: #60a5fa; }
        .stage-bar.deep { background: #8b5cf6; }
        .stage-bar.awake { background: #fbbf24; }
        
        .stage-label {
            font-size: 13px;
            color: var(--white-60);
            width: 50px;
        }
        
        .stage-value {
            font-size: 14px;
            font-weight: 500;
            color: var(--white);
        }
        
        .sleep-details {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.06);
        }
        
        .sleep-detail {
            text-align: center;
        }
        
        .detail-value {
            display: block;
            font-size: 15px;
            font-weight: 500;
            color: var(--white);
        }
        
        .detail-label {
            font-size: 10px;
            color: var(--white-40);
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 48px 0;
            font-size: 12px;
            color: var(--white-20);
        }
        
        .footer a {
            color: var(--white-40);
            text-decoration: none;
        }
        
        /* Login */
        .login {
            position: relative;
            z-index: 1;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 48px;
        }
        
        .login-icon {
            font-size: 48px;
            margin-bottom: 24px;
            opacity: 0.8;
        }
        
        .login-title {
            font-size: 28px;
            font-weight: 300;
            margin-bottom: 12px;
        }
        
        .login-subtitle {
            font-size: 14px;
            color: var(--white-40);
            max-width: 260px;
            line-height: 1.6;
            margin-bottom: 48px;
        }
        
        .login-btn {
            padding: 16px 48px;
            background: var(--white);
            color: var(--black);
            border-radius: 100px;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            transition: transform 0.2s;
        }
        
        .login-btn:active {
            transform: scale(0.98);
        }
        
        /* Warning */
        .warning {
            background: rgba(255,59,48,0.1);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            font-size: 13px;
            color: var(--red);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        /* Planned Workout */
        .planned-card {
            background: rgba(96, 165, 250, 0.08);
            border: 1px solid rgba(96, 165, 250, 0.15);
            border-radius: 16px;
            padding: 18px;
        }
        
        .planned-workout {
            font-size: 18px;
            font-weight: 500;
            color: #60a5fa;
            margin-bottom: 8px;
        }
        
        .planned-note {
            font-size: 13px;
            color: var(--white-60);
            line-height: 1.5;
            padding-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.06);
            margin-top: 12px;
        }
        
        /* Exercise Logger */
        .log-card {
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(20px);
        }
        
        .exercise-row {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        
        .exercise-row-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }
        
        .ex-select {
            width: 100%;
            padding: 14px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: var(--white);
            font-size: 14px;
            cursor: pointer;
            appearance: none;
        }
        
        .ex-select option {
            background: #1a1a1a;
            color: white;
        }
        
        .ex-input-wide {
            width: 100%;
            padding: 14px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: var(--white);
            font-size: 14px;
        }
        
        .ex-field {
            position: relative;
        }
        
        .ex-input {
            width: 100%;
            padding: 14px 12px 14px 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: var(--white);
            font-size: 16px;
            text-align: center;
        }
        
        .ex-unit {
            position: absolute;
            bottom: -18px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            color: var(--white-20);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .ex-input::placeholder { color: var(--white-20); }
        .ex-input:focus, .ex-select:focus, .ex-input-wide:focus { outline: none; border-color: rgba(255,255,255,0.2); }
        
        .add-exercise-btn {
            width: 100%;
            margin-top: 20px;
            padding: 14px;
            background: rgba(96, 165, 250, 0.15);
            border: 1px solid rgba(96, 165, 250, 0.3);
            color: #60a5fa;
        }
        
        .add-exercise-btn:hover {
            background: rgba(96, 165, 250, 0.25);
        }
        
        .optional-toggle {
            font-size: 12px;
            color: var(--white-40);
            cursor: pointer;
            padding: 8px 0;
            margin-bottom: 8px;
        }
        
        .optional-toggle:hover { color: var(--white-60); }
        
        .optional-fields { margin-bottom: 12px; }
        
        .ex-notes {
            width: 100%;
            padding: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            color: var(--white);
            font-size: 13px;
            font-family: inherit;
            resize: none;
        }
        
        .ex-notes::placeholder { color: var(--white-20); }
        
        .exercise-list {
            margin-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 12px;
        }
        
        .exercise-list {
            margin-top: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .exercise-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
        }
        
        .exercise-info {
            flex: 1;
        }
        
        .exercise-name {
            font-size: 15px;
            font-weight: 500;
            color: var(--white);
            margin-bottom: 4px;
        }
        
        .exercise-details {
            font-size: 13px;
            color: var(--white-40);
        }
        
        .exercise-delete {
            background: none;
            border: none;
            color: var(--white-20);
            cursor: pointer;
            padding: 8px;
            font-size: 16px;
        }
        
        .exercise-delete:hover { color: #f87171; }
        
        .btn-secondary {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--white-40);
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .log-history {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .log-history-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 14px;
            padding: 14px;
        }
        
        .log-history-date {
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--white-40);
            margin-bottom: 8px;
        }
        
        .log-history-text {
            font-size: 13px;
            color: var(--white-60);
            line-height: 1.5;
            white-space: pre-wrap;
        }
        
        .calendar-row {
            display: flex;
            gap: 10px;
        }
        
        .time-picker {
            flex: 0 0 110px;
            padding: 14px 12px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: var(--white);
            font-size: 13px;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
        }
        
        .time-picker option {
            background: #1a1a1a;
            color: white;
        }
        
        .calendar-row .btn {
            flex: 1;
        }
        
        @media (max-width: 380px) {
            .score { font-size: 88px; }
            .metrics { gap: 24px; }
            .week { gap: 4px; }
            .day { padding: 12px 0; border-radius: 8px; }
            .calendar-row { flex-direction: column; }
            .time-picker { flex: 1; }
        }
    </style>
    <script>
        function addToGoogleCalendar(title, description, duration, time) {
            const today = new Date();
            const [hours, mins] = time.split(':');
            today.setHours(parseInt(hours), parseInt(mins), 0, 0);
            
            const endTime = new Date(today.getTime() + duration * 60000);
            
            const formatDate = (d) => {
                return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
            };
            
            const startStr = formatDate(today);
            const endStr = formatDate(endTime);
            
            const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&details=${encodeURIComponent(description)}&dates=${startStr}/${endStr}`;
            
            window.open(url, '_blank');
        }
        
        // Exercise Database
        const exerciseDB = {
            categories: [
                { id: "warmup", name: "Warmup", exercises: ["Dynamic Stretching", "Static Stretching", "Foam Rolling", "Arm Circles", "Leg Swings", "Hip Circles", "Shoulder Rolls", "Neck Rotations", "Wrist Rotations", "Ankle Rotations", "Jumping Jacks", "High Knees", "Butt Kicks", "World Greatest Stretch", "Cat Cow", "Child Pose", "Downward Dog", "Inchworm", "Band Pull Apart Warmup", "Light Jog"] },
                { id: "lower_compound", name: "Lower Body - Compound", exercises: ["Back Squat", "Front Squat", "Goblet Squat", "Box Squat", "Forward Lunge", "Reverse Lunge", "Walking Lunge", "Bulgarian Split Squat", "Conventional Deadlift", "Sumo Deadlift", "Romanian Deadlift", "Trap Bar Deadlift", "Step Up", "Lateral Step Up"] },
                { id: "lower_isolation", name: "Lower Body - Isolation", exercises: ["Leg Extension", "Lying Hamstring Curl", "Seated Hamstring Curl", "Hip Thrust", "Glute Bridge", "Single Leg Hip Thrust", "Standing Calf Raise", "Seated Calf Raise", "Hip Adduction Machine", "Hip Abduction Machine"] },
                { id: "upper_push", name: "Upper Body - Push", exercises: ["Bench Press", "Incline Bench Press", "Decline Bench Press", "Dumbbell Bench Press", "Push Up", "Floor Press", "Close Grip Bench Press", "Dip", "Overhead Press", "Push Press", "Arnold Press", "Dumbbell Fly", "Cable Fly", "Pec Deck"] },
                { id: "upper_pull", name: "Upper Body - Pull", exercises: ["Pull Up", "Chin Up", "Lat Pulldown", "Assisted Pull Up", "Barbell Row", "Dumbbell Row", "Cable Row", "Chest Supported Row", "Inverted Row", "Face Pull", "Band Pull Apart", "Straight Arm Pulldown"] },
                { id: "shoulders_arms", name: "Shoulders & Arms", exercises: ["Lateral Raise", "Front Raise", "Rear Delt Fly", "Shoulder Shrug", "Upright Row", "Barbell Curl", "Dumbbell Curl", "Hammer Curl", "Preacher Curl", "Cable Curl", "Skull Crusher", "Triceps Pushdown", "Overhead Triceps Extension", "Wrist Curl", "Reverse Wrist Curl", "Farmers Carry"] },
                { id: "core", name: "Core", exercises: ["Plank", "Ab Wheel Rollout", "Dead Bug", "Pallof Press", "Cable Anti Rotation Hold", "Crunch", "Hanging Leg Raise", "Sit Up", "V Up", "Russian Twist", "Cable Chop"] },
                { id: "climbing_specific", name: "Climbing-Specific", exercises: ["Dead Hang", "Max Hang", "Repeater Hang", "Half Crimp Hang", "Open Hand Hang", "Full Crimp Hang", "One Arm Hang", "Assisted One Arm Hang", "Campus Ladder", "Campus Doubles", "Limit Bouldering", "System Board Circuits"] },
                { id: "conditioning", name: "Conditioning", exercises: ["Rower", "Assault Bike", "Cross Trainer", "Treadmill", "Easy Run", "Tempo Run", "Interval Run", "Hill Sprint", "Burpee", "Mountain Climber", "Jump Squat", "Jump Rope"] },
                { id: "recovery", name: "Recovery", exercises: ["Sauna", "Cold Plunge", "Contrast Therapy", "Zone 2 Cardio", "Walking", "Yoga", "Breathwork", "Mobility Flow"] }
            ]
        };
        
        const today = new Date().toISOString().split('T')[0];
        
        function formatExerciseName(name) {
            return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        }
        
        function initExerciseDB() {
            const catSelect = document.getElementById('categorySelect');
            if (!catSelect) return;
            
            exerciseDB.categories.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat.id;
                opt.textContent = cat.name;
                catSelect.appendChild(opt);
            });
            
            // Populate datalist with all exercises
            const dataList = document.getElementById('exerciseOptions');
            if (dataList) {
                exerciseDB.categories.forEach(cat => {
                    cat.exercises.forEach(ex => {
                        const opt = document.createElement('option');
                        opt.value = ex;
                        dataList.appendChild(opt);
                    });
                });
            }
        }
        
        function updateExercises() {
            const catId = document.getElementById('categorySelect').value;
            const dataList = document.getElementById('exerciseOptions');
            const input = document.getElementById('exerciseInput');
            dataList.innerHTML = '';
            input.value = '';
            
            if (!catId) {
                // Show all exercises
                exerciseDB.categories.forEach(cat => {
                    cat.exercises.forEach(ex => {
                        const opt = document.createElement('option');
                        opt.value = ex;
                        dataList.appendChild(opt);
                    });
                });
            } else {
                const cat = exerciseDB.categories.find(c => c.id === catId);
                if (cat) {
                    cat.exercises.forEach(ex => {
                        const opt = document.createElement('option');
                        opt.value = ex;
                        dataList.appendChild(opt);
                    });
                }
            }
        }
        
        function toggleOptional() {
            const fields = document.getElementById('optionalFields');
            const icon = document.getElementById('optionalIcon');
            if (fields.style.display === 'none') {
                fields.style.display = 'block';
                icon.textContent = '▾';
            } else {
                fields.style.display = 'none';
                icon.textContent = '▸';
            }
        }
        
        function addExercise() {
            const exercise = document.getElementById('exerciseInput').value.trim();
            const weight = document.getElementById('weightInput').value;
            const sets = document.getElementById('setsInput').value;
            const reps = document.getElementById('repsInput').value;
            const rpe = document.getElementById('rpeSelect').value;
            const tempo = document.getElementById('tempoSelect').value;
            const notes = document.getElementById('notesInput').value;
            
            if (!exercise) { alert('Enter an exercise'); return; }
            
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            if (!logs[today]) logs[today] = { exercises: [], notes: '' };
            
            logs[today].exercises.push({
                name: exercise,
                weight: weight ? parseFloat(weight) : null,
                sets: sets ? parseInt(sets) : null,
                reps: reps ? parseInt(reps) : null,
                rpe: rpe ? parseInt(rpe) : null,
                tempo: tempo || null,
                notes: notes || null,
                time: new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'})
            });
            
            localStorage.setItem('exerciseLogs', JSON.stringify(logs));
            
            // Clear inputs
            document.getElementById('exerciseInput').value = '';
            document.getElementById('weightInput').value = '';
            document.getElementById('setsInput').value = '';
            document.getElementById('repsInput').value = '';
            document.getElementById('rpeSelect').value = '';
            document.getElementById('tempoSelect').value = '';
            document.getElementById('notesInput').value = '';
            
            renderExerciseList();
        }
        
        function deleteExercise(idx) {
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            if (logs[today] && logs[today].exercises) {
                logs[today].exercises.splice(idx, 1);
                localStorage.setItem('exerciseLogs', JSON.stringify(logs));
                renderExerciseList();
            }
        }
        
        function renderExerciseList() {
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            const list = document.getElementById('exerciseList');
            if (!list) return;
            
            const todayExercises = logs[today]?.exercises || [];
            
            if (todayExercises.length === 0) {
                list.innerHTML = '<div style="text-align: center; color: var(--white-20); padding: 16px; font-size: 13px;">No exercises logged yet</div>';
                return;
            }
            
            list.innerHTML = todayExercises.map((ex, i) => {
                const details = [];
                if (ex.weight) details.push(ex.weight + 'kg');
                if (ex.sets && ex.reps) details.push(ex.sets + '×' + ex.reps);
                else if (ex.sets) details.push(ex.sets + ' sets');
                else if (ex.reps) details.push(ex.reps + ' reps');
                if (ex.rpe) details.push('RPE ' + ex.rpe);
                if (ex.tempo) details.push(ex.tempo);
                if (ex.notes) details.push('"' + ex.notes + '"');
                
                return '<div class="exercise-item">' +
                    '<div class="exercise-info">' +
                        '<div class="exercise-name">' + formatExerciseName(ex.name) + '</div>' +
                        '<div class="exercise-details">' + (details.join(' · ') || 'No details') + '</div>' +
                    '</div>' +
                    '<button class="exercise-delete" onclick="deleteExercise(' + i + ')">×</button>' +
                '</div>';
            }).join('');
        }
        
        function saveWorkoutNotes() {
            const notes = document.getElementById('workoutNotes').value;
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            if (!logs[today]) logs[today] = { exercises: [], notes: '' };
            logs[today].notes = notes;
            localStorage.setItem('exerciseLogs', JSON.stringify(logs));
            alert('Notes saved!');
        }
        
        function loadWorkoutNotes() {
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            const notesField = document.getElementById('workoutNotes');
            if (notesField && logs[today]?.notes) {
                notesField.value = logs[today].notes;
            }
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initExerciseDB();
            renderExerciseList();
            loadWorkoutNotes();
        });
        
        // Day Details Modal
        const dayNames = { M: 'Monday', T: 'Tuesday', W: 'Wednesday', T: 'Thursday', F: 'Friday', S: 'Saturday', S: 'Sunday' };
        const fullDayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        
        function showDayDetails(name, recovery, strain, sleep, hrv, rhr, color) {
            // Map short name to full name
            const dayIndex = ['M', 'T', 'W', 'T', 'F', 'S', 'S'].indexOf(name);
            const fullName = fullDayNames[dayIndex] || name;
            
            document.getElementById('modalDayName').textContent = fullName;
            
            const recoveryEl = document.getElementById('modalRecovery');
            recoveryEl.textContent = recovery !== '—' ? recovery + '%' : '—';
            recoveryEl.className = 'day-modal-value ' + color;
            
            document.getElementById('modalStrain').textContent = strain;
            document.getElementById('modalSleep').textContent = sleep;
            document.getElementById('modalHRV').textContent = hrv !== '—' ? hrv + ' ms' : '—';
            document.getElementById('modalRHR').textContent = rhr !== '—' ? rhr + ' bpm' : '—';
            
            document.getElementById('dayModal').style.display = 'flex';
        }
        
        function closeDayModal(e) {
            if (!e || e.target.id === 'dayModal') {
                document.getElementById('dayModal').style.display = 'none';
            }
        }
        
        // Show planned workout
        function showPlannedWorkout() {
            const plan = JSON.parse(localStorage.getItem('weeklyPlan') || '{}');
            const dayMap = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
            const todayKey = dayMap[new Date().getDay()];
            const planned = plan[todayKey];
            
            if (planned && planned.trim()) {
                document.getElementById('plannedSection').style.display = 'block';
                document.getElementById('plannedWorkout').textContent = planned;
                
                // Show AI note if enabled
                const aiEnabled = localStorage.getItem('aiCoachEnabled') === 'true';
                if (aiEnabled) {
                    const recovery = parseInt('{{ recovery_score }}') || 50;
                    let note = '';
                    
                    if (recovery >= 67) {
                        note = '🟢 High recovery - push hard today, go for projects or increase intensity.';
                    } else if (recovery >= 34) {
                        note = '🟡 Moderate recovery - stick to your plan but listen to your body.';
                    } else {
                        note = '🔴 Low recovery - consider swapping for technique work or active recovery.';
                    }
                    
                    document.getElementById('aiNote').textContent = note;
                    document.getElementById('aiNote').style.display = 'block';
                }
            }
        }
        
        document.addEventListener('DOMContentLoaded', showPlannedWorkout);
        
        function toggleHistory() {
            const historyDiv = document.getElementById('logHistory');
            const btnText = document.getElementById('historyBtnText');
            
            if (historyDiv.style.display === 'none') {
                showHistory();
                historyDiv.style.display = 'flex';
                btnText.textContent = 'Hide Workout History';
            } else {
                historyDiv.style.display = 'none';
                btnText.textContent = 'Show Workout History';
            }
        }
        
        function showHistory() {
            const logs = JSON.parse(localStorage.getItem('exerciseLogs') || '{}');
            const historyDiv = document.getElementById('logHistory');
            
            const sortedDates = Object.keys(logs)
                .filter(d => d !== today && logs[d].exercises && logs[d].exercises.length > 0)
                .sort((a, b) => new Date(b) - new Date(a))
                .slice(0, 14);
            
            if (sortedDates.length === 0) {
                historyDiv.innerHTML = '<div style="text-align: center; color: var(--white-20); padding: 20px;">No past workouts logged yet</div>';
                return;
            }
            
            historyDiv.innerHTML = sortedDates.map(date => {
                const log = logs[date];
                const dateObj = new Date(date + 'T12:00:00');
                const formatted = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                
                const exerciseList = log.exercises.map(ex => {
                    let line = formatExerciseName(ex.name);
                    if (ex.weight) line += ' ' + ex.weight + 'kg';
                    if (ex.sets && ex.reps) line += ' ' + ex.sets + '×' + ex.reps;
                    return line;
                }).join('<br>');
                
                return '<div class="log-history-item">' +
                    '<div class="log-history-date">' + formatted + ' (' + log.exercises.length + ' exercises)</div>' +
                    '<div class="log-history-text">' + exerciseList + (log.notes ? '<br><em>' + log.notes + '</em>' : '') + '</div>' +
                '</div>';
            }).join('');
        }
    </script>
</head>
<body>
    {% if not authenticated %}
    <div class="mountain-bg" style="opacity: 0.25;"></div>
    <div class="login">
        <div class="login-icon">⛰</div>
        <h1 class="login-title">Training Dashboard</h1>
        <p class="login-subtitle">Connect your WHOOP for personalized training built around your recovery.</p>
        <a href="{{ auth_url }}" class="login-btn">Connect WHOOP</a>
    </div>
    {% else %}
    <div class="mountain-bg"></div>
    <div class="app">
        <a href="/settings" class="setup-link">⚙ Edit Training Plan</a>
        <div class="header">
            <div class="header-label">{{ user_name }}</div>
            <div class="score {{ score_color }}">{{ recovery_score }}</div>
            <div class="score-label">Recovery</div>
            <div class="status">{{ intensity }} day</div>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{{ hrv }}</div>
                <div class="metric-label">HRV</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ rhr }}</div>
                <div class="metric-label">RHR</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ sleep_perf }}%</div>
                <div class="metric-label">Sleep</div>
            </div>
        </div>
        
        {% for warning in warnings %}
        <div class="warning">
            <span>⚠</span>
            <span>{{ warning }}</span>
        </div>
        {% endfor %}
        
        <!-- Planned Workout -->
        <div class="section" id="plannedSection" style="display: none;">
            <div class="section-title">Planned Today</div>
            <div class="planned-card">
                <div class="planned-workout" id="plannedWorkout"></div>
                <div class="planned-note" id="aiNote" style="display: none;"></div>
            </div>
        </div>
        
        <!-- Exercise Logger -->
        <div class="section">
            <div class="section-title">Log Exercises</div>
            <div class="log-card">
                <!-- Exercise Input -->
                <div class="exercise-row">
                    <select id="categorySelect" class="ex-select" onchange="updateExercises()">
                        <option value="">Category</option>
                    </select>
                </div>
                <div class="exercise-row">
                    <input type="text" id="exerciseInput" class="ex-input-wide" list="exerciseOptions" placeholder="Select or type exercise...">
                    <datalist id="exerciseOptions"></datalist>
                </div>
                <div class="exercise-row exercise-row-3">
                    <div class="ex-field">
                        <input type="number" id="weightInput" class="ex-input" placeholder="0">
                        <span class="ex-unit">kg</span>
                    </div>
                    <div class="ex-field">
                        <input type="number" id="setsInput" class="ex-input" placeholder="0">
                        <span class="ex-unit">sets</span>
                    </div>
                    <div class="ex-field">
                        <input type="number" id="repsInput" class="ex-input" placeholder="0">
                        <span class="ex-unit">reps</span>
                    </div>
                </div>
                <button class="btn add-exercise-btn" onclick="addExercise()">+ Add Exercise</button>
                
                <!-- Optional Details (expandable) -->
                <div class="optional-toggle" onclick="toggleOptional()">
                    <span id="optionalIcon">▸</span> Optional: RPE, Tempo, Notes
                </div>
                <div id="optionalFields" class="optional-fields" style="display: none;">
                    <div class="exercise-row">
                        <select id="rpeSelect" class="ex-select">
                            <option value="">RPE</option>
                            <option value="6">6 - Easy</option>
                            <option value="7">7 - Moderate</option>
                            <option value="8">8 - Hard</option>
                            <option value="9">9 - Very Hard</option>
                            <option value="10">10 - Max</option>
                        </select>
                        <select id="tempoSelect" class="ex-select">
                            <option value="">Tempo</option>
                            <option value="normal">Normal</option>
                            <option value="slow">Slow</option>
                            <option value="paused">Paused</option>
                            <option value="explosive">Explosive</option>
                        </select>
                    </div>
                    <input type="text" id="notesInput" class="ex-notes" placeholder="Notes...">
                </div>
                
                <!-- Logged Exercises List -->
                <div id="exerciseList" class="exercise-list"></div>
                
                <!-- Workout Notes -->
                <textarea id="workoutNotes" class="ex-notes" placeholder="Workout notes (optional)..." style="margin-top: 12px;"></textarea>
                <button class="btn" style="margin-top: 12px;" onclick="saveWorkoutNotes()">Save Notes</button>
            </div>
            
            <!-- Past Logs -->
            <div id="logHistory" class="log-history" style="display: none; margin-top: 16px;"></div>
            <button class="btn btn-secondary" style="width: 100%; margin-top: 12px;" onclick="toggleHistory()">
                <span id="historyBtnText">Show Workout History</span>
            </button>
        </div>
        
        <div class="section">
            <div class="section-title">Suggested</div>
            {% for workout in workouts %}
            <div class="workout">
                <div class="workout-header">
                    <div class="workout-icon">{{ workout.icon }}</div>
                    <div class="workout-meta">
                        <div class="workout-title">{{ workout.title }}</div>
                        <div class="workout-time">{{ workout.duration_min }} min</div>
                    </div>
                </div>
                <div class="workout-desc">{{ workout.description }}</div>
                <ul class="workout-steps">
                    {% for step in workout.details[:4] %}
                    <li>{{ step }}</li>
                    {% endfor %}
                </ul>
                <div class="calendar-row">
                    <select class="time-picker" id="time-{{ loop.index0 }}">
                        <option value="06:00">6:00 AM</option>
                        <option value="07:00">7:00 AM</option>
                        <option value="08:00">8:00 AM</option>
                        <option value="09:00">9:00 AM</option>
                        <option value="10:00">10:00 AM</option>
                        <option value="11:00">11:00 AM</option>
                        <option value="12:00">12:00 PM</option>
                        <option value="13:00">1:00 PM</option>
                        <option value="14:00">2:00 PM</option>
                        <option value="15:00">3:00 PM</option>
                        <option value="16:00">4:00 PM</option>
                        <option value="17:00" selected>5:00 PM</option>
                        <option value="18:00">6:00 PM</option>
                        <option value="19:00">7:00 PM</option>
                        <option value="20:00">8:00 PM</option>
                        <option value="21:00">9:00 PM</option>
                    </select>
                    <button class="btn" onclick="addToGoogleCalendar('{{ workout.title | e }}', '{{ workout.description | e }}', {{ workout.duration_min }}, document.getElementById('time-{{ loop.index0 }}').value)">Add to Google Calendar</button>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="section">
            <div class="section-title">This Week</div>
            <div class="week">
                {% for day in weekly_recovery %}
                <div class="day {{ 'today' if day.is_today else '' }}" onclick="showDayDetails('{{ day.name }}', '{{ day.score }}', '{{ day.strain }}', '{{ day.sleep }}', '{{ day.hrv }}', '{{ day.rhr }}', '{{ day.color }}')">
                    <div class="day-name">{{ day.name }}</div>
                    <div class="day-score {{ day.color if day.color else 'empty' }}">{{ day.score }}</div>
                </div>
                {% endfor %}
            </div>
            <div class="insight">{{ weekly_suggestion }}</div>
            
            <!-- Day Details Modal -->
            <div id="dayModal" class="day-modal" style="display: none;" onclick="closeDayModal(event)">
                <div class="day-modal-content" onclick="event.stopPropagation()">
                    <div class="day-modal-header">
                        <span id="modalDayName"></span>
                        <button class="day-modal-close" onclick="closeDayModal()">&times;</button>
                    </div>
                    <div class="day-modal-body">
                        <div class="day-modal-row">
                            <span class="day-modal-label">Recovery</span>
                            <span class="day-modal-value" id="modalRecovery"></span>
                        </div>
                        <div class="day-modal-row">
                            <span class="day-modal-label">Strain</span>
                            <span class="day-modal-value" id="modalStrain"></span>
                        </div>
                        <div class="day-modal-row">
                            <span class="day-modal-label">Sleep</span>
                            <span class="day-modal-value" id="modalSleep"></span>
                        </div>
                        <div class="day-modal-row">
                            <span class="day-modal-label">HRV</span>
                            <span class="day-modal-value" id="modalHRV"></span>
                        </div>
                        <div class="day-modal-row">
                            <span class="day-modal-label">RHR</span>
                            <span class="day-modal-value" id="modalRHR"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Recent Workouts</div>
            <div class="activity-list">
                {% for activity in recent_activities %}
                <div class="activity-card">
                    <div class="activity-header">
                        <span class="activity-icon">{{ activity.icon }}</span>
                        <div class="activity-info">
                            <div class="activity-name">{{ activity.name }}</div>
                            <div class="activity-time">{{ activity.time }}</div>
                        </div>
                        <div class="activity-strain-badge">{{ activity.strain }}</div>
                    </div>
                    <div class="activity-stats">
                        <div class="activity-stat">
                            <span class="stat-value">{{ activity.duration }}</span>
                            <span class="stat-label">min</span>
                        </div>
                        <div class="activity-stat">
                            <span class="stat-value">{{ activity.max_hr }}</span>
                            <span class="stat-label">max HR</span>
                        </div>
                        <div class="activity-stat">
                            <span class="stat-value">{{ activity.avg_hr }}</span>
                            <span class="stat-label">avg HR</span>
                        </div>
                        <div class="activity-stat">
                            <span class="stat-value">{{ activity.calories }}</span>
                            <span class="stat-label">kcal</span>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        {% if sleep_stages %}
        <div class="section">
            <div class="section-title">Last Night's Sleep</div>
            <div class="sleep-card">
                <div class="sleep-header">
                    <span class="sleep-icon">🌙</span>
                    <div class="sleep-info">
                        <div class="sleep-date">{{ sleep_stages.date }}</div>
                        <div class="sleep-total">{{ sleep_stages.total_in_bed }} in bed</div>
                    </div>
                    <div class="sleep-perf-badge">{{ sleep_stages.performance }}%</div>
                </div>
                <div class="sleep-stages">
                    <div class="sleep-stage">
                        <div class="stage-bar light" style="flex: {{ sleep_stages.light.split('h')[0] }}"></div>
                        <span class="stage-label">Light</span>
                        <span class="stage-value">{{ sleep_stages.light }}</span>
                    </div>
                    <div class="sleep-stage">
                        <div class="stage-bar rem"></div>
                        <span class="stage-label">REM</span>
                        <span class="stage-value">{{ sleep_stages.rem }}</span>
                    </div>
                    <div class="sleep-stage">
                        <div class="stage-bar deep"></div>
                        <span class="stage-label">Deep</span>
                        <span class="stage-value">{{ sleep_stages.deep }}</span>
                    </div>
                    <div class="sleep-stage">
                        <div class="stage-bar awake"></div>
                        <span class="stage-label">Awake</span>
                        <span class="stage-value">{{ sleep_stages.awake }}</span>
                    </div>
                </div>
                <div class="sleep-details">
                    <div class="sleep-detail">
                        <span class="detail-value">{{ sleep_stages.efficiency }}%</span>
                        <span class="detail-label">Efficiency</span>
                    </div>
                    <div class="sleep-detail">
                        <span class="detail-value">{{ sleep_stages.cycles }}</span>
                        <span class="detail-label">Cycles</span>
                    </div>
                    <div class="sleep-detail">
                        <span class="detail-value">{{ sleep_stages.disturbances }}</span>
                        <span class="detail-label">Disturbances</span>
                    </div>
                    <div class="sleep-detail">
                        <span class="detail-value">{{ sleep_stages.respiratory_rate }}</span>
                        <span class="detail-label">Resp Rate</span>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <div class="footer">
            Updated {{ updated_at }} · <a href="/">Refresh</a> · <a href="/settings">Settings</a>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""


_current_workouts = []


@app.route("/")
def index():
    global _current_workouts
    client = get_client()
    
    if not client:
        from urllib.parse import urlencode
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "state": "dashboard"
        }
        auth_url = f"{AUTH_URL}?{urlencode(params)}"
        return render_template_string(DASHBOARD_HTML, authenticated=False, auth_url=auth_url)
    
    try:
        profile = client.get_profile()
        user_name = f"{profile['first_name']} {profile['last_name']}"
        
        recovery_data = client.get_latest_recovery()
        recovery_score = 0
        hrv = 0
        rhr = 0
        
        if recovery_data and recovery_data.get("score_state") == "SCORED" and recovery_data.get("score"):
            score = recovery_data["score"]
            recovery_score = int(score.get("recovery_score", 0))
            hrv = round(score.get("hrv_rmssd_milli", 0), 1)
            rhr = int(score.get("resting_heart_rate", 0))
        
        if recovery_score >= 67:
            score_color = "green"
            intensity = "Hard"
        elif recovery_score >= 34:
            score_color = "yellow"
            intensity = "Moderate"
        elif recovery_score >= 15:
            score_color = "yellow"
            intensity = "Easy"
        else:
            score_color = "red"
            intensity = "Rest"
        
        sleep = client.get_latest_sleep()
        sleep_perf = 0
        if sleep and sleep.get("score_state") == "SCORED" and sleep.get("score"):
            sleep_perf = int(sleep["score"].get("sleep_performance_percentage", 0))
        
        planner = TrainingPlanner(client)
        recommendation = planner.get_todays_recommendation()
        generator = WorkoutGenerator()
        
        workouts_data = client.get_recent_workouts(days=7)
        climb_count = 0
        days_since_climb = 999
        
        for w in workouts_data:
            sport = w.get("sport_name", "").lower()
            if any(k in sport for k in ["climbing", "bouldering"]):
                climb_count += 1
                w_date = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
                days = (datetime.now(w_date.tzinfo) - w_date).days
                days_since_climb = min(days_since_climb, days)
        
        generated_workouts = generator.generate_day_plan(
            recovery_score=recovery_score,
            days_since_climb=days_since_climb if days_since_climb < 999 else 7,
            climb_count_7d=climb_count,
            recent_strain_avg=10
        )
        
        icon_map = {"climbing": "🧗", "running": "🏃", "gym": "🏋️", "sauna": "🧖", "rest": "😴"}
        
        workouts = []
        _current_workouts = []
        for w in generated_workouts:
            w.icon = icon_map.get(w.activity, "💪")
            workouts.append(w)
            _current_workouts.append(w)
        
        recovery_history = client.get_recovery(limit=7)
        day_names = ["M", "T", "W", "T", "F", "S", "S"]
        today_idx = datetime.now().weekday()
        
        # Get cycles for strain data
        cycles_data = client.get_cycles(limit=7)
        sleep_data = client.get_sleep(limit=7)
        
        weekly_recovery = []
        for i, day_name in enumerate(day_names):
            is_today = (i == today_idx)
            score_val = "—"
            color = ""
            strain_val = "—"
            sleep_val = "—"
            hrv_val = "—"
            rhr_val = "—"
            
            if is_today:
                score_val = str(recovery_score) if recovery_score else "—"
                color = score_color
                strain_val = "—"  # Today's strain is ongoing
                sleep_val = str(sleep_perf) + "%" if sleep_perf else "—"
                hrv_val = str(hrv) if hrv else "—"
                rhr_val = str(rhr) if rhr else "—"
            elif i < today_idx and recovery_history:
                day_offset = today_idx - i
                if day_offset < len(recovery_history):
                    r = recovery_history[day_offset]
                    if r.get("score_state") == "SCORED" and r.get("score"):
                        sc = r["score"]
                        s = int(sc.get("recovery_score", 0))
                        score_val = str(s)
                        hrv_val = str(round(sc.get("hrv_rmssd_milli", 0), 1))
                        rhr_val = str(int(sc.get("resting_heart_rate", 0)))
                        if s >= 67: color = "green"
                        elif s >= 34: color = "yellow"
                        else: color = "red"
                
                # Get strain from cycles
                if day_offset < len(cycles_data):
                    c = cycles_data[day_offset]
                    if c.get("score_state") == "SCORED" and c.get("score"):
                        strain_val = str(round(c["score"].get("strain", 0), 1))
                
                # Get sleep performance
                if day_offset < len(sleep_data):
                    sl = sleep_data[day_offset]
                    if sl.get("score_state") == "SCORED" and sl.get("score"):
                        sp = sl["score"].get("sleep_performance_percentage", 0)
                        sleep_val = str(int(sp)) + "%" if sp else "—"
            
            weekly_recovery.append({
                "name": day_name,
                "score": score_val,
                "color": color,
                "is_today": is_today,
                "strain": strain_val,
                "sleep": sleep_val,
                "hrv": hrv_val,
                "rhr": rhr_val
            })
        
        recent_activities = []
        for w in workouts_data[:5]:
            if w.get("score_state") == "SCORED" and w.get("score"):
                sport = w.get("sport_name", "activity")
                # Clean up the sport name
                if sport.lower() == "activity" or not sport:
                    sport = "General Activity"
                
                score = w["score"]
                strain = round(score.get("strain", 0), 1)
                max_hr = score.get("max_heart_rate", 0)
                avg_hr = score.get("average_heart_rate", 0)
                calories = round(score.get("kilojoule", 0) / 4.184)  # Convert kJ to kcal
                
                # Calculate duration
                start = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(w["end"].replace("Z", "+00:00"))
                duration_mins = int((end - start).total_seconds() / 60)
                
                # Format time
                workout_time = start.strftime("%b %d, %H:%M")
                
                icon = "💪"
                sport_lower = sport.lower()
                if "climb" in sport_lower or "boulder" in sport_lower: icon = "🧗"
                elif "run" in sport_lower: icon = "🏃"
                elif "gym" in sport_lower or "fitness" in sport_lower or "weight" in sport_lower: icon = "🏋️"
                elif "sauna" in sport_lower or "heat" in sport_lower: icon = "🧖"
                elif "cycling" in sport_lower or "bike" in sport_lower: icon = "🚴"
                elif "swim" in sport_lower: icon = "🏊"
                elif "yoga" in sport_lower: icon = "🧘"
                elif "walk" in sport_lower or "hike" in sport_lower: icon = "🚶"
                
                recent_activities.append({
                    "icon": icon, 
                    "name": sport.replace("_", " ").title()[:20], 
                    "strain": strain,
                    "duration": duration_mins,
                    "max_hr": max_hr,
                    "avg_hr": avg_hr,
                    "calories": calories,
                    "time": workout_time
                })
        
        # Get sleep stages from latest sleep
        sleep_stages = None
        if sleep_data and len(sleep_data) > 0:
            latest_sleep = sleep_data[0]
            if latest_sleep.get("score_state") == "SCORED" and latest_sleep.get("score"):
                sc = latest_sleep["score"]
                stages = sc.get("stage_summary", {})
                sleep_needed = sc.get("sleep_needed", {})
                
                # Convert milliseconds to hours/minutes
                def ms_to_hr_min(ms):
                    if not ms: return {"hr": 0, "min": 0}
                    total_mins = ms / 60000
                    return {"hr": int(total_mins // 60), "min": int(total_mins % 60)}
                
                total_in_bed = ms_to_hr_min(stages.get("total_in_bed_time_milli", 0))
                total_awake = ms_to_hr_min(stages.get("total_awake_time_milli", 0))
                light_sleep = ms_to_hr_min(stages.get("total_light_sleep_time_milli", 0))
                rem_sleep = ms_to_hr_min(stages.get("total_rem_sleep_time_milli", 0))
                deep_sleep = ms_to_hr_min(stages.get("total_slow_wave_sleep_time_milli", 0))
                
                sleep_start = datetime.fromisoformat(latest_sleep["start"].replace("Z", "+00:00"))
                sleep_end = datetime.fromisoformat(latest_sleep["end"].replace("Z", "+00:00"))
                
                sleep_stages = {
                    "date": sleep_start.strftime("%b %d"),
                    "performance": int(sc.get("sleep_performance_percentage", 0)),
                    "efficiency": int(sc.get("sleep_efficiency_percentage", 0)),
                    "total_in_bed": f"{total_in_bed['hr']}h {total_in_bed['min']}m",
                    "awake": f"{total_awake['hr']}h {total_awake['min']}m" if total_awake['hr'] > 0 else f"{total_awake['min']}m",
                    "light": f"{light_sleep['hr']}h {light_sleep['min']}m",
                    "rem": f"{rem_sleep['hr']}h {rem_sleep['min']}m",
                    "deep": f"{deep_sleep['hr']}h {deep_sleep['min']}m",
                    "disturbances": stages.get("disturbance_count", 0),
                    "cycles": stages.get("sleep_cycle_count", 0),
                    "respiratory_rate": round(sc.get("respiratory_rate", 0), 1)
                }
        
        weekly = planner.get_weekly_plan()
        
        return render_template_string(
            DASHBOARD_HTML,
            authenticated=True,
            user_name=user_name,
            recovery_score=recovery_score,
            score_color=score_color,
            intensity=intensity,
            hrv=hrv,
            rhr=rhr,
            sleep_perf=sleep_perf,
            workouts=workouts,
            warnings=recommendation.warnings,
            weekly_recovery=weekly_recovery,
            weekly_suggestion=weekly.get("suggestion", ""),
            recent_activities=recent_activities,
            sleep_stages=sleep_stages,
            updated_at=datetime.now().strftime("%H:%M")
        )
        
    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>", 500


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if code:
        client = WhoopClient(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
        client.exchange_code(code)
    return redirect("/")


@app.route("/calendar/add")
def add_to_calendar():
    # Regenerate workouts fresh to avoid memory issues
    client = get_client()
    if not client:
        return redirect("/")
    
    try:
        idx = request.args.get("idx", 0, type=int)
        
        recovery_data = client.get_latest_recovery()
        recovery_score = 0
        if recovery_data and recovery_data.get("score_state") == "SCORED" and recovery_data.get("score"):
            recovery_score = int(recovery_data["score"].get("recovery_score", 0))
        
        workouts_data = client.get_recent_workouts(days=7)
        climb_count = 0
        days_since_climb = 7
        
        for w in workouts_data:
            sport = w.get("sport_name", "").lower()
            if any(k in sport for k in ["climbing", "bouldering"]):
                climb_count += 1
                from datetime import datetime, timedelta
                w_date = datetime.fromisoformat(w["start"].replace("Z", "+00:00"))
                days = (datetime.now(w_date.tzinfo) - w_date).days
                days_since_climb = min(days_since_climb, days)
        
        generator = WorkoutGenerator()
        workouts = generator.generate_day_plan(
            recovery_score=recovery_score,
            days_since_climb=days_since_climb,
            climb_count_7d=climb_count,
            recent_strain_avg=10
        )
        
        if idx >= len(workouts):
            return "Not found", 404
        
        workout = workouts[idx]
        ics = generate_ics_content(
            title=workout.title,
            description=workout.description,
            details=workout.details,
            duration_min=workout.duration_min
        )
        return Response(ics, mimetype='text/calendar', 
                       headers={'Content-Disposition': 'attachment; filename=workout.ics'})
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/settings")
def settings():
    return render_template_string(SETTINGS_HTML)


SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: #000;
            color: #fff;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            padding: 24px;
        }
        .container { max-width: 500px; margin: 0 auto; }
        h1 {
            font-size: 24px;
            font-weight: 300;
            margin-bottom: 32px;
            text-align: center;
        }
        .back {
            display: inline-block;
            color: rgba(255,255,255,0.4);
            text-decoration: none;
            font-size: 14px;
            margin-bottom: 24px;
        }
        .section {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.4);
            margin-bottom: 16px;
        }
        .day-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }
        .day-row:last-child { border-bottom: none; }
        .day-name {
            width: 40px;
            font-size: 13px;
            font-weight: 500;
            color: rgba(255,255,255,0.6);
        }
        .day-input {
            flex: 1;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 12px;
            color: #fff;
            font-size: 14px;
        }
        .day-input:focus {
            outline: none;
            border-color: rgba(255,255,255,0.2);
        }
        .btn {
            display: block;
            width: 100%;
            padding: 16px;
            background: #fff;
            color: #000;
            border: none;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            margin-top: 20px;
        }
        .saved-msg {
            text-align: center;
            color: #4ade80;
            font-size: 14px;
            margin-top: 16px;
            display: none;
        }
        .ai-toggle {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
        }
        .ai-label {
            font-size: 14px;
            color: rgba(255,255,255,0.8);
        }
        .ai-desc {
            font-size: 12px;
            color: rgba(255,255,255,0.4);
            margin-top: 4px;
        }
        .toggle {
            width: 50px;
            height: 28px;
            background: rgba(255,255,255,0.1);
            border-radius: 14px;
            position: relative;
            cursor: pointer;
            transition: background 0.2s;
        }
        .toggle.active { background: #4ade80; }
        .toggle::after {
            content: '';
            position: absolute;
            width: 22px;
            height: 22px;
            background: #fff;
            border-radius: 50%;
            top: 3px;
            left: 3px;
            transition: transform 0.2s;
        }
        .toggle.active::after { transform: translateX(22px); }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">← Back</a>
        <h1>Training Settings</h1>
        
        <div class="section">
            <div class="section-title">Weekly Plan</div>
            <div class="day-row">
                <span class="day-name">Mon</span>
                <input type="text" class="day-input" id="mon" placeholder="e.g., Climbing - Bouldering">
            </div>
            <div class="day-row">
                <span class="day-name">Tue</span>
                <input type="text" class="day-input" id="tue" placeholder="e.g., Gym - Upper Body">
            </div>
            <div class="day-row">
                <span class="day-name">Wed</span>
                <input type="text" class="day-input" id="wed" placeholder="e.g., Rest">
            </div>
            <div class="day-row">
                <span class="day-name">Thu</span>
                <input type="text" class="day-input" id="thu" placeholder="e.g., Running">
            </div>
            <div class="day-row">
                <span class="day-name">Fri</span>
                <input type="text" class="day-input" id="fri" placeholder="e.g., Climbing - Routes">
            </div>
            <div class="day-row">
                <span class="day-name">Sat</span>
                <input type="text" class="day-input" id="sat" placeholder="e.g., Gym - Full Body">
            </div>
            <div class="day-row">
                <span class="day-name">Sun</span>
                <input type="text" class="day-input" id="sun" placeholder="e.g., Rest / Sauna">
            </div>
            <button class="btn" onclick="savePlan()">Save Weekly Plan</button>
            <div class="saved-msg" id="savedMsg">✓ Saved</div>
        </div>
        
        <div class="section">
            <div class="section-title">AI Coach</div>
            <div class="ai-toggle">
                <div>
                    <div class="ai-label">Enable AI Suggestions</div>
                    <div class="ai-desc">Claude analyzes your WHOOP data and adjusts training</div>
                </div>
                <div class="toggle" id="aiToggle" onclick="toggleAI()"></div>
            </div>
        </div>
    </div>
    
    <script>
        const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
        
        // Default plan from user's PDF
        const defaultPlan = {
            mon: 'Climbing - Power/Projecting',
            tue: 'Climbing - Endurance + Gym',
            wed: 'Rest',
            thu: 'Climbing - Power/Projecting',
            fri: 'Climbing - Endurance + Gym',
            sat: 'Optional Climbing or Gym',
            sun: 'Rest / Sauna'
        };
        
        function loadPlan() {
            const stored = localStorage.getItem('weeklyPlan');
            const plan = stored ? JSON.parse(stored) : defaultPlan;
            
            // If no stored plan, save the default
            if (!stored) {
                localStorage.setItem('weeklyPlan', JSON.stringify(defaultPlan));
            }
            
            days.forEach(day => {
                document.getElementById(day).value = plan[day] || '';
            });
            
            const aiEnabled = localStorage.getItem('aiCoachEnabled') === 'true';
            document.getElementById('aiToggle').classList.toggle('active', aiEnabled);
        }
        
        function savePlan() {
            const plan = {};
            days.forEach(day => {
                plan[day] = document.getElementById(day).value;
            });
            localStorage.setItem('weeklyPlan', JSON.stringify(plan));
            
            document.getElementById('savedMsg').style.display = 'block';
            setTimeout(() => {
                document.getElementById('savedMsg').style.display = 'none';
            }, 2000);
        }
        
        function toggleAI() {
            const toggle = document.getElementById('aiToggle');
            toggle.classList.toggle('active');
            localStorage.setItem('aiCoachEnabled', toggle.classList.contains('active'));
        }
        
        loadPlan();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n⛰  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=not IS_PRODUCTION)
