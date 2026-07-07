from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import types
from pathlib import Path
from typing import Any


DEFAULT_AUDIO_DIR = "audio_bench"
DEFAULT_REF_FILE = "result.json"
DEFAULT_OUT_FILE = "AI.json"
DEFAULT_BACKEND = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_NEMO_MODEL = "nvidia/nemotron-3.5-asr-streaming-0.6b"
DEFAULT_LANGUAGE = "vi-VN"
DEFAULT_GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
DEFAULT_GEMINI_MAX_TOKENS = 4096

AUDIO_MIME_BY_SUFFIX = {
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
}

GEMINI_TRANSCRIBE_PROMPT = """Bạn là hệ thống ASR tiếng Việt cho cuộc gọi chăm sóc khách hàng.

Nhiệm vụ: nghe toàn bộ audio và chép lại nguyên văn lời nói.

Yêu cầu đầu ra:
- Chỉ trả về transcript thô.
- Không thêm nhãn speaker, timestamp, markdown, giải thích hoặc tóm tắt.
- Giữ đúng thứ tự lời nói, kể cả từ đệm và đoạn lặp.
- Nếu nghe số điện thoại, mã xác nhận, mật khẩu, ID hoặc số tổng đài, hãy viết bằng chữ tiếng Việt theo âm nghe được thay vì chuyển thành chữ số.
- Ưu tiên cách viết tiếng Việt cho các thuật ngữ thường gặp: kiốt việt, hóa đơn điện tử, ultraview, teamviewer, htkk, chữ ký số.
- Nếu không chắc một từ, hãy ghi phỏng đoán gần nhất theo âm thanh.

Ngôn ngữ mục tiêu: {language}
"""


def install_nemo_prompt_alias() -> None:
    """Alias the prompt RNNT class name expected by this checkpoint.

    The Nemotron 3.5 ASR checkpoint points to
    nemo.collections.asr.models.rnnt_bpe_models_prompt.EncDecRNNTBPEModelWithPrompt,
    while NeMo 2.7.3 ships the implementation under
    hybrid_rnnt_ctc_bpe_models_prompt. Registering this alias lets NeMo restore
    the model without editing files inside .venv.
    """
    try:
        from nemo.collections.asr.models.hybrid_rnnt_ctc_bpe_models_prompt import (
            EncDecHybridRNNTCTCBPEModelWithPrompt,
            HybridRNNTCTCPromptTranscribeConfig,
        )
    except ImportError:
        return

    module_name = "nemo.collections.asr.models.rnnt_bpe_models_prompt"
    if module_name in sys.modules:
        return

    class EncDecRNNTBPEModelWithPrompt(EncDecHybridRNNTCTCBPEModelWithPrompt):
        """Compatibility class for Nemotron 3.5 prompt RNNT checkpoints.

        The published checkpoint does not contain the auxiliary CTC decoder
        weights expected by NeMo's hybrid prompt class. Transcription uses the
        RNNT decoder by default, so allow only those auxiliary CTC keys to be
        absent while keeping other checkpoint mismatches visible.
        """

        def load_state_dict(self, state_dict: Any, strict: bool = True, *args: Any, **kwargs: Any) -> Any:
            result = super().load_state_dict(state_dict, strict=False, *args, **kwargs)

            allowed_missing_prefixes = ("ctc_decoder.decoder_layers.",)
            disallowed_missing = [
                key
                for key in result.missing_keys
                if not key.startswith(allowed_missing_prefixes)
            ]

            if strict and (disallowed_missing or result.unexpected_keys):
                details = []
                if disallowed_missing:
                    details.append(f"missing keys: {disallowed_missing}")
                if result.unexpected_keys:
                    details.append(f"unexpected keys: {result.unexpected_keys}")
                raise RuntimeError("Checkpoint mismatch after compatibility load: " + "; ".join(details))

            if result.missing_keys:
                print(
                    "Compatibility load: ignored missing auxiliary CTC weights: "
                    + ", ".join(result.missing_keys),
                    flush=True,
                )

            return result

    EncDecRNNTBPEModelWithPrompt.__module__ = module_name

    alias_module = types.ModuleType(module_name)
    alias_module.EncDecRNNTBPEModelWithPrompt = EncDecRNNTBPEModelWithPrompt
    alias_module.RNNTBPEPromptTranscribeConfig = HybridRNNTCTCPromptTranscribeConfig
    sys.modules[module_name] = alias_module


def load_reference(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing reference file: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Reference JSON must be a list of objects with audio_id.")

    entries: list[dict[str, Any]] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict) or not item.get("audio_id"):
            raise ValueError(f"Reference item #{index} must contain audio_id.")
        entries.append(item)

    return entries


def load_existing(path: Path) -> dict[str, str]:
    if not path.exists() or path.stat().st_size == 0:
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return {}

    existing: dict[str, str] = {}
    for item in data:
        if isinstance(item, dict) and item.get("audio_id") and item.get("transcript"):
            existing[str(item["audio_id"])] = str(item["transcript"])
    return existing


def save_output(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, ensure_ascii=False, indent=2)
        file.write("\n")


def read_env_value(name: str, env_path: Path = Path(".env")) -> str | None:
    value = os.getenv(name)
    if value:
        return value

    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        if key != name:
            continue

        parsed_value = raw_value.strip()
        if (
            len(parsed_value) >= 2
            and parsed_value[0] == parsed_value[-1]
            and parsed_value[0] in {'"', "'"}
        ):
            parsed_value = parsed_value[1:-1]
        return parsed_value or None

    return None


def audio_mime_type(path: Path) -> str:
    return AUDIO_MIME_BY_SUFFIX.get(path.suffix.lower(), "audio/wav")


def prediction_to_text(prediction: Any) -> str:
    if isinstance(prediction, str):
        return prediction

    if hasattr(prediction, "text"):
        return str(prediction.text)

    if isinstance(prediction, dict):
        for key in ("text", "transcript", "pred_text"):
            if key in prediction:
                return str(prediction[key])

    return str(prediction)


def text_from_gemini_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)

    return str(content)


def text_from_jsonish(data: Any) -> str | None:
    if isinstance(data, str):
        return data

    if isinstance(data, list):
        parts = [text_from_jsonish(item) for item in data]
        return " ".join(part for part in parts if part)

    if isinstance(data, dict):
        transcript = data.get("transcript")
        if transcript is not None:
            return text_from_jsonish(transcript)

        text = data.get("text")
        if isinstance(text, str):
            return text

    return None


def clean_gemini_transcript(text: str) -> str:
    text = text.strip()

    fence = re.fullmatch(r"```(?:\w+)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    parsed_text = text_from_jsonish(parsed)
    if parsed_text:
        text = parsed_text.strip()

    text = re.sub(r"^\s*transcript\s*:\s*", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def build_gemini_llm(model_name: str, api_key: str, temperature: float, max_tokens: int) -> Any:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as exc:
        raise ImportError(
            "Missing langchain-google-genai package. Install requirements.txt first."
        ) from exc

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        max_output_tokens=max_tokens,
        google_api_key=api_key,
    )


def transcribe_one_gemini(llm: Any, audio_path: Path, language: str) -> str:
    try:
        from langchain_core.messages import HumanMessage
    except ImportError as exc:
        raise ImportError("Missing langchain-core package. Install requirements.txt first.") from exc

    audio_base64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": GEMINI_TRANSCRIBE_PROMPT.format(language=language),
            },
            {
                "type": "media",
                "mime_type": audio_mime_type(audio_path),
                "data": audio_base64,
            },
        ]
    )
    response = llm.invoke([message])
    content = getattr(response, "content", response)
    return clean_gemini_transcript(text_from_gemini_content(content))


def transcribe_one(asr_model: Any, audio_path: Path, language: str, batch_size: int) -> str:
    transcriptions = asr_model.transcribe(
        [str(audio_path)],
        batch_size=batch_size,
        target_lang=language,
    )
    if isinstance(transcriptions, tuple):
        transcriptions = transcriptions[0]

    if not transcriptions:
        return ""
    return prediction_to_text(transcriptions[0]).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcribe audio_bench/*.wav with Gemini or NeMo ASR and save AI.json."
    )
    parser.add_argument("--audio-dir", default=DEFAULT_AUDIO_DIR, help="Folder containing wav files")
    parser.add_argument("--ref", default=DEFAULT_REF_FILE, help="Reference JSON with audio_id order")
    parser.add_argument("--out", default=DEFAULT_OUT_FILE, help="Output AI transcript JSON")
    parser.add_argument(
        "--backend",
        choices=("gemini", "nemo"),
        default=DEFAULT_BACKEND,
        help="Transcription backend to use",
    )
    parser.add_argument(
        "--model",
        help=(
            f"Model name. Defaults to {DEFAULT_GEMINI_MODEL} for Gemini "
            f"or {DEFAULT_NEMO_MODEL} for NeMo."
        ),
    )
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Prompt language, e.g. vi-VN")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for ASR transcription")
    parser.add_argument(
        "--gemini-api-key-env",
        default=DEFAULT_GEMINI_API_KEY_ENV,
        help="Environment variable name containing the Gemini API key",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Gemini sampling temperature",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_GEMINI_MAX_TOKENS,
        help="Gemini max output tokens",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse existing transcripts in output file and only transcribe missing audio_id",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_dir = Path(args.audio_dir)
    ref_path = Path(args.ref)
    out_path = Path(args.out)
    model_name = args.model or (
        DEFAULT_GEMINI_MODEL if args.backend == "gemini" else DEFAULT_NEMO_MODEL
    )

    try:
        entries = load_reference(ref_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(exc)
        return 1

    audio_paths: dict[str, Path] = {}
    for item in entries:
        audio_id = str(item["audio_id"])
        audio_path = audio_dir / audio_id
        if not audio_path.exists():
            print(f"Missing audio file for {audio_id}: {audio_path}")
            return 1
        audio_paths[audio_id] = audio_path

    existing = load_existing(out_path) if args.resume else {}
    rows: list[dict[str, str]] = []

    if args.backend == "gemini":
        api_key = read_env_value(args.gemini_api_key_env)
        if not api_key:
            print(
                f"Missing Gemini API key. Set {args.gemini_api_key_env} "
                "in the environment or in .env."
            )
            return 1

        try:
            print(f"Loading Gemini model: {model_name}", flush=True)
            transcriber = build_gemini_llm(
                model_name,
                api_key,
                args.temperature,
                args.max_tokens,
            )
        except ImportError as exc:
            print(exc)
            return 1
    else:
        try:
            import nemo.collections.asr as nemo_asr
        except ImportError:
            print("Missing NeMo ASR package.")
            print('Install it first, for example: pip install "nemo_toolkit[asr]"')
            return 1

        install_nemo_prompt_alias()

        print(f"Loading NeMo ASR model: {model_name}", flush=True)
        transcriber = nemo_asr.models.ASRModel.from_pretrained(model_name)

    for index, item in enumerate(entries, start=1):
        audio_id = str(item["audio_id"])
        audio_path = audio_paths[audio_id]

        if audio_id in existing:
            transcript = existing[audio_id]
            print(f"[{index}/{len(entries)}] Reuse {audio_id}")
        else:
            print(f"[{index}/{len(entries)}] Transcribe {audio_path} with {args.backend}")
            if args.backend == "gemini":
                transcript = transcribe_one_gemini(transcriber, audio_path, args.language)
            else:
                transcript = transcribe_one(
                    transcriber,
                    audio_path,
                    args.language,
                    args.batch_size,
                )

        rows.append({"audio_id": audio_id, "transcript": transcript})
        save_output(out_path, rows)

    print(f"\nSaved AI transcripts to {out_path}")
    print("Run evaluation:")
    print(f"  python thang.py --ref {ref_path} --hyp {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
