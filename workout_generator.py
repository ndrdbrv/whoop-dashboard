"""Structured workout generator based on WHOOP recovery and training load"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import random


@dataclass
class Workout:
    activity: str  # climbing, running, gym, sauna, rest
    title: str
    duration_min: int
    intensity: str  # easy, moderate, hard
    description: str
    details: list[str]
    strain_estimate: tuple[float, float]


class WorkoutGenerator:
    
    # ─── Climbing Workouts ────────────────────────────────────────────────────
    
    CLIMBING_WORKOUTS = {
        "rest": [],
        "easy": [
            {
                "title": "Easy Climbing + Finger Maintenance",
                "duration": 60,
                "description": "Light session with low-intensity finger work",
                "details": [
                    "Warm up: 15 min easy traversing",
                    "Hangboard: 3x10s half crimp @ bodyweight",
                    "Climb 2-3 grades below max",
                    "Focus on open-hand grip on easy holds",
                    "Finger rolls with light weight: 3x15",
                    "Cool down: Finger stretches + rice bucket"
                ],
                "strain": (5, 8)
            },
            {
                "title": "Volume Session - Grip Endurance",
                "duration": 75,
                "description": "High volume for finger stamina",
                "details": [
                    "Warm up: 10 min + progressive hangs",
                    "Climb 15-20 easy problems focusing on grip",
                    "Vary grip types: open, half crimp, pinch",
                    "Repeaters: 7s on/3s off x6 (half crimp)",
                    "Rest 3 min, repeat 2-3 sets",
                    "Cool down: Reverse wrist curls + stretching"
                ],
                "strain": (6, 9)
            }
        ],
        "moderate": [
            {
                "title": "Hangboard - Repeaters Protocol",
                "duration": 90,
                "description": "Build finger endurance with repeaters",
                "details": [
                    "Warm up: 20 min climbing + progressive hangs",
                    "Repeaters: 7s on/3s off x6 reps per set",
                    "4-6 sets on 20mm edge (half crimp)",
                    "2-3 sets on slopers or pinch block",
                    "3 min rest between sets",
                    "Finish with easy climbing: 15-20 min"
                ],
                "strain": (10, 13)
            },
            {
                "title": "Finger Strength + Crimpy Problems",
                "duration": 90,
                "description": "Target crimp strength on small holds",
                "details": [
                    "Warm up: 15 min easy + finger prep",
                    "Max hangs: 10s x5 on 18-20mm edge",
                    "Add weight if >15s feels easy",
                    "Rest 3 min between hangs",
                    "Climb: Seek out crimpy problems at moderate grade",
                    "Pinch block: 3x10s max effort holds",
                    "Cool down: Antagonist + finger stretches"
                ],
                "strain": (9, 12)
            },
            {
                "title": "Open Hand + Sloper Training",
                "duration": 75,
                "description": "Build open-hand and sloper strength",
                "details": [
                    "Warm up: 20 min progressive",
                    "Open hand hangs: 10s x5 on 35° sloper",
                    "Sloper problems: Focus on body tension",
                    "Pinch training: 3x8s each hand",
                    "Compression drills on steep terrain",
                    "Cool down: Wrist curls + finger extensions"
                ],
                "strain": (8, 11)
            }
        ],
        "hard": [
            {
                "title": "Max Hangs - Strength Protocol",
                "duration": 90,
                "description": "Maximum finger recruitment for strength gains",
                "details": [
                    "Extended warm up: 30 min climbing + hangs",
                    "Max hangs: 10s x5-6 on 18mm edge",
                    "Add weight until 10s is near-max effort",
                    "Full rest: 3-5 min between hangs",
                    "Vary grips: Half crimp → Full crimp → 3-finger drag",
                    "One-arm progressions if strong enough",
                    "Total finger time: ~60-90s hard effort"
                ],
                "strain": (12, 15)
            },
            {
                "title": "Limit Bouldering + Finger Power",
                "duration": 120,
                "description": "Maximum power on small holds",
                "details": [
                    "Warm up: 30 min including progressive hangs",
                    "Max hangs: 5s x4 heavy (near 1RM)",
                    "Limit boulders: Focus on hard finger moves",
                    "Seek out crimpy crux sequences",
                    "Full recovery between attempts (4-5 min)",
                    "Campus board: Ladders on small rungs (optional)",
                    "Stop when power drops"
                ],
                "strain": (14, 17)
            },
            {
                "title": "One-Arm Progressions",
                "duration": 75,
                "description": "Advanced finger strength development",
                "details": [
                    "Warm up: 25 min + two-arm max hangs",
                    "One-arm hangs: Assisted with pulley",
                    "5s x3 each hand on 20mm",
                    "Reduce assistance progressively",
                    "Min edge hangs: Find your limit edge",
                    "Offset hangs: 70/30 weight distribution",
                    "Cool down: Easy climbing + stretching"
                ],
                "strain": (13, 16)
            }
        ]
    }
    
    # ─── Running Workouts ─────────────────────────────────────────────────────
    
    RUNNING_WORKOUTS = {
        "rest": [],
        "easy": [
            {
                "title": "Recovery Run",
                "duration": 25,
                "description": "Very easy conversational pace",
                "details": [
                    "Zone 1-2 heart rate only",
                    "Should feel effortless",
                    "Can hold full conversation",
                    "Walk breaks are fine",
                    "Focus on relaxed form"
                ],
                "strain": (4, 6)
            },
            {
                "title": "Easy Jog + Mobility",
                "duration": 35,
                "description": "Light run followed by stretching",
                "details": [
                    "20 min easy jog (Zone 2)",
                    "15 min dynamic stretching",
                    "Hip circles, leg swings, lunges",
                    "Good option post-climbing"
                ],
                "strain": (5, 7)
            }
        ],
        "moderate": [
            {
                "title": "Steady State Run",
                "duration": 45,
                "description": "Moderate aerobic effort",
                "details": [
                    "5 min warm up walk/jog",
                    "35 min Zone 3 steady",
                    "Comfortably hard - short sentences",
                    "5 min cool down",
                    "Focus on consistent pace"
                ],
                "strain": (9, 12)
            },
            {
                "title": "Fartlek Run",
                "duration": 40,
                "description": "Unstructured speed play",
                "details": [
                    "10 min easy warm up",
                    "20 min fartlek: alternate fast/easy",
                    "Fast segments: 30 sec - 2 min",
                    "Easy segments: equal or longer recovery",
                    "10 min easy cool down"
                ],
                "strain": (10, 13)
            }
        ],
        "hard": [
            {
                "title": "Interval Session",
                "duration": 50,
                "description": "Structured high-intensity intervals",
                "details": [
                    "15 min progressive warm up",
                    "5x 3 min hard (Zone 4-5)",
                    "2 min easy jog between",
                    "10 min cool down jog",
                    "Focus on consistent effort each rep"
                ],
                "strain": (13, 16)
            },
            {
                "title": "Tempo Run",
                "duration": 55,
                "description": "Sustained threshold effort",
                "details": [
                    "15 min easy warm up",
                    "25 min tempo (Zone 4)",
                    "Comfortably uncomfortable pace",
                    "15 min easy cool down",
                    "No talking during tempo block"
                ],
                "strain": (14, 17)
            }
        ]
    }
    
    # ─── Gym Workouts ─────────────────────────────────────────────────────────
    
    GYM_WORKOUTS = {
        "rest": [],
        "easy": [
            {
                "title": "Mobility & Core",
                "duration": 40,
                "description": "Active recovery focused on movement quality",
                "details": [
                    "15 min foam rolling / stretching",
                    "Core circuit: 3 rounds",
                    "- Plank 30 sec",
                    "- Dead bug 10 each side",
                    "- Bird dog 10 each side",
                    "15 min yoga flow or stretching"
                ],
                "strain": (3, 5)
            }
        ],
        "moderate": [
            {
                "title": "Full Body - Moderate",
                "duration": 60,
                "description": "Balanced strength session",
                "details": [
                    "Warm up: 10 min cardio + dynamic stretches",
                    "Squats or Lunges: 3x10",
                    "Push (bench/press): 3x10",
                    "Pull (rows/pullups): 3x10",
                    "Core: 2x15 each",
                    "Cool down stretching"
                ],
                "strain": (9, 12)
            },
            {
                "title": "Climbing Antagonists",
                "duration": 50,
                "description": "Balance out climbing muscle imbalances",
                "details": [
                    "Push focus to balance all the pulling",
                    "Push ups: 3x15",
                    "Shoulder press: 3x12",
                    "Tricep dips: 3x12",
                    "Reverse wrist curls: 3x15",
                    "External rotation: 3x12 each"
                ],
                "strain": (7, 10)
            }
        ],
        "hard": [
            {
                "title": "Strength Session - Heavy",
                "duration": 75,
                "description": "Compound lifts at high intensity",
                "details": [
                    "Warm up: 15 min progressive",
                    "Squat/Deadlift: 5x5 heavy",
                    "Bench/OHP: 4x6",
                    "Pull ups weighted: 4x6",
                    "Accessories: 2-3 exercises",
                    "Rest 2-3 min between heavy sets"
                ],
                "strain": (12, 15)
            }
        ]
    }
    
    # ─── Sauna ────────────────────────────────────────────────────────────────
    
    SAUNA_WORKOUTS = {
        "any": [
            {
                "title": "Sauna - Recovery Session",
                "duration": 20,
                "description": "Heat exposure for recovery",
                "details": [
                    "2-3 rounds of 8-12 min",
                    "Cool shower between rounds",
                    "Hydrate well before and after",
                    "Good for circulation and relaxation",
                    "Best on rest days or after easy workouts"
                ],
                "strain": (2, 4)
            }
        ]
    }

    def generate_workout(self, activity: str, intensity: str) -> Optional[Workout]:
        """Generate a single workout based on activity type and intensity"""
        
        if activity == "sauna":
            options = self.SAUNA_WORKOUTS["any"]
        elif activity == "climbing":
            options = self.CLIMBING_WORKOUTS.get(intensity, [])
        elif activity == "running":
            options = self.RUNNING_WORKOUTS.get(intensity, [])
        elif activity == "gym":
            options = self.GYM_WORKOUTS.get(intensity, [])
        else:
            return None
        
        if not options:
            return None
        
        workout_data = random.choice(options)
        
        return Workout(
            activity=activity,
            title=workout_data["title"],
            duration_min=workout_data["duration"],
            intensity=intensity,
            description=workout_data["description"],
            details=workout_data["details"],
            strain_estimate=workout_data["strain"]
        )

    def generate_day_plan(
        self,
        recovery_score: float,
        days_since_climb: int,
        climb_count_7d: int,
        recent_strain_avg: float
    ) -> list[Workout]:
        """Generate a full day's workout plan based on recovery and training load"""
        
        workouts = []
        
        # Determine intensity zone
        if recovery_score >= 67:
            zone = "hard"
        elif recovery_score >= 34:
            zone = "moderate"
        elif recovery_score >= 15:
            zone = "easy"
        else:
            zone = "rest"
        
        # Rest day
        if zone == "rest":
            workouts.append(Workout(
                activity="rest",
                title="Rest Day",
                duration_min=0,
                intensity="rest",
                description="Full recovery day - no training",
                details=[
                    "Sleep 8+ hours",
                    "Light walking OK",
                    "Focus on nutrition and hydration",
                    "Sauna optional for circulation"
                ],
                strain_estimate=(0, 3)
            ))
            sauna = self.generate_workout("sauna", "any")
            if sauna:
                workouts.append(sauna)
            return workouts
        
        # Climbing logic
        if days_since_climb >= 2 and climb_count_7d < 4:
            # Fresh for climbing
            climb_workout = self.generate_workout("climbing", zone)
            if climb_workout:
                workouts.append(climb_workout)
        elif days_since_climb == 1:
            # Climbed yesterday - light climbing or cross train
            if zone == "hard":
                # Downgrade to moderate or run instead
                if random.random() > 0.5:
                    workouts.append(self.generate_workout("climbing", "easy"))
                else:
                    workouts.append(self.generate_workout("running", "moderate"))
            else:
                workouts.append(self.generate_workout("running", zone))
        else:
            # Climbed today or very recently - cross train
            if zone != "easy":
                workouts.append(self.generate_workout("running", zone) or 
                               self.generate_workout("gym", zone))
            else:
                workouts.append(self.generate_workout("gym", "easy"))
        
        # Add secondary workout for high recovery days
        if zone == "hard" and len(workouts) == 1 and recovery_score >= 75:
            secondary = self.generate_workout("running", "easy")
            if secondary:
                secondary.title = "Optional: " + secondary.title
                workouts.append(secondary)
        
        # Always add sauna for recovery - adjust duration based on recovery
        sauna = self.generate_workout("sauna", "any")
        if sauna:
            if recovery_score >= 67:
                sauna.duration_min = 20  # High recovery = longer sauna
                sauna.description = "Recovery sauna - great day for heat therapy"
            elif recovery_score >= 34:
                sauna.duration_min = 15
                sauna.description = "Moderate sauna session for circulation"
            else:
                sauna.duration_min = 10
                sauna.description = "Light sauna to aid recovery"
            workouts.append(sauna)
        
        return [w for w in workouts if w is not None]

