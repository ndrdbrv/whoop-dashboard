"""Training plan generator based on WHOOP data - customized for climbing, running, gym, sauna"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from whoop_client import WhoopClient


@dataclass
class TrainingRecommendation:
    intensity: str  # "rest", "easy", "moderate", "hard", "peak"
    strain_target: tuple[float, float]  # min, max strain
    reasoning: list[str]
    climbing: str  # specific climbing recommendation
    running: str   # specific running recommendation
    gym: str       # specific gym recommendation
    sauna: str     # sauna recommendation
    warnings: list[str]


class TrainingPlanner:
    def __init__(self, client: WhoopClient):
        self.client = client
        self._cache = {}

    def _get_recent_strain(self, days: int = 7) -> list[float]:
        """Get strain values for recent cycles"""
        cycles = self.client.get_cycles(
            start=datetime.now() - timedelta(days=days),
            limit=days
        )
        return [
            c["score"]["strain"] 
            for c in cycles 
            if c.get("score_state") == "SCORED" and c.get("score")
        ]

    def _get_workouts_by_type(self, days: int = 7) -> dict:
        """Categorize recent workouts"""
        workouts = self.client.get_recent_workouts(days=days)
        
        categories = {
            "climbing": [],
            "running": [],
            "gym": [],
            "sauna": [],
            "other": []
        }
        
        climbing_keywords = ["climbing", "bouldering", "rock climbing", "lead climbing"]
        running_keywords = ["running", "run", "jogging", "trail running", "treadmill"]
        gym_keywords = ["functional fitness", "weightlifting", "strength training", "crossfit", "gym", "weight training"]
        sauna_keywords = ["sauna", "steam room", "hot tub"]
        
        for w in workouts:
            if w.get("score_state") != "SCORED" or not w.get("score"):
                continue
                
            sport = w.get("sport_name", "").lower()
            score = w.get("score") or {}
            workout_data = {
                "date": w.get("start"),
                "strain": score.get("strain", 0),
                "sport": w.get("sport_name")
            }
            
            if any(k in sport for k in climbing_keywords):
                categories["climbing"].append(workout_data)
            elif any(k in sport for k in running_keywords):
                categories["running"].append(workout_data)
            elif any(k in sport for k in gym_keywords):
                categories["gym"].append(workout_data)
            elif any(k in sport for k in sauna_keywords):
                categories["sauna"].append(workout_data)
            else:
                categories["other"].append(workout_data)
        
        return categories

    def _days_since_climbing(self, workout_categories: dict) -> int:
        """Calculate days since last climbing session"""
        climbing = workout_categories.get("climbing", [])
        if not climbing:
            return 999  # No recent climbing
        
        last_climb = max(climbing, key=lambda x: x["date"])
        last_date = datetime.fromisoformat(last_climb["date"].replace("Z", "+00:00"))
        return (datetime.now(last_date.tzinfo) - last_date).days

    def _climbing_load_7d(self, workout_categories: dict) -> tuple[int, float]:
        """Get climbing session count and total strain in last 7 days"""
        climbing = workout_categories.get("climbing", [])
        count = len(climbing)
        total_strain = sum(c["strain"] for c in climbing)
        return count, total_strain

    def get_todays_recommendation(self) -> TrainingRecommendation:
        """Generate training recommendation for today"""
        
        # Fetch current state
        recovery = self.client.get_latest_recovery()
        sleep = self.client.get_latest_sleep()
        recent_strain = self._get_recent_strain(days=7)
        workout_categories = self._get_workouts_by_type(days=7)
        
        reasoning = []
        warnings = []
        
        # ─── Recovery Score Analysis ──────────────────────────────────────────
        recovery_score = None
        hrv = None
        rhr = None
        
        if recovery and recovery.get("score_state") == "SCORED":
            score = recovery.get("score", {})
            recovery_score = score.get("recovery_score")
            hrv = score.get("hrv_rmssd_milli")
            rhr = score.get("resting_heart_rate")
            
            if score.get("user_calibrating"):
                warnings.append("WHOOP is still calibrating - recommendations may be less accurate")
        
        # ─── Sleep Quality Analysis ───────────────────────────────────────────
        sleep_performance = None
        
        if sleep and sleep.get("score_state") == "SCORED":
            score = sleep.get("score", {})
            sleep_performance = score.get("sleep_performance_percentage")
        
        # ─── Climbing Load Analysis ───────────────────────────────────────────
        days_since_climb = self._days_since_climbing(workout_categories)
        climb_count, climb_strain = self._climbing_load_7d(workout_categories)
        
        # ─── Strain Accumulation ──────────────────────────────────────────────
        avg_strain = sum(recent_strain) / len(recent_strain) if recent_strain else 0
        high_strain_days = sum(1 for s in recent_strain if s > 14)
        
        # ─── Decision Logic ───────────────────────────────────────────────────
        
        if recovery_score is None:
            intensity = "moderate"
            strain_target = (8.0, 12.0)
            reasoning.append("No recovery data - defaulting to moderate")
            climbing = "Moderate routes, focus on technique"
            running = "Easy to moderate pace"
            gym = "Regular session"
            sauna = "Optional"
        
        elif recovery_score >= 67:
            # GREEN ZONE
            reasoning.append(f"Recovery {recovery_score:.0f}% (green) - body is ready")
            
            if days_since_climb == 0:
                # Climbed today/yesterday - tendons need rest
                intensity = "moderate"
                strain_target = (10.0, 14.0)
                climbing = "⚠️ Rest fingers - climbed recently. Light hangboard at most"
                running = "Good day for a harder run"
                gym = "Upper body might be fatigued - focus on legs/cardio"
                reasoning.append("Climbed recently - prioritize finger recovery")
            elif days_since_climb == 1:
                intensity = "moderate"
                strain_target = (10.0, 14.0)
                climbing = "Easy climbing OK if fingers feel good, no projecting"
                running = "Moderate to hard effort OK"
                gym = "Full session OK"
                reasoning.append("1 day since climbing - fingers still recovering")
            elif climb_count >= 4:
                intensity = "moderate"
                strain_target = (10.0, 14.0)
                climbing = "Consider rest day from climbing - high weekly volume"
                running = "Good alternative - run or gym"
                gym = "Good option today"
                warnings.append(f"Already {climb_count} climbing sessions this week - watch for overuse")
            else:
                intensity = "hard"
                strain_target = (14.0, 18.0)
                climbing = "🔥 Project day - send something hard"
                running = "Intervals or long run"
                gym = "Heavy session OK"
                reasoning.append(f"{days_since_climb} days rest from climbing - fresh for hard session")
        
        elif recovery_score >= 34:
            # YELLOW ZONE
            reasoning.append(f"Recovery {recovery_score:.0f}% (yellow) - moderate readiness")
            
            if days_since_climb <= 1:
                intensity = "easy"
                strain_target = (6.0, 10.0)
                climbing = "Rest from climbing today"
                running = "Easy jog only"
                gym = "Light session or skip"
                sauna = "Good recovery option"
            else:
                intensity = "moderate"
                strain_target = (10.0, 14.0)
                climbing = "Moderate routes - volume over intensity"
                running = "Steady state, nothing too hard"
                gym = "Normal session, moderate weights"
            
            if sleep_performance and sleep_performance < 70:
                intensity = "easy"
                strain_target = (6.0, 10.0)
                reasoning.append(f"Sleep only {sleep_performance:.0f}% - take it easier")
                climbing = "Easy climbing or rest"
                running = "Easy jog or walk"
        
        else:
            # RED ZONE
            reasoning.append(f"Recovery {recovery_score:.0f}% (red) - prioritize recovery")
            
            if recovery_score < 20:
                intensity = "rest"
                strain_target = (0.0, 5.0)
                climbing = "❌ No climbing"
                running = "❌ No running"
                gym = "❌ Rest day"
                sauna = "✓ Light sauna for recovery"
                warnings.append("Very low recovery - check if you're getting sick or overstressed")
            else:
                intensity = "easy"
                strain_target = (4.0, 8.0)
                climbing = "❌ Skip climbing - fingers need recovery too"
                running = "Light walk at most"
                gym = "Skip or very light mobility work"
                sauna = "✓ Good for recovery"
        
        # Set sauna recommendation based on intensity
        if intensity in ["rest", "easy"]:
            sauna = "✓ Sauna is a good option for recovery"
        elif intensity == "moderate":
            sauna = "Optional - fine if you want it"
        else:
            sauna = "Skip or do post-workout only"
        
        # ─── Add metrics ──────────────────────────────────────────────────────
        if hrv:
            reasoning.append(f"HRV: {hrv:.1f}ms")
        if rhr:
            reasoning.append(f"Resting HR: {rhr:.0f}bpm")
        reasoning.append(f"7-day climbing: {climb_count} sessions, {climb_strain:.1f} total strain")
        
        return TrainingRecommendation(
            intensity=intensity,
            strain_target=strain_target,
            reasoning=reasoning,
            climbing=climbing,
            running=running,
            gym=gym,
            sauna=sauna,
            warnings=warnings
        )

    def get_weekly_plan(self) -> dict:
        """Generate a 7-day training outlook based on current trends"""
        
        today = self.get_todays_recommendation()
        recovery_data = self.client.get_recovery(limit=7)
        workout_categories = self._get_workouts_by_type(days=7)
        
        recent_recoveries = [
            r["score"]["recovery_score"] 
            for r in recovery_data 
            if r.get("score_state") == "SCORED" and r.get("score")
        ]
        
        avg_recovery = sum(recent_recoveries) / len(recent_recoveries) if recent_recoveries else 50
        
        # Count workouts by type
        climb_count = len(workout_categories.get("climbing", []))
        run_count = len(workout_categories.get("running", []))
        gym_count = len(workout_categories.get("gym", []))
        
        return {
            "today": today,
            "avg_recovery_7d": avg_recovery,
            "trend": "improving" if len(recent_recoveries) >= 2 and recent_recoveries[0] > recent_recoveries[-1] else "declining",
            "weekly_summary": {
                "climbing": climb_count,
                "running": run_count,
                "gym": gym_count
            },
            "suggestion": self._weekly_suggestion(avg_recovery, climb_count)
        }

    def _weekly_suggestion(self, avg_recovery: float, climb_count: int) -> str:
        if avg_recovery >= 60:
            if climb_count < 3:
                return "Recovery is solid - you could add another climbing session this week."
            else:
                return "Good recovery trend. Maintain current volume."
        elif avg_recovery >= 40:
            if climb_count >= 4:
                return "Recovery is mixed and climbing volume is high - consider dropping a session."
            else:
                return "Mixed recovery - alternate hard and easy days."
        else:
            return "Recovery has been low. Prioritize sleep and lighter training."


def print_recommendation(rec: TrainingRecommendation):
    """Pretty print a training recommendation"""
    
    intensity_colors = {
        "rest": "🔴",
        "easy": "🟡", 
        "moderate": "🟢",
        "hard": "🔵",
        "peak": "🟣"
    }
    
    print("\n" + "="*60)
    print("TODAY'S TRAINING RECOMMENDATION")
    print("="*60)
    
    print(f"\n{intensity_colors.get(rec.intensity, '')} Overall: {rec.intensity.upper()}")
    print(f"   Target Strain: {rec.strain_target[0]:.1f} - {rec.strain_target[1]:.1f}")
    
    print("\n" + "-"*60)
    print("ACTIVITY RECOMMENDATIONS")
    print("-"*60)
    print(f"\n🧗 Climbing:  {rec.climbing}")
    print(f"🏃 Running:   {rec.running}")
    print(f"🏋️ Gym:       {rec.gym}")
    print(f"🧖 Sauna:     {rec.sauna}")
    
    print("\n" + "-"*60)
    print("ANALYSIS")
    print("-"*60)
    for reason in rec.reasoning:
        print(f"   • {reason}")
    
    if rec.warnings:
        print("\n⚠️  Warnings:")
        for warning in rec.warnings:
            print(f"   • {warning}")
    
    print()
