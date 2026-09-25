# app/firestore_tools.py
import datetime
import uuid
import google.auth
from google.cloud import firestore

# Hardcoded GCP Project ID (Agent Platform sets GOOGLE_CLOUD_PROJECT to project number, so hardcode string ID)
PROJECT_ID = "qwiklabs-gcp-02-9f748384db25"


def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded GCP project ID."""
    credentials, _ = google.auth.default()
    return firestore.Client(project=PROJECT_ID, credentials=credentials)


def get_workouts() -> list[dict]:
    """Retrieves all logged workout routines from the Firestore database.

    Returns:
        A list of dictionaries representing logged workout routines.
    """
    db = _get_firestore_client()
    workouts_ref = db.collection("workouts")
    docs = workouts_ref.stream()

    workouts = []
    for doc in docs:
        data = doc.to_dict()
        workouts.append(data)
    return workouts


def log_workout(
    title: str,
    category: str,
    duration_mins: int,
    calories_burned: int,
    notes: str = "",
) -> dict:
    """Logs a new workout routine into the Firestore database.

    Args:
        title: Title/name of the workout (e.g. 'Morning Interval Run').
        category: Category of workout (e.g. 'Running', 'Cycling', 'Strength', 'Yoga').
        duration_mins: Duration of the workout in minutes.
        calories_burned: Estimated calories burned.
        notes: Optional additional notes or details about the workout session.

    Returns:
        A dictionary containing the newly logged workout details.
    """
    db = _get_firestore_client()
    workout_id = f"workout_{uuid.uuid4().hex[:6]}"
    workout_data = {
        "workout_id": workout_id,
        "title": title,
        "category": category,
        "duration_mins": duration_mins,
        "calories_burned": calories_burned,
        "notes": notes,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    db.collection("workouts").document(workout_id).set(workout_data)
    return workout_data


def get_gear() -> list[dict]:
    """Retrieves all fitness gear and equipment items from the Firestore database.

    Returns:
        A list of dictionaries representing registered fitness gear items.
    """
    db = _get_firestore_client()
    gear_ref = db.collection("gear")
    docs = gear_ref.stream()

    gear_list = []
    for doc in docs:
        data = doc.to_dict()
        gear_list.append(data)
    return gear_list


def log_gear(
    name: str,
    gear_type: str,
    brand: str,
    mileage_km: float,
    max_mileage_km: float,
    status: str = "Good",
) -> dict:
    """Logs or registers a new piece of fitness gear in the Firestore database.

    Args:
        name: Name/model of the gear (e.g. 'Pegasus 40 Running Shoes').
        gear_type: Type of gear (e.g. 'Running Shoes', 'Heart Rate Monitor').
        brand: Brand/manufacturer (e.g. 'Nike', 'Garmin', 'Hoka').
        mileage_km: Current usage/mileage in kilometers.
        max_mileage_km: Maximum recommended mileage before replacement in kilometers.
        status: Current condition/status (e.g. 'Good', 'Needs Maintenance', 'Replace Soon').

    Returns:
        A dictionary containing the registered gear details.
    """
    db = _get_firestore_client()
    gear_id = f"gear_{uuid.uuid4().hex[:6]}"
    gear_data = {
        "gear_id": gear_id,
        "name": name,
        "type": gear_type,
        "brand": brand,
        "mileage_km": mileage_km,
        "max_mileage_km": max_mileage_km,
        "status": status,
    }

    db.collection("gear").document(gear_id).set(gear_data)
    return gear_data
