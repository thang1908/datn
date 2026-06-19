import json
import mimetypes
import os
import random
import uuid
from pathlib import Path

from locust import HttpUser, between, task


ROOT_DIR = Path(__file__).resolve().parent
SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}

AUDIO_DIR = Path(os.getenv("LOCUST_AUDIO_DIR", ROOT_DIR / "data")).expanduser()
CONVERSATION_LIMIT = int(os.getenv("LOCUST_CONVERSATION_LIMIT", "100"))
MIN_WAIT_SECONDS = float(os.getenv("LOCUST_MIN_WAIT", "0.5"))
MAX_WAIT_SECONDS = float(os.getenv("LOCUST_MAX_WAIT", "1.5"))


def _discover_audio_files() -> list[Path]:
    explicit_audio_file = os.getenv("LOCUST_AUDIO_FILE")
    if explicit_audio_file:
        return [Path(explicit_audio_file).expanduser()]

    if not AUDIO_DIR.is_dir():
        return []

    return sorted(
        path
        for path in AUDIO_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


AUDIO_FILES = _discover_audio_files()


def _parse_sse_events(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue

        payload = line.removeprefix("data:").strip()
        if not payload:
            continue

        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            events.append({"type": "invalid", "raw": payload})

    return events


class BaseCSQAUser(HttpUser):
    abstract = True
    wait_time = between(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)

    def get_conversations(self):
        """Test tải API + MongoDB bằng cách lấy danh sách kết quả đã lưu."""
        with self.client.get(
            f"/conversations?limit={CONVERSATION_LIMIT}",
            name="/conversations?limit=:limit",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"HTTP {response.status_code}: {response.text[:300]}")
                return

            try:
                payload = response.json()
            except json.JSONDecodeError:
                response.failure("Response is not valid JSON")
                return

            if not isinstance(payload.get("results"), list):
                response.failure("Response does not contain a results list")
                return

            response.success()

    def run_pipeline_stream(
        self,
        endpoint: str = "/pipeline/run/stream",
        timeout: int = 600,
    ):
        """Test pipeline bằng cách upload audio và đọc SSE đến khi có result."""
        if not AUDIO_FILES:
            raise RuntimeError(
                "Không tìm thấy file audio mẫu. Đặt LOCUST_AUDIO_FILE=/path/to/audio.wav "
                "hoặc LOCUST_AUDIO_DIR=/path/to/audio-directory"
            )

        audio_path = random.choice(AUDIO_FILES)
        if not audio_path.is_file():
            raise RuntimeError(f"File audio mẫu không tồn tại: {audio_path}")

        call_id = f"LOCUST-{uuid.uuid4().hex[:8].upper()}"
        mime_type = mimetypes.guess_type(audio_path.name)[0] or "audio/wav"

        with audio_path.open("rb") as audio_file:
            files = {
                "audio": (audio_path.name, audio_file, mime_type),
            }
            data = {"call_id": call_id}

            with self.client.post(
                endpoint,
                files=files,
                data=data,
                name=endpoint,
                timeout=timeout,
                catch_response=True,
            ) as response:
                if response.status_code >= 400:
                    response.failure(f"HTTP {response.status_code}: {response.text[:300]}")
                    return

                events = _parse_sse_events(response.text)
                invalid_event = next((event for event in events if event.get("type") == "invalid"), None)
                error_event = next((event for event in events if event.get("type") == "error"), None)
                result_event = next((event for event in events if event.get("type") == "result"), None)

                if invalid_event:
                    response.failure(f"Invalid SSE JSON: {invalid_event.get('raw', '')[:200]}")
                elif error_event:
                    response.failure(error_event.get("message", "Pipeline returned error event"))
                elif not result_event:
                    response.failure("Pipeline stream ended without result event")
                elif not result_event.get("data", {}).get("ConversationId"):
                    response.failure("Pipeline result does not contain ConversationId")
                else:
                    response.success()


class DBHistoryUser(BaseCSQAUser):
    """Scenario 1: đo tải API đọc lịch sử và MongoDB."""

    @task
    def browse_history(self):
        self.get_conversations()


class PipelineUser(BaseCSQAUser):
    """Scenario 2: đo pipeline thật, có gọi Gemini."""

    @task
    def upload_audio(self):
        self.run_pipeline_stream()


class PipelineMockUser(BaseCSQAUser):
    """Scenario 3: đo pipeline mock, không gọi Gemini nhưng vẫn upload, SSE và lưu DB."""

    @task
    def upload_audio_mock(self):
        self.run_pipeline_stream("/pipeline/run/mock/stream", timeout=120)


class MixedWorkloadUser(BaseCSQAUser):
    """Scenario 4: mô phỏng người dùng thật, đọc lịch sử nhiều hơn upload audio thật."""

    @task(8)
    def browse_history(self):
        self.get_conversations()

    @task(2)
    def upload_audio(self):
        self.run_pipeline_stream()
