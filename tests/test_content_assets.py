import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = PROJECT_ROOT / "content"
STATIC_ROOT = PROJECT_ROOT / "static"
MARKDOWN_IMAGE = re.compile(r"!\[[^]]*\]\((?P<target>/img/.+)\)\s*$")
SHORTCODE_IMAGE = re.compile(
    r'{{<\s+(?:photo|image-text)\s+[^>]*\bsrc="(?P<target>/img/[^"]+)"[^>]*>}}'
)
IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
JOURNAL_ROOT = STATIC_ROOT / "img" / "journal"
MAX_JOURNAL_IMAGE_BYTES = 1_500_000


def exact_path_problem(path: Path) -> str | None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        if not current.is_dir():
            return f"parent directory does not exist: {current}"

        entries = {entry.name for entry in current.iterdir()}
        if part not in entries:
            case_match = next((entry for entry in entries if entry.casefold() == part.casefold()), None)
            if case_match:
                return f"case mismatch: referenced {part!r}, actual name is {case_match!r}"
            return f"missing path component: {part!r}"
        current /= part

    if not current.is_file():
        return "path is not a file"
    return None


class ContentAssetTests(unittest.TestCase):
    def test_local_markdown_images_exist_with_exact_case(self):
        problems = []

        for markdown_file in sorted(CONTENT_ROOT.rglob("*.md")):
            for line_number, line in enumerate(markdown_file.read_text(encoding="utf-8").splitlines(), 1):
                matches = [*MARKDOWN_IMAGE.finditer(line), *SHORTCODE_IMAGE.finditer(line)]
                for match in matches:
                    target = match.group("target").split(maxsplit=1)[0]
                    url_path = unquote(urlsplit(target).path)
                    asset_path = STATIC_ROOT / url_path.removeprefix("/")
                    problem = exact_path_problem(asset_path)
                    if problem:
                        source = markdown_file.relative_to(PROJECT_ROOT)
                        problems.append(f"{source}:{line_number}: {target}: {problem}")

        self.assertFalse(problems, "Local image reference problems:\n" + "\n".join(problems))

    def test_image_extensions_are_lowercase(self):
        uppercase_extensions = [
            path.relative_to(PROJECT_ROOT)
            for path in STATIC_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and path.suffix != path.suffix.lower()
        ]

        self.assertFalse(
            uppercase_extensions,
            "Image extensions must be lowercase:\n" + "\n".join(map(str, uppercase_extensions)),
        )

    def test_journal_images_are_web_friendly(self):
        problems = []
        for path in sorted(JOURNAL_ROOT.rglob("*")):
            if not path.is_file() or path.name == ".DS_Store":
                continue
            relative_path = path.relative_to(PROJECT_ROOT)
            if path.suffix.lower() not in {".png", ".webp"}:
                problems.append(f"{relative_path}: journal photos must be WebP")
            if path.stat().st_size > MAX_JOURNAL_IMAGE_BYTES:
                size_mib = path.stat().st_size / 1024 / 1024
                problems.append(f"{relative_path}: {size_mib:.1f} MiB exceeds the 1.5 MB limit")

        self.assertFalse(problems, "Journal image optimization problems:\n" + "\n".join(problems))
