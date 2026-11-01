#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
JOURNAL_ROOT = PROJECT_ROOT / "static" / "img" / "journal"
CONTENT_ROOT = PROJECT_ROOT / "content"
JPEG_EXTENSIONS = {".jpeg", ".jpg"}


def image_dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    width_match = re.search(r"pixelWidth: (\d+)", result.stdout)
    height_match = re.search(r"pixelHeight: (\d+)", result.stdout)
    if not width_match or not height_match:
        raise RuntimeError(f"Could not read dimensions for {path}")
    return int(width_match.group(1)), int(height_match.group(1))


def target_url(path: Path) -> str:
    return "/" + path.relative_to(PROJECT_ROOT / "static").as_posix()


def convert_image(source: Path, destination: Path, max_dimension: int, quality: int) -> None:
    width, height = image_dimensions(source)
    resize_arguments: list[str] = []
    if max(width, height) > max_dimension:
        if width >= height:
            resize_arguments = ["-resize", str(max_dimension), "0"]
        else:
            resize_arguments = ["-resize", "0", str(max_dimension)]

    temporary = destination.with_name(destination.name + ".tmp")
    command = [
        "cwebp",
        "-quiet",
        "-q",
        str(quality),
        "-m",
        "6",
        "-mt",
        "-sharp_yuv",
        "-metadata",
        "none",
        *resize_arguments,
        str(source),
        "-o",
        str(temporary),
    ]
    subprocess.run(command, check=True)

    if temporary.stat().st_size >= source.stat().st_size:
        temporary.unlink()
        raise RuntimeError(f"Optimized image is not smaller than its source: {source}")
    temporary.replace(destination)


def update_content(replacements: dict[str, str]) -> int:
    changed_files = 0
    for markdown_file in sorted(CONTENT_ROOT.rglob("*.md")):
        original = markdown_file.read_text(encoding="utf-8")
        updated = original
        for old_url, new_url in replacements.items():
            updated = updated.replace(old_url, new_url)
        if updated != original:
            markdown_file.write_text(updated, encoding="utf-8")
            changed_files += 1
    return changed_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert journal JPEGs to size-limited WebP images.")
    parser.add_argument("--apply", action="store_true", help="Write converted images and update Markdown references.")
    parser.add_argument("--max-dimension", type=int, default=2000, help="Maximum image width or height in pixels.")
    parser.add_argument("--quality", type=int, default=82, help="WebP quality from 0 to 100.")
    args = parser.parse_args()

    if shutil.which("cwebp") is None:
        raise SystemExit("cwebp is required. On macOS, install it with: brew install webp")
    if shutil.which("sips") is None:
        raise SystemExit("sips is required; this optimizer currently supports macOS.")

    sources = sorted(
        path for path in JOURNAL_ROOT.rglob("*") if path.is_file() and path.suffix.lower() in JPEG_EXTENSIONS
    )
    if not sources:
        print("No journal JPEGs need optimization.")
        return

    replacements = {target_url(source): target_url(source.with_suffix(".webp")) for source in sources}
    old_size = sum(source.stat().st_size for source in sources)
    print(f"Found {len(sources)} journal JPEGs.")
    if not args.apply:
        for old_url, new_url in replacements.items():
            print(f"{old_url} -> {new_url}")
        print("Run again with --apply to convert the files and update Markdown references.")
        return

    created: list[Path] = []
    try:
        for index, source in enumerate(sources, 1):
            destination = source.with_suffix(".webp")
            if destination.exists():
                raise RuntimeError(f"Destination already exists: {destination}")
            convert_image(source, destination, args.max_dimension, args.quality)
            created.append(destination)
            print(f"[{index}/{len(sources)}] {source.relative_to(PROJECT_ROOT)} -> {destination.name}")
    except Exception:
        for destination in created:
            destination.unlink(missing_ok=True)
        raise

    changed_files = update_content(replacements)
    for source in sources:
        source.unlink()

    new_size = sum(destination.stat().st_size for destination in created)
    print(f"Updated {changed_files} Markdown files.")
    reduction = (1 - new_size / old_size) * 100
    print(
        f"Created {len(created)} WebP images: "
        f"{old_size / 1024 / 1024:.1f} MiB -> {new_size / 1024 / 1024:.1f} MiB "
        f"({reduction:.1f}% smaller)."
    )


if __name__ == "__main__":
    main()
