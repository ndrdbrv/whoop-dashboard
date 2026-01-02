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
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 18px;
            overflow: hidden;
        }
        
        .activity {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 18px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        
        .activity:last-child {
            border-bottom: none;
        }
        
        .activity-name {
            font-size: 13px;
            color: var(--white-60);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .activity-strain {
            font-size: 13px;
            color: var(--white-20);
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
        
        /* Workout Log */
        .log-card {
            background: rgba(20,20,22,0.85);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(20px);
        }
        
        .log-input {
            width: 100%;
            min-height: 120px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 14px;
            color: var(--white);
            font-family: inherit;
            font-size: 13px;
            line-height: 1.6;
            resize: vertical;
            margin-bottom: 12px;
        }
        
        .log-input::placeholder {
            color: var(--white-20);
        }
        
        .log-input:focus {
            outline: none;
            border-color: rgba(255,255,255,0.15);
        }
        
        .log-actions {
            display: flex;
            gap: 10px;
        }
        
        .log-actions .btn {
            flex: 1;
        }
        
        .btn-secondary {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.1);
            color: var(--white-40);
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .log-saved {
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid rgba(74, 222, 128, 0.2);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            font-size: 13px;
            color: var(--white-60);
            white-space: pre-wrap;
            line-height: 1.6;
        }
        
        .log-saved-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .log-saved-title {
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #4ade80;
        }
        
        .log-saved-time {
            font-size: 11px;
            color: var(--white-20);
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
        
        // Workout Log Functions
        const today = new Date().toISOString().split('T')[0];
        
        function saveLog() {
            const log = document.getElementById('workoutLog').value.trim();
            if (!log) return;
            
            const logs = JSON.parse(localStorage.getItem('workoutLogs') || '{}');
            logs[today] = {
                text: log,
                time: new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'})
            };
            localStorage.setItem('workoutLogs', JSON.stringify(logs));
            
            showSavedLog();
            document.getElementById('workoutLog').value = '';
        }
        
        function clearLog() {
            if (confirm('Clear this log?')) {
                const logs = JSON.parse(localStorage.getItem('workoutLogs') || '{}');
                delete logs[today];
                localStorage.setItem('workoutLogs', JSON.stringify(logs));
                document.getElementById('savedLog').style.display = 'none';
                document.getElementById('workoutLog').value = '';
            }
        }
        
        function showSavedLog() {
            const logs = JSON.parse(localStorage.getItem('workoutLogs') || '{}');
            const todayLog = logs[today];
            const savedDiv = document.getElementById('savedLog');
            
            if (todayLog) {
                savedDiv.innerHTML = `
                    <div class="log-saved-header">
                        <span class="log-saved-title">✓ Logged</span>
                        <span class="log-saved-time">${todayLog.time}</span>
                    </div>
                    ${todayLog.text.replace(/\n/g, '<br>')}
                `;
                savedDiv.style.display = 'block';
            }
        }
        
        // Load saved log on page load
        document.addEventListener('DOMContentLoaded', showSavedLog);
        
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
            const logs = JSON.parse(localStorage.getItem('workoutLogs') || '{}');
            const historyDiv = document.getElementById('logHistory');
            
            const sortedDates = Object.keys(logs)
                .filter(d => d !== today)
                .sort((a, b) => new Date(b) - new Date(a))
                .slice(0, 14); // Last 14 days
            
            if (sortedDates.length === 0) {
                historyDiv.innerHTML = '<div style="text-align: center; color: var(--white-20); padding: 20px;">No past workouts logged yet</div>';
                return;
            }
            
            historyDiv.innerHTML = sortedDates.map(date => {
                const log = logs[date];
                const dateObj = new Date(date + 'T12:00:00');
                const formatted = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                return `
                    <div class="log-history-item">
                        <div class="log-history-date">${formatted}</div>
                        <div class="log-history-text">${log.text.replace(/\n/g, '<br>')}</div>
                    </div>
                `;
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
        
        <!-- Workout Log Section -->
        <div class="section">
            <div class="section-title">Log Today's Workout</div>
            <div class="log-card">
                <div class="log-saved" id="savedLog" style="display: none;"></div>
                <textarea id="workoutLog" class="log-input" placeholder="Bench Press: 80kg × 8, 85kg × 6, 85kg × 6
Incline DB: 30kg × 10 × 3
Cable Flies: 15kg × 12 × 3

Add notes, RPE, how it felt..."></textarea>
                <div class="log-actions">
                    <button class="btn btn-secondary" onclick="clearLog()">Clear</button>
                    <button class="btn" onclick="saveLog()">Save Workout</button>
                </div>
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
                <div class="day {{ 'today' if day.is_today else '' }}">
                    <div class="day-name">{{ day.name }}</div>
                    <div class="day-score {{ day.color if day.color else 'empty' }}">{{ day.score }}</div>
                </div>
                {% endfor %}
            </div>
            <div class="insight">{{ weekly_suggestion }}</div>
        </div>
        
        <div class="section">
            <div class="section-title">Recent</div>
            <div class="activity-list">
                {% for activity in recent_activities %}
                <div class="activity">
                    <span class="activity-name">
                        <span>{{ activity.icon }}</span>
                        {{ activity.name }}
                    </span>
                    <span class="activity-strain">{{ activity.strain }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="footer">
            Updated {{ updated_at }} · <a href="/">Refresh</a>
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
        
        weekly_recovery = []
        for i, day_name in enumerate(day_names):
            is_today = (i == today_idx)
            score_val = "—"
            color = ""
            
            if is_today:
                score_val = str(recovery_score) if recovery_score else "—"
                color = score_color
            elif i < today_idx and recovery_history:
                day_offset = today_idx - i
                if day_offset < len(recovery_history):
                    r = recovery_history[day_offset]
                    if r.get("score_state") == "SCORED" and r.get("score"):
                        s = int(r["score"].get("recovery_score", 0))
                        score_val = str(s)
                        if s >= 67: color = "green"
                        elif s >= 34: color = "yellow"
                        else: color = "red"
            
            weekly_recovery.append({
                "name": day_name,
                "score": score_val,
                "color": color,
                "is_today": is_today
            })
        
        recent_activities = []
        for w in workouts_data[:4]:
            if w.get("score_state") == "SCORED" and w.get("score"):
                sport = w.get("sport_name", "activity")
                strain = round(w["score"].get("strain", 0), 1)
                icon = "💪"
                sport_lower = sport.lower()
                if "climb" in sport_lower or "boulder" in sport_lower: icon = "🧗"
                elif "run" in sport_lower: icon = "🏃"
                elif "gym" in sport_lower or "fitness" in sport_lower: icon = "🏋️"
                elif "sauna" in sport_lower: icon = "🧖"
                
                recent_activities.append({"icon": icon, "name": sport[:18], "strain": strain})
        
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n⛰  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=not IS_PRODUCTION)
