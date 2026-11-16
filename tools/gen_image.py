#!/usr/bin/env python3
"""Генерация концепт-арта через Pollinations.ai (бесплатно, без API-ключа).

Примеры:
    python tools/gen_image.py "cozy tavern interior, painterly concept art"
    python tools/gen_image.py --prompt-file docs/prompts/img-0001-hero.md
    python tools/gen_image.py "hero portrait" --size 768x1024 --seed 42 --count 4
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = PROJECT_ROOT / "docs" / "art" / "raw"
BASE_URL = "https://image.pollinations.ai/prompt/"
USER_AGENT = "pet-plays-concept-art/1.0"
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAGIC = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
}


def parse_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d{2,4})\s*[x×*]\s*(\d{2,4})\s*", value.lower())
    if not match:
        raise argparse.ArgumentTypeError("размер должен быть в формате 1024x1024")
    width, height = int(match.group(1)), int(match.group(2))
    if not (64 <= width <= 2048 and 64 <= height <= 2048):
        raise argparse.ArgumentTypeError("стороны должны быть от 64 до 2048 пикселей")
    return width, height


def read_section(body: str, name: str) -> str:
    match = re.search(rf"^{name}\s*:\s*(.*)$", body, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    tail = body[match.end():]
    stop = re.search(
        r"^(NEGATIVE|NOTES|PARAMS|RESULT|FILES)\s*:", tail, re.MULTILINE | re.IGNORECASE
    )
    text = tail[: stop.start()] if stop else tail
    return (match.group(1) + "\n" + text).strip()


def load_prompt_file(path: Path) -> tuple[str, str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
            for line in parts[1].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip().lower()] = value.strip()
    prompt = read_section(body, "PROMPT") or body.strip()
    negative = read_section(body, "NEGATIVE")
    return prompt, negative, meta


def build_url(
    prompt: str,
    negative: str,
    width: int,
    height: int,
    model: str,
    seed: int,
    nologo: bool,
    enhance: bool,
    private: bool,
) -> str:
    full_prompt = prompt.strip()
    if negative.strip():
        full_prompt += "\n\nAvoid: " + negative.strip()
    params = {
        "width": width,
        "height": height,
        "seed": seed,
        "model": model,
        "nologo": "true" if nologo else "false",
        "enhance": "true" if enhance else "false",
        "private": "true" if private else "false",
        "referrer": "pet-plays",
    }
    return BASE_URL + urllib.parse.quote(full_prompt, safe="") + "?" + urllib.parse.urlencode(params)


def download(url: str, timeout: int, retries: int) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    preview = data[:300].decode("utf-8", "replace")
                    raise RuntimeError(f"сервер вернул не изображение: {preview}")
                if not data:
                    raise RuntimeError("сервер вернул пустой ответ")
                return data, content_type.split(";")[0].strip().lower()
        except (urllib.error.URLError, RuntimeError, TimeoutError) as error:
            last_error = error
            if attempt < retries:
                wait = 2 * attempt
                print(f"Попытка {attempt} не удалась: {error}. Повтор через {wait} с...")
                time.sleep(wait)
    raise SystemExit(f"Не удалось получить изображение: {last_error}")


def detect_ext(data: bytes, content_type: str) -> str:
    for magic, ext in MAGIC.items():
        if data.startswith(magic):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return EXT_BY_TYPE.get(content_type, ".jpg")


def slugify(text: str, limit: int = 32) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].strip("-") or "image"


def resolve_output(raw: str | None, prompt: str, seed: int, ext: str, prompt_id: str) -> Path:
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if path.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            return path.with_suffix(path.suffix + ext)
        return path.with_suffix(ext)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = prompt_id.strip() or slugify(prompt)
    return DEFAULT_OUT_DIR / f"{stamp}-{base}-s{seed}{ext}"


def write_metadata(path: Path, meta: dict) -> Path:
    sidecar = path.with_suffix(path.suffix + ".json")
    sidecar.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    index = path.parent / "index.jsonl"
    with index.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(meta, ensure_ascii=False) + "\n")
    return sidecar


def main() -> int:
    parser = argparse.ArgumentParser(description="Генерация изображений через Pollinations.ai")
    parser.add_argument("prompt", nargs="?", help="текст промта (по-английски)")
    parser.add_argument("--prompt-file", help="файл промта из docs/prompts/*.md")
    parser.add_argument("--negative", default="", help="что не должно попасть в кадр")
    parser.add_argument("--out", help="путь к файлу; по умолчанию docs/art/raw/")
    parser.add_argument("--size", type=parse_size, default=None, help="например 1024x1024")
    parser.add_argument("--model", default=None, help="модель Pollinations (по умолчанию sana)")
    parser.add_argument("--seed", type=int, default=None, help="-1 = случайный сид")
    parser.add_argument("--count", type=int, default=1, help="сколько вариантов сгенерировать")
    parser.add_argument("--timeout", type=int, default=120, help="таймаут запроса, секунды")
    parser.add_argument("--retries", type=int, default=3, help="число попыток")
    parser.add_argument("--no-logo", action="store_true", default=True, help="без логотипа сервиса")
    parser.add_argument("--enhance", action="store_true", help="улучшить промт на стороне сервиса")
    parser.add_argument("--public", action="store_true", help="не скрывать генерацию в ленте сервиса")
    parser.add_argument("--dry-run", action="store_true", help="только показать URL")
    args = parser.parse_args()

    meta: dict[str, str] = {}
    prompt = args.prompt or ""
    negative = args.negative
    if args.prompt_file:
        file_prompt, file_negative, meta = load_prompt_file(Path(args.prompt_file))
        prompt = prompt or file_prompt
        negative = negative or file_negative
    if not prompt.strip():
        parser.error("нужен промт: аргументом или через --prompt-file")

    if len(prompt) > 2500:
        parser.error("промт длиннее 2500 символов — сократи его")

    size = args.size or parse_size(meta.get("size", "1024x1024"))
    model = args.model or meta.get("model") or "sana"
    seed_arg = args.seed
    if seed_arg is None:
        seed_arg = int(meta["seed"]) if str(meta.get("seed", "")).strip().lstrip("-").isdigit() else -1

    width, height = size
    base_seed = seed_arg if seed_arg >= 0 else random.randint(1, 2**31 - 1)
    saved: list[Path] = []

    for index in range(max(1, args.count)):
        seed = base_seed + index
        url = build_url(
            prompt,
            negative,
            width,
            height,
            model,
            seed,
            args.no_logo,
            args.enhance,
            not args.public,
        )
        if args.dry_run:
            print(url)
            continue

        data, content_type = download(url, args.timeout, args.retries)
        ext = detect_ext(data, content_type)
        out_path = resolve_output(args.out, prompt, seed, ext, meta.get("id", ""))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)

        record = {
            "provider": "pollinations",
            "model": model,
            "prompt": prompt,
            "negative": negative,
            "width": width,
            "height": height,
            "seed": seed,
            "file": str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "source": str(args.prompt_file) if args.prompt_file else "",
            "prompt_id": meta.get("id", ""),
            "created": dt.datetime.now().isoformat(timespec="seconds"),
            "bytes": len(data),
            "content_type": content_type,
            "url": url,
        }
        sidecar = write_metadata(out_path, record)
        saved.append(out_path)
        print(f"Изображение: {record['file']}")
        print(f"Метаданные: {sidecar.relative_to(PROJECT_ROOT).as_posix()}")
        print(f"Сид: {seed}, модель: {model}, размер: {width}x{height}")

    if saved:
        print(f"Готово: {len(saved)} шт.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
