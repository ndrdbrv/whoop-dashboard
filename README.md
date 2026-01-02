# WHOOP Training Planner

Connects to your WHOOP and generates daily training recommendations based on your recovery, strain, and sleep data.

## Setup

### 1. Create a WHOOP Developer App

1. Go to [developer.whoop.com](https://developer.whoop.com)
2. Sign up / log in
3. Create a new app
4. Set redirect URI to `http://localhost:8080/callback`
5. Enable all scopes:
   - `read:recovery`
   - `read:cycles`
   - `read:workout`
   - `read:sleep`
   - `read:profile`
   - `read:body_measurement`

### 2. Configure Credentials

Create a `.env` file:

```
WHOOP_CLIENT_ID=your_client_id_here
WHOOP_CLIENT_SECRET=your_client_secret_here
WHOOP_REDIRECT_URI=http://localhost:8080/callback
```

### 3. Install & Run

```bash
pip install -r requirements.txt
python main.py
```

First run will open your browser to authorize the app. After that, tokens are cached.

## What It Does

Based on your WHOOP data, it recommends:

| Recovery Zone | Intensity | Target Strain |
|---------------|-----------|---------------|
| 🔴 Red (0-33%) | Rest/Easy | 0-8 |
| 🟡 Yellow (34-66%) | Moderate | 8-14 |
| 🟢 Green (67-100%) | Hard | 14-18 |

Factors in:
- Today's recovery score
- HRV and resting heart rate
- Sleep performance
- Recent strain accumulation
- Sleep debt

## API Endpoints Used

- `/v2/recovery` - Recovery scores, HRV, resting HR
- `/v2/cycle` - Daily strain
- `/v2/activity/sleep` - Sleep stages, performance
- `/v2/activity/workout` - Workout strain, HR zones
- `/v2/user/profile/basic` - User info
- `/v2/user/measurement/body` - Max HR, height, weight

