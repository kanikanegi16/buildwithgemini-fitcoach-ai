# app/video_tools.py
import base64
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded bucket name and GCP Project ID
BUCKET_NAME = "fitcoach-ai-media-9f748384"
PROJECT_ID = "qwiklabs-gcp-02-9f748384db25"


def generate_fitness_video(
    prompt: str,
    tool_context: ToolContext | None = None,
) -> dict:
    """Generates a short video clip for a fitness workout, exercise technique, equipment demo, or athlete highlight.

    Args:
        prompt: Detailed description of the video clip to generate (e.g. 'Short video clip of an athlete performing a kettlebell swing with proper form').
        tool_context: ADK ToolContext used to save the generated video as a session artifact.

    Returns:
        A dictionary containing the video prompt, filename, and public Cloud Storage URL.
    """
    try:
        # 1. Initialize Gemini client with global region
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        video_bytes = None
        mime_type = "video/mp4"

        # 2. Generate video using gemini-omni-flash-preview via Interactions API
        try:
            interaction = client.interactions.create(
                model="gemini-omni-flash-preview",
                input=f"Short 5-second video clip of fitness item or workout: {prompt}",
            )
            # Extract video bytes from interaction output
            if hasattr(interaction, "output_video") and interaction.output_video:
                if hasattr(interaction.output_video, "data") and interaction.output_video.data:
                    data = interaction.output_video.data
                    if isinstance(data, str):
                        video_bytes = base64.b64decode(data)
                    else:
                        video_bytes = data
            elif hasattr(interaction, "outputs") and interaction.outputs:
                for out in interaction.outputs:
                    if hasattr(out, "data") and out.data and hasattr(out.data, "data"):
                        data = out.data.data
                        if getattr(out.data, "mime_type", None):
                            mime_type = out.data.mime_type
                        video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                        break
                    elif hasattr(out, "video") and out.video and hasattr(out.video, "data"):
                        data = out.video.data
                        video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                        break
        except Exception:
            # Fallback to generate_content if interactions API is unavailable
            response = client.models.generate_content(
                model="gemini-omni-flash-preview",
                contents=f"Short video clip: {prompt}",
            )
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        video_bytes = part.inline_data.data
                        if part.inline_data.mime_type:
                            mime_type = part.inline_data.mime_type
                        break

        if not video_bytes:
            return {"error": "No video bytes received from gemini-omni-flash-preview."}

        filename = f"fitness_video_{uuid.uuid4().hex[:8]}.mp4"

        # (1) Save artifact via tool_context if available
        if tool_context:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            try:
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception:
                pass

        # (2) Upload video bytes to public GCS bucket directly from memory
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate fitness video: {str(e)}"}
