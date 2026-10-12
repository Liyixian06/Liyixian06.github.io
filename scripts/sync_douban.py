#!/usr/bin/env python3
"""Fill new Douban card CSV rows from Douban subject pages."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup, Tag


CSV_FIELDS = ("title", "rating", "tags", "image", "url", "summary")
TEXT_FIELDS = ("title", "rating", "tags", "summary")
SUBJECT_URL_RE = re.compile(
    r"^https?://(?P<kind>book|movie)\.douban\.com/subject/(?P<id>\d+)/?(?:[?#].*)?$",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"[（(](\d{4})[）)]\s*$")
BLOCKED_MARKERS = (
    "sec.douban.com",
    "检测到有异常请求",
    "异常请求",
    "访问豆瓣的方式有点不太像人类",
    "captcha",
)
BOOK_HOST = "book.douban.com"
MOVIE_HOSTS = {"movie.douban.com", "m.douban.com"}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1"
)
ProgressCallback = Callable[[str], None]


def _no_progress(message: str) -> None:
    """Discard progress messages when the caller did not request logging."""


def print_progress(message: str) -> None:
    """Print a timestamped progress message immediately."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


class SyncError(Exception):
    """Base class for errors that should be reported without a traceback."""


class CsvValidationError(SyncError):
    """The local CSV cannot be processed safely."""


class FetchError(SyncError):
    """A remote page could not be fetched."""


class BlockedError(FetchError):
    """Douban returned a rate limit or security check."""


class NotFoundError(FetchError):
    """The requested subject does not exist."""


class ParseError(SyncError):
    """A response did not contain a valid subject page."""


@dataclass(frozen=True)
class SubjectRef:
    kind: str
    subject_id: str
    url: str


@dataclass(frozen=True)
class Metadata:
    title: str
    rating: str
    tags: str
    image: str
    url: str
    summary: str


@dataclass
class CsvScan:
    path: Path
    kind: str
    rows: list[dict[str, str]]
    pending: list[tuple[int, SubjectRef]]
    complete: int
    partial: list[int]
    invalid: list[tuple[int, str]]


@dataclass
class FileResult:
    path: Path
    updated: int = 0
    skipped: int = 0
    failed: list[tuple[SubjectRef, str, str]] | None = None
    warnings: list[tuple[SubjectRef, str]] | None = None

    def __post_init__(self) -> None:
        if self.failed is None:
            self.failed = []
        if self.warnings is None:
            self.warnings = []


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def strip_latin_aliases(value: str) -> str:
    def replace_alias(match: re.Match[str]) -> str:
        content = match.group(1)
        return "" if re.search(r"[A-Za-z]", content) else match.group(0)

    return clean_text(re.sub(r"\s*[（(]([^()（）]*)[）)]", replace_alias, value))


def normalize_subject_url(value: str) -> SubjectRef:
    raw = value.strip()
    match = SUBJECT_URL_RE.fullmatch(raw)
    if not match:
        raise ValueError("expected https://book|movie.douban.com/subject/<numeric-id>/")
    kind = match.group("kind").lower()
    subject_id = match.group("id")
    return SubjectRef(
        kind=kind,
        subject_id=subject_id,
        url=f"https://{kind}.douban.com/subject/{subject_id}/",
    )


def read_csv(path: Path, expected_kind: str) -> CsvScan:
    try:
        handle = path.open("r", encoding="utf-8", newline="")
    except OSError as exc:
        raise CsvValidationError(f"cannot open {path}: {exc}") from exc

    with handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise CsvValidationError(
                f"{path}: expected header {','.join(CSV_FIELDS)}, got {reader.fieldnames}"
            )
        rows: list[dict[str, str]] = []
        pending: list[tuple[int, SubjectRef]] = []
        partial: list[int] = []
        invalid: list[tuple[int, str]] = []
        complete = 0
        seen: dict[str, int] = {}

        for row_index, raw_row in enumerate(reader, start=2):
            if None in raw_row or any(value is None for value in raw_row.values()):
                raise CsvValidationError(f"{path}:{row_index}: malformed CSV row")
            row = {field: raw_row[field] for field in CSV_FIELDS}
            rows.append(row)
            if not any(value.strip() for value in row.values()):
                invalid.append((row_index, "empty row"))
                continue
            try:
                subject = normalize_subject_url(row["url"])
            except ValueError as exc:
                invalid.append((row_index, str(exc)))
                continue
            if subject.kind != expected_kind:
                invalid.append(
                    (row_index, f"{subject.kind} URL is not allowed in {expected_kind}.csv")
                )
                continue
            if subject.url in seen:
                invalid.append(
                    (row_index, f"duplicate URL; first occurrence is line {seen[subject.url]}")
                )
                continue
            seen[subject.url] = row_index

            filled = [bool(row[field].strip()) for field in TEXT_FIELDS]
            if not any(filled):
                pending.append((len(rows) - 1, subject))
            elif all(filled):
                complete += 1
            else:
                partial.append(row_index)

    return CsvScan(path, expected_kind, rows, pending, complete, partial, invalid)


def _looks_blocked(html: str) -> bool:
    lowered = html.lower()
    return any(marker.lower() in lowered for marker in BLOCKED_MARKERS)


def _required_text(node: Tag | None, field: str) -> str:
    value = clean_text(node.get_text(" ", strip=True)) if node else ""
    if not value:
        raise ParseError(f"missing {field}")
    return value


def _book_info_value(info: Tag, label_name: str) -> str:
    for label in info.select(".pl"):
        normalized_label = clean_text(label.get_text(" ", strip=True)).rstrip(":：")
        if normalized_label != label_name:
            continue
        if label.parent is not info:
            container_text = clean_text(label.parent.get_text(" ", strip=True))
            return clean_text(
                re.sub(rf"^\s*{re.escape(normalized_label)}\s*[:：]?\s*", "", container_text)
            )
        values: list[str] = []
        for sibling in label.next_siblings:
            if isinstance(sibling, Tag) and sibling.name == "br":
                break
            text = sibling.get_text(" ", strip=True) if isinstance(sibling, Tag) else str(sibling)
            if clean_text(text):
                values.append(clean_text(text))
        return clean_text(" ".join(values).lstrip(":："))
    return ""


def parse_book_page(html: str, canonical_url: str) -> Metadata:
    if _looks_blocked(html):
        raise BlockedError("Douban returned a security check")
    soup = BeautifulSoup(html, "html.parser")
    title = _required_text(
        soup.select_one('h1 [property="v:itemreviewed"]') or soup.select_one("h1.title"),
        "book title",
    )
    rating_node = soup.select_one('[property="v:average"]')
    rating = clean_text(rating_node.get_text()) if rating_node else "N/A"
    if rating != "N/A" and not re.fullmatch(r"\d+(?:\.\d+)?", rating):
        raise ParseError(f"invalid rating {rating!r}")

    info = soup.select_one("#info")
    if not isinstance(info, Tag):
        raise ParseError("missing book info")
    author = strip_latin_aliases(_book_info_value(info, "作者"))
    pub_year = _book_info_value(info, "出版年")
    publisher = _book_info_value(info, "出版社")
    tag_parts = [part for part in (author, pub_year, publisher) if part]
    if not tag_parts:
        raise ParseError("missing book author, publication year, and publisher")

    intro = soup.select_one("#link-report .intro")
    if not isinstance(intro, Tag):
        raise ParseError("missing book summary")
    paragraphs = [clean_text(node.get_text(" ", strip=True)) for node in intro.select("p")]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    summary = " ".join(paragraphs) or clean_text(intro.get_text(" ", strip=True))
    if not summary:
        raise ParseError("empty book summary")

    cover = soup.select_one("#mainpic a.nbg")
    image = clean_text(str(cover.get("href", ""))) if isinstance(cover, Tag) else ""
    return Metadata(title, rating, " / ".join(tag_parts), image, canonical_url, summary)


def parse_movie_credits(payload: object) -> tuple[list[str], list[str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ParseError("invalid movie credits response")
    directors: list[str] = []
    actors: list[str] = []
    for item in payload["items"]:
        if not isinstance(item, dict):
            continue
        name = clean_text(str(item.get("name", "")))
        category = clean_text(str(item.get("category", "")))
        if not name:
            continue
        if category == "导演" and name not in directors:
            directors.append(name)
        elif category == "演员" and name not in actors:
            actors.append(name)
    return directors, actors


def parse_movie_page(
    html: str,
    canonical_url: str,
    credits: tuple[Sequence[str], Sequence[str]] | None = None,
) -> Metadata:
    if _looks_blocked(html):
        raise BlockedError("Douban returned a security check")
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one(".subject-header-wrap .sub-title")
    title = _required_text(title_node, "movie title")

    rating_node = soup.select_one('meta[itemprop="ratingValue"]')
    rating = clean_text(str(rating_node.get("content", ""))) if rating_node else "N/A"
    if rating != "N/A" and not re.fullmatch(r"\d+(?:\.\d+)?", rating):
        raise ParseError(f"invalid rating {rating!r}")

    original_title_node = soup.select_one(".subject-header-wrap .sub-original-title")
    original_title = clean_text(original_title_node.get_text(" ", strip=True)) if original_title_node else ""
    year_match = YEAR_RE.search(original_title)
    year = year_match.group(1) if year_match else ""
    original_title = clean_text(YEAR_RE.sub("", original_title))
    if original_title and original_title.casefold() != title.casefold():
        title = f"{title} {original_title}"

    meta_node = soup.select_one(".subject-header-wrap .sub-meta")
    meta = clean_text(meta_node.get_text(" ", strip=True)) if meta_node else ""
    meta_parts = [clean_text(part) for part in meta.split("/")]
    subject_parts = [
        part
        for part in meta_parts
        if part
        and "上映" not in part
        and not part.startswith("片长")
        and not part.startswith("集数")
    ]
    region = subject_parts[0] if subject_parts else ""
    genres = " ".join(subject_parts[1:])
    directors, actors = credits or ((), ())
    tag_parts = [
        part
        for part in (
            year,
            region,
            genres,
            " ".join(directors),
            " ".join(list(actors)[:5]),
        )
        if part
    ]
    if not tag_parts:
        raise ParseError("missing movie year, region, and genre")

    intro = soup.select_one(".subject-intro .bd p")
    summary = _required_text(intro, "movie summary")
    cover = soup.select_one(".subject-header-wrap .sub-cover img")
    image = clean_text(str(cover.get("src", ""))) if isinstance(cover, Tag) else ""
    return Metadata(title, rating, " / ".join(tag_parts), image, canonical_url, summary)


class DoubanClient:
    def __init__(
        self,
        delay: float = 3.0,
        timeout: tuple[float, float] = (10.0, 30.0),
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        progress: ProgressCallback = _no_progress,
    ) -> None:
        self.delay = max(0.0, delay)
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        self.sleep = sleep
        self.clock = clock
        self.progress = progress
        self._last_request_at: float | None = None

    def _wait(self) -> None:
        if self._last_request_at is None:
            return
        remaining = self.delay - (self.clock() - self._last_request_at)
        if remaining > 0:
            self.progress(f"Waiting {remaining:.1f}s before the next Douban request")
            self.sleep(remaining)

    def fetch_subject(self, subject: SubjectRef) -> str:
        self._wait()
        target = (
            subject.url
            if subject.kind == "book"
            else f"https://m.douban.com/movie/subject/{subject.subject_id}/"
        )
        headers = (
            {"User-Agent": MOBILE_USER_AGENT, "Referer": "https://m.douban.com/"}
            if subject.kind == "movie"
            else None
        )
        last_error: Exception | None = None
        for attempt in range(2):
            self.progress(
                f"Fetching Douban {subject.kind}:{subject.subject_id}"
                + (f" (attempt {attempt + 1}/2)" if attempt else "")
            )
            try:
                response = self.session.get(
                    target,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                self._last_request_at = self.clock()
            except requests.RequestException as exc:
                last_error = exc
                if attempt == 0:
                    self.progress("Douban request failed; retrying in 1.0s")
                    self.sleep(1.0)
                    continue
                raise FetchError(f"network error: {exc}") from exc

            final_host = (urlsplit(response.url).hostname or "").lower()
            if final_host == "sec.douban.com" or _looks_blocked(response.text):
                raise BlockedError("redirected to Douban security check")
            if response.status_code == 404:
                raise NotFoundError("Douban subject not found")
            if response.status_code in (403, 418, 429):
                raise BlockedError(f"Douban returned HTTP {response.status_code}")
            if response.status_code >= 500 and attempt == 0:
                self.progress(
                    f"Douban returned HTTP {response.status_code}; retrying in 1.0s"
                )
                self.sleep(1.0)
                continue
            if response.status_code != 200:
                raise FetchError(f"Douban returned HTTP {response.status_code}")

            allowed_hosts = {BOOK_HOST} if subject.kind == "book" else MOVIE_HOSTS
            if final_host not in allowed_hosts:
                raise FetchError(f"unexpected redirect to {final_host or 'an unknown host'}")
            return response.text

        raise FetchError(f"network error: {last_error or 'unknown failure'}")

    def fetch_movie_credits(self, subject: SubjectRef) -> tuple[list[str], list[str]]:
        if subject.kind != "movie":
            return [], []
        self._wait()
        self.progress(f"Fetching Douban credits for movie:{subject.subject_id}")
        target = (
            f"https://m.douban.com/rexxar/api/v2/movie/"
            f"{subject.subject_id}/credits"
        )
        headers = {
            "Accept": "application/json",
            "Referer": f"https://m.douban.com/movie/subject/{subject.subject_id}/",
            "User-Agent": MOBILE_USER_AGENT,
        }
        try:
            response = self.session.get(
                target,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            self._last_request_at = self.clock()
        except requests.RequestException as exc:
            raise FetchError(f"movie credits network error: {exc}") from exc
        if response.status_code in (403, 418, 429):
            raise BlockedError(f"Douban credits returned HTTP {response.status_code}")
        if response.status_code != 200:
            raise FetchError(f"Douban credits returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ParseError("Douban credits returned invalid JSON") from exc
        return parse_movie_credits(payload)


class NeoDBClient:
    endpoint = "https://neodb.social/api/catalog/fetch"

    def __init__(
        self,
        timeout: tuple[float, float] = (10.0, 30.0),
        poll_interval: float = 15.0,
        max_wait: float = 120.0,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        progress: ProgressCallback = _no_progress,
    ) -> None:
        self.timeout = timeout
        self.poll_interval = max(0.0, poll_interval)
        self.max_wait = max(0.0, max_wait)
        self.session = session or requests.Session()
        self.session.headers.update(
            {"User-Agent": DEFAULT_USER_AGENT, "Accept": "application/json"}
        )
        self.sleep = sleep
        self.progress = progress

    def fetch_cover(self, subject_url: str) -> str | None:
        waited = 0.0
        subject_id = urlsplit(subject_url).path.rstrip("/").split("/")[-1]
        self.progress(f"Looking up NeoDB cover for subject:{subject_id}")
        while True:
            try:
                response = self.session.get(
                    self.endpoint,
                    params={"url": subject_url},
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                raise FetchError(f"NeoDB network error: {exc}") from exc
            if response.status_code == 202:
                if waited + self.poll_interval > self.max_wait:
                    self.progress(
                        f"NeoDB cover lookup timed out after {waited:.0f}s for subject:{subject_id}"
                    )
                    return None
                self.progress(
                    f"NeoDB is still processing subject:{subject_id}; "
                    f"waiting {self.poll_interval:.0f}s (elapsed {waited:.0f}s)"
                )
                self.sleep(self.poll_interval)
                waited += self.poll_interval
                continue
            if response.status_code in (404, 422):
                return None
            if response.status_code == 429:
                raise FetchError("NeoDB rate limited the request")
            if response.status_code != 200:
                raise FetchError(f"NeoDB returned HTTP {response.status_code}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise FetchError("NeoDB returned invalid JSON") from exc
            cover = payload.get("cover_image_url")
            return clean_text(cover) if isinstance(cover, str) and cover.strip() else None


def merge_metadata(
    original: dict[str, str], metadata: Metadata, remote_cover: str | None
) -> dict[str, str]:
    return {
        "title": metadata.title,
        "rating": metadata.rating,
        "tags": metadata.tags,
        "image": original["image"].strip() or remote_cover or metadata.image,
        "url": metadata.url,
        "summary": metadata.summary,
    }


def is_douban_image(url: str) -> bool:
    host = (urlsplit(url.strip()).hostname or "").lower()
    return host == "doubanio.com" or host.endswith(".doubanio.com")


def write_csv_atomic(path: Path, kind: str, rows: Sequence[dict[str, str]]) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            writer = csv.DictWriter(
                handle,
                fieldnames=CSV_FIELDS,
                extrasaction="raise",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())

        verification = read_csv(temp_path, kind)
        if len(verification.rows) != len(rows):
            raise CsvValidationError(f"temporary CSV row count changed for {path}")
        os.replace(temp_path, path)
        temp_path = None
    except (OSError, csv.Error) as exc:
        raise CsvValidationError(f"cannot safely write {path}: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def sync_scan(
    scan: CsvScan,
    douban: DoubanClient,
    neodb: NeoDBClient,
    progress: ProgressCallback = _no_progress,
) -> FileResult:
    result = FileResult(scan.path, skipped=scan.complete + len(scan.partial))
    total = len(scan.pending)
    progress(
        f"{scan.path.name}: found {total} pending, {scan.complete} complete, "
        f"{len(scan.partial)} partial, {len(scan.invalid)} invalid"
    )
    for item_number, (row_index, subject) in enumerate(scan.pending, start=1):
        label = f"{scan.path.name} [{item_number}/{total}] {subject.kind}:{subject.subject_id}"
        progress(f"{label}: starting")
        try:
            html = douban.fetch_subject(subject)
            progress(f"{label}: parsing Douban metadata")
            if subject.kind == "book":
                metadata = parse_book_page(html, subject.url)
            else:
                credits = douban.fetch_movie_credits(subject)
                metadata = parse_movie_page(html, subject.url, credits)
        except BlockedError as exc:
            result.failed.append((subject, "blocked", str(exc)))
            progress(f"{label}: failed (blocked: {exc})")
            continue
        except NotFoundError as exc:
            result.failed.append((subject, "not_found", str(exc)))
            progress(f"{label}: failed (not found: {exc})")
            continue
        except ParseError as exc:
            result.failed.append((subject, "parse_error", str(exc)))
            progress(f"{label}: failed (parse error: {exc})")
            continue
        except FetchError as exc:
            result.failed.append((subject, "network_error", str(exc)))
            progress(f"{label}: failed (network error: {exc})")
            continue

        remote_cover: str | None = None
        if not scan.rows[row_index]["image"].strip():
            try:
                remote_cover = neodb.fetch_cover(subject.url)
            except FetchError as exc:
                result.warnings.append((subject, str(exc)))
                progress(f"{label}: cover warning ({exc})")
        scan.rows[row_index] = merge_metadata(scan.rows[row_index], metadata, remote_cover)
        if not scan.rows[row_index]["image"]:
            result.warnings.append((subject, "no remote cover found"))
            progress(f"{label}: no cover found; saving metadata without an image")
        result.updated += 1
        progress(f"{label}: ready ({metadata.title})")

    if result.updated:
        progress(f"{scan.path.name}: writing {result.updated} update(s) atomically")
        write_csv_atomic(scan.path, scan.kind, scan.rows)
        progress(f"{scan.path.name}: write complete")
    elif not total:
        progress(f"{scan.path.name}: nothing to update")
    return result


def replace_douban_images(
    scan: CsvScan,
    neodb: NeoDBClient,
    delay: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    progress: ProgressCallback = _no_progress,
) -> FileResult:
    candidates: list[tuple[int, SubjectRef]] = []
    for row_index, row in enumerate(scan.rows):
        if not is_douban_image(row["image"]):
            continue
        try:
            subject = normalize_subject_url(row["url"])
        except ValueError as exc:
            placeholder = SubjectRef(scan.kind, "unknown", row["url"])
            candidates.append((row_index, placeholder))
            continue
        candidates.append((row_index, subject))

    result = FileResult(scan.path, skipped=len(scan.rows) - len(candidates))
    total = len(candidates)
    progress(f"{scan.path.name}: found {total} Douban image(s) to replace")
    for candidate_number, (row_index, subject) in enumerate(candidates):
        label = (
            f"{scan.path.name} [{candidate_number + 1}/{total}] "
            f"{subject.kind}:{subject.subject_id}"
        )
        if candidate_number and delay > 0:
            progress(f"{label}: waiting {delay:.1f}s before lookup")
            sleep(delay)
        if subject.subject_id == "unknown":
            result.failed.append((subject, "invalid", "invalid Douban subject URL"))
            progress(f"{label}: failed (invalid Douban subject URL)")
            continue
        progress(f"{label}: looking up replacement cover")
        try:
            cover = neodb.fetch_cover(subject.url)
        except FetchError as exc:
            result.failed.append((subject, "cover_error", str(exc)))
            progress(f"{label}: failed ({exc})")
            continue
        if not cover:
            result.failed.append((subject, "cover_error", "NeoDB has no cover"))
            progress(f"{label}: failed (NeoDB has no cover)")
            continue
        if is_douban_image(cover):
            result.failed.append(
                (subject, "cover_error", "NeoDB returned another Douban image URL")
            )
            progress(f"{label}: failed (NeoDB returned a Douban image URL)")
            continue
        scan.rows[row_index]["image"] = cover
        result.updated += 1
        progress(f"{label}: replacement ready")

    if result.updated:
        progress(f"{scan.path.name}: writing {result.updated} replacement(s) atomically")
        write_csv_atomic(scan.path, scan.kind, scan.rows)
        progress(f"{scan.path.name}: write complete")
    elif not total:
        progress(f"{scan.path.name}: nothing to replace")
    return result


def _print_scan(scan: CsvScan) -> None:
    print(
        f"{scan.path.name}: {len(scan.pending)} pending, {scan.complete} complete, "
        f"{len(scan.partial)} partial, {len(scan.invalid)} invalid"
    )
    for _, subject in scan.pending:
        print(f"  pending: {subject.kind}:{subject.subject_id} {subject.url}")
    for line in scan.partial:
        print(f"  partial: line {line} (left unchanged)")
    for line, reason in scan.invalid:
        print(f"  invalid: line {line}: {reason}")


def _print_image_scan(scan: CsvScan) -> None:
    candidates = [row for row in scan.rows if is_douban_image(row["image"])]
    print(
        f"{scan.path.name}: {len(candidates)} Douban images to replace, "
        f"{len(scan.rows) - len(candidates)} unchanged"
    )


def _print_result(result: FileResult) -> None:
    print(
        f"{result.path.name}: {result.updated} updated, {result.skipped} skipped, "
        f"{len(result.failed)} failed"
    )
    for subject, message in result.warnings:
        print(f"  warning: {subject.kind}:{subject.subject_id}: {message}")
    for subject, status, message in result.failed:
        print(f"  {status}: {subject.kind}:{subject.subject_id}: {message}")


def build_parser() -> argparse.ArgumentParser:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Fill blank Douban card CSV rows from low-frequency subject requests."
    )
    parser.add_argument("--dry-run", action="store_true", help="scan only; do not use the network or write files")
    parser.add_argument("--type", choices=("book", "movie"), help="process only one CSV")
    parser.add_argument("--delay", type=float, default=3.0, help="minimum seconds between Douban requests (default: 3)")
    parser.add_argument(
        "--replace-douban-images",
        action="store_true",
        help="replace existing *.doubanio.com image URLs with NeoDB covers",
    )
    parser.add_argument(
        "--book-file",
        type=Path,
        default=repo_root / "assets/douban/book.csv",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--movie-file",
        type=Path,
        default=repo_root / "assets/douban/movie.csv",
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.delay < 0:
        print("error: --delay must not be negative", file=sys.stderr)
        return 2
    targets: Iterable[tuple[str, Path]] = (
        ((args.type, args.book_file if args.type == "book" else args.movie_file),)
        if args.type
        else (("book", args.book_file), ("movie", args.movie_file))
    )
    try:
        scans = [read_csv(path, kind) for kind, path in targets]
    except CsvValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        for scan in scans:
            if args.replace_douban_images:
                _print_image_scan(scan)
            else:
                _print_scan(scan)
        return 0

    print_progress("Starting Douban CSV sync")
    douban = DoubanClient(delay=args.delay, progress=print_progress)
    neodb = NeoDBClient(progress=print_progress)
    results: list[FileResult] = []
    try:
        for scan in scans:
            if args.replace_douban_images:
                results.append(
                    replace_douban_images(
                        scan, neodb, args.delay, progress=print_progress
                    )
                )
            else:
                results.append(sync_scan(scan, douban, neodb, progress=print_progress))
    except CsvValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for result in results:
        _print_result(result)
    return 1 if any(result.failed for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
