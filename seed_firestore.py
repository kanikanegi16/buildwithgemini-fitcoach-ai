# seed_firestore.py
import datetime
import google.auth
from google.cloud import firestore

# IMPORTANT: Hardcode the GCP project ID (do NOT use GOOGLE_CLOUD_PROJECT or google.auth.default() for project ID)
PROJECT_ID = "qwiklabs-gcp-02-9f748384db25"

def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    credentials, _ = google.auth.default()
    db = firestore.Client(project=PROJECT_ID, credentials=credentials)

    # 1. Seed workouts
    workouts_ref = db.collection("workouts")
    initial_workouts = [
        {
            "workout_id": "workout_001",
            "title": "Morning Interval Run",
            "category": "Running",
            "duration_mins": 45,
            "calories_burned": 520,
            "notes": "8x400m speed intervals at 3:45/km pace. Felt strong.",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "workout_id": "workout_002",
            "title": "Full Body Strength & Core",
            "category": "Strength",
            "duration_mins": 60,
            "calories_burned": 410,
            "notes": "Squats 4x8, Deadlifts 3x5, Planks 3x60s.",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        },
        {
            "workout_id": "workout_003",
            "title": "Zone 2 Base Endurance Ride",
            "category": "Cycling",
            "duration_mins": 90,
            "calories_burned": 750,
            "notes": "Maintained heart rate between 130-142 bpm.",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    ]

    for item in initial_workouts:
        doc_ref = workouts_ref.document(item["workout_id"])
        doc_ref.set(item)
        print(f"Seeded workout: {item['title']} ({item['workout_id']})")

    # 2. Seed gear
    gear_ref = db.collection("gear")
    initial_gear = [
        {
            "gear_id": "gear_001",
            "name": "Pegasus 40 Running Shoes",
            "type": "Running Shoes",
            "brand": "Nike",
            "mileage_km": 420.5,
            "max_mileage_km": 600.0,
            "status": "Good"
        },
        {
            "gear_id": "gear_002",
            "name": "Pro 7 Heart Rate Monitor",
            "type": "Heart Rate Monitor",
            "brand": "Garmin",
            "mileage_km": 1250.0,
            "max_mileage_km": 5000.0,
            "status": "Good"
        },
        {
            "gear_id": "gear_003",
            "name": "Speedgoat 5 Trail Shoes",
            "type": "Trail Running Shoes",
            "brand": "Hoka",
            "mileage_km": 580.0,
            "max_mileage_km": 600.0,
            "status": "Replace Soon"
        }
    ]

    for item in initial_gear:
        doc_ref = gear_ref.document(item["gear_id"])
        doc_ref.set(item)
        print(f"Seeded gear: {item['name']} ({item['gear_id']})")

    print("Firestore seeding complete!")

if __name__ == "__main__":
    seed_database()
