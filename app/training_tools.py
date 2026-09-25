# app/training_tools.py


def calculate_training_metrics(
    recent_5k_time_mins: float | None = None,
    max_heart_rate: int | None = None,
) -> dict:
    """Calculates training heart rate zones and predicts race times based on a recent 5k time or max HR.

    Args:
        recent_5k_time_mins: Recent 5k race/time-trial duration in minutes (e.g. 22.5 for 22 mins 30 secs).
        max_heart_rate: User's maximum heart rate in bpm (e.g. 185).

    Returns:
        A dictionary containing predicted race finish times and heart rate zone boundaries.
    """
    results = {}

    # 1. Calculate Race Pace Predictions if 5k time is provided
    if recent_5k_time_mins and recent_5k_time_mins > 0:
        # Riegel's Formula: T2 = T1 * (D2 / D1)^1.06
        time_10k = recent_5k_time_mins * (10.0 / 5.0) ** 1.06
        time_half = recent_5k_time_mins * (21.0975 / 5.0) ** 1.06
        time_marathon = recent_5k_time_mins * (42.195 / 5.0) ** 1.06

        def format_time(mins: float) -> str:
            hrs = int(mins // 60)
            remaining_mins = int(mins % 60)
            secs = int(round((mins - int(mins)) * 60))
            if hrs > 0:
                return f"{hrs}h {remaining_mins:02d}m {secs:02d}s"
            return f"{remaining_mins}m {secs:02d}s"

        results["race_predictions"] = {
            "5k_baseline": format_time(recent_5k_time_mins),
            "10k_predicted": format_time(time_10k),
            "half_marathon_predicted": format_time(time_half),
            "marathon_predicted": format_time(time_marathon),
            "easy_pace_per_km": format_time((recent_5k_time_mins / 5.0) * 1.3),
            "tempo_pace_per_km": format_time((recent_5k_time_mins / 5.0) * 1.1),
        }

    # 2. Calculate Heart Rate Zones if Max HR is provided (default 185 if unspecified)
    hr_max = max_heart_rate if (max_heart_rate and max_heart_rate > 0) else 185
    results["heart_rate_zones_bpm"] = {
        "max_hr": hr_max,
        "zone_1_recovery": f"{int(hr_max * 0.50)}-{int(hr_max * 0.60)} bpm",
        "zone_2_aerobic_base": f"{int(hr_max * 0.60)}-{int(hr_max * 0.70)} bpm",
        "zone_3_tempo": f"{int(hr_max * 0.70)}-{int(hr_max * 0.80)} bpm",
        "zone_4_threshold": f"{int(hr_max * 0.80)}-{int(hr_max * 0.90)} bpm",
        "zone_5_anaerobic": f"{int(hr_max * 0.90)}-{hr_max} bpm",
    }

    return results
