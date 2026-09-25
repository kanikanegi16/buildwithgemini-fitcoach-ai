# app/image_tools.py
import uuid
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded bucket name and GCP Project ID
BUCKET_NAME = "fitcoach-ai-media-9f748384"
PROJECT_ID = "qwiklabs-gcp-02-9f748384db25"


def generate_fitness_image(
    prompt: str,
    tool_context: ToolContext | None = None,
) -> dict:
    """Generates a visual image or graphic for a fitness item, equipment, workout routine, or milestone badge.

    Args:
        prompt: Detailed description of the image to generate (e.g. 'A sleek pair of high-performance trail running shoes on a mountain path').
        tool_context: ADK ToolContext used to save the generated image as a session artifact.

    Returns:
        A dictionary containing the image prompt, filename, and public Cloud Storage URL.
    """
    try:
        # 1. Initialize Gemini client with global region
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        # 2. Generate image using gemini-3.1-flash-lite-image
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=f"High quality fitness item photo or graphic: {prompt}",
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return {"error": "No image bytes received from gemini-3.1-flash-lite-image."}

        filename = f"fitness_{uuid.uuid4().hex[:8]}.jpg"

        # (1) Save artifact via tool_context if available
        if tool_context:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # (2) Upload image bytes to public GCS bucket directly from memory
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return {
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate fitness image: {str(e)}"}
