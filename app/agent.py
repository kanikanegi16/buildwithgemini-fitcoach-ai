# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.exercise_db_tools import search_exercise_database
from app.firestore_tools import get_gear, get_workouts, log_gear, log_workout
from app.image_tools import generate_fitness_image
from app.maps_tools import find_nearby_places, geocode_address
from app.training_tools import calculate_training_metrics
from app.video_tools import generate_fitness_video

PROJECT_ID = "qwiklabs-gcp-02-9f748384db25"
MEMORY_BANK_ID = "2289072708111040512"

# Load Agent Engine resource name from deployment_metadata.json for code execution sandbox
_metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
_remote_agent_runtime_id = None
if _metadata_path.exists():
    try:
        with open(_metadata_path, "r", encoding="utf-8") as f:
            _meta = json.load(f)
            _remote_agent_runtime_id = _meta.get("remote_agent_runtime_id")
    except Exception:
        pass

code_executor = (
    AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=_remote_agent_runtime_id
    )
    if _remote_agent_runtime_id
    else None
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract durable user facts, preferences, goals, and limitations into Vertex AI Memory Bank after each turn."""
    await callback_context.add_session_to_memory()
    return None


def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService pointing to the Agent Engine Memory Bank instance."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-central1",
        agent_engine_id=MEMORY_BANK_ID,
    )


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Build A2UI v0.8 system prompt
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are FitCoach AI, an intelligent fitness assistant that helps users track "
        "their workout routines, monitor equipment & gear usage, calculate training metrics, "
        "search for exercise routines in the public exercise database, locate nearby fitness centers/parks, "
        "generate visual fitness gear/workout graphics, execute Python calculations in a secure sandbox, "
        "and plan personalized training sessions. "
        "IMPORTANT MEMORY GUIDELINES: Pay special attention to remembering and recalling all user workout preferences "
        "(e.g., preferred workout times, training frequency, equipment available), fitness goals "
        "(e.g., target race times, marathon distance, weight loss targets, strength milestones), "
        "and physical limitations or health considerations (e.g., joint/knee issues, past injuries, heart rate thresholds). "
        "Use PreloadMemoryTool to recall these details automatically at the start of each turn, and tailor all advice, "
        "workout plans, and gear recommendations around the user's specific goals and limitations. "
        "Use your Firestore tools to read and log workouts and gear, calculate_training_metrics for race predictions/HR zones, "
        "search_exercise_database to look up exercise instructions & equipment, generate_fitness_image to create visual graphics, "
        "and geocode_address & find_nearby_places to discover nearby gyms & parks."
    ),
    workflow_description="Analyze the user request, call function tools when appropriate, and return structured UI when displaying fitness plans, workout logs, gear summaries, or exercise details.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    tools=[
        PreloadMemoryTool(),
        generate_fitness_image,
        generate_fitness_video,
        geocode_address,
        find_nearby_places,
        search_exercise_database,
        calculate_training_metrics,
        get_workouts,
        log_workout,
        get_gear,
        log_gear,
        get_weather,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
