# app/exercise_db_tools.py
import json
import os
import re
import urllib.request


def search_exercise_database(query: str = "", category: str = "") -> list[dict]:
    """Queries the public WGER Exercise Database for exercise routines, instructions, and required equipment.

    Args:
        query: Optional search keyword to filter exercises by name or description (e.g. 'Squat', 'Press', 'Swing').
        category: Optional muscle/body category filter (e.g. 'Legs', 'Abs', 'Arms', 'Shoulders', 'Chest', 'Back').

    Returns:
        A list of matching exercises containing name, category, required equipment, target muscles, and description.
    """
    url = "https://wger.de/api/v2/exerciseinfo/?limit=30"
    headers = {"User-Agent": "FitCoachAI/1.0"}

    # Read API Key from environment variable if provided
    api_key = os.environ.get("WGER_API_KEY") or os.environ.get("EXERCISE_API_KEY")
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        exercises = []
        for item in data.get("results", []):
            # Find English translation
            en_trans = next(
                (t for t in item.get("translations", []) if t.get("language") == 2),
                None,
            )
            if not en_trans and item.get("translations"):
                en_trans = item.get("translations")[0]
            elif not en_trans:
                en_trans = {}

            name = en_trans.get("name", "Unknown Exercise")
            raw_desc = en_trans.get("description", "")
            clean_desc = re.sub(r"<[^<]+?>", "", raw_desc).strip()

            item_cat = item.get("category", {}).get("name", "General")
            equipment = [
                eq.get("name") for eq in item.get("equipment", []) if eq.get("name")
            ]
            muscles = [
                m.get("name_en") or m.get("name")
                for m in item.get("muscles", [])
                if m.get("name")
            ]

            # Match query and category filters
            matches_query = (
                not query
                or query.lower() in name.lower()
                or query.lower() in clean_desc.lower()
            )
            matches_category = not category or category.lower() in item_cat.lower()

            if matches_query and matches_category:
                exercises.append(
                    {
                        "name": name,
                        "category": item_cat,
                        "equipment": equipment if equipment else ["None / Bodyweight"],
                        "target_muscles": muscles,
                        "description": (
                            clean_desc[:250] + "..."
                            if len(clean_desc) > 250
                            else clean_desc
                        ),
                    }
                )

        return exercises[:5]  # Return top 5 matches
    except Exception as e:
        return [{"error": f"Failed to fetch exercise database: {str(e)}"}]
