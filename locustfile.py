import json
import mimetypes
import os
import uuid
from pathlib import Path

from locust import HttpUser, between, task


ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_AUDIO_PATH = next((ROOT_DIR / "data").glob("*.wav"), None)
AUDIO_PATH = Path(os.getenv("LOCUST_AUDIO_FILE", DEFAULT_AUDIO_PATH or "")).expanduser()


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


class CSQAAppUser(HttpUser):
    wait_time = between(0.5, 1.5) # Giảm thời gian chờ để gửi request dồn dập hơn

    @task
    def get_conversations(self):
        """Test tải kết nối Database: Lấy danh sách các cuộc hội thoại từ MongoDB"""
        self.client.get("/conversations?limit=100")

    @task
    def run_pipeline_stream(self):
        """Test đồng thời pipeline stream bằng cách upload audio mẫu."""
        if not AUDIO_PATH.is_file():
            raise RuntimeError(
                "Không tìm thấy file audio mẫu. Đặt LOCUST_AUDIO_FILE=/path/to/audio.wav"
            )

        call_id = f"LOCUST-{uuid.uuid4().hex[:8].upper()}"
        mime_type = mimetypes.guess_type(AUDIO_PATH.name)[0] or "audio/wav"

        with AUDIO_PATH.open("rb") as audio_file:
            files = {
                "audio": (AUDIO_PATH.name, audio_file, mime_type),
            }
            data = {"call_id": call_id}

            with self.client.post(
                "/pipeline/run/stream",
                files=files,
                data=data,
                name="/pipeline/run/stream",
                timeout=600,
                catch_response=True,
            ) as response:
                if response.status_code >= 400:
                    response.failure(f"HTTP {response.status_code}: {response.text[:300]}")
                    return

                events = _parse_sse_events(response.text)
                error_event = next((event for event in events if event.get("type") == "error"), None)
                result_event = next((event for event in events if event.get("type") == "result"), None)

                if error_event:
                    response.failure(error_event.get("message", "Pipeline returned error event"))
                elif not result_event:
                    response.failure("Pipeline stream ended without result event")
                else:
                    response.success()
