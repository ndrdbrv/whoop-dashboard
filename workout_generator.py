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
                "title": "Easy Climbing - Technique Focus",
                "duration": 60,
                "description": "Light session focusing on movement quality",
                "details": [
                    "Warm up: 15 min easy traversing",
                    "Main: Routes 2-3 grades below max",
                    "Focus on footwork and body positioning",
                    "No limit bouldering or projecting",
                    "Cool down: Light stretching"
                ],
                "strain": (5, 8)
            },
            {
                "title": "Volume Session - Easy Mileage",
                "duration": 75,
                "description": "High volume, low intensity climbing",
                "details": [
                    "Warm up: 10 min cardio + dynamic stretches",
                    "Climb 15-20 easy routes/problems",
                    "Rest 1-2 min between climbs",
                    "Focus on efficiency and flow",
                    "No falls - if you're falling, go easier"
                ],
                "strain": (6, 9)
            }
        ],
        "moderate": [
            {
                "title": "Endurance Builder",
                "duration": 90,
                "description": "Build climbing stamina with moderate intensity",
                "details": [
                    "Warm up: 20 min progressive difficulty",
                    "4x4s: 4 problems, 4 sets, minimal rest between problems",
                    "Problems should be moderate (flash grade -1)",
                    "3-4 min rest between sets",
                    "Cool down: Easy routes + stretching"
                ],
                "strain": (10, 13)
            },
            {
                "title": "Technique + Moderate Routes",
                "duration": 90,
                "description": "Work on weaknesses at moderate intensity",
                "details": [
                    "Warm up: 15 min easy climbing",
                    "Drills: 20 min focused skill work",
                    "Pick a weakness: slopers, crimps, overhangs, slabs",
                    "Main: Routes at onsight grade",
                    "2-3 min rest between attempts",
                    "Cool down: Antagonist exercises"
                ],
                "strain": (9, 12)
            }
        ],
        "hard": [
            {
                "title": "Project Session",
                "duration": 120,
                "description": "Work your hardest routes/problems",
                "details": [
                    "Extended warm up: 30 min progressive",
                    "Project work: Pick 1-2 hard projects",
                    "Full rest between attempts (3-5 min)",
                    "Quality over quantity - max 8-10 hard attempts",
                    "Stop if power drops noticeably",
                    "Cool down: Easy climbing + stretching"
                ],
                "strain": (14, 17)
            },
            {
                "title": "Limit Bouldering",
                "duration": 90,
                "description": "Maximum power and hard moves",
                "details": [
                    "Warm up: 25 min including easy problems",
                    "Limit boulders: 2-3 grades above flash level",
                    "Work single hard moves or short sequences",
                    "Full recovery between attempts (4-5 min)",
                    "Total hard attempts: 15-20 max",
                    "Stop before fatigue compromises form"
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
        
        # Add sauna for moderate/easy days
        if zone in ["easy", "moderate"] and random.random() > 0.5:
            sauna = self.generate_workout("sauna", "any")
            if sauna:
                workouts.append(sauna)
        
        return [w for w in workouts if w is not None]

