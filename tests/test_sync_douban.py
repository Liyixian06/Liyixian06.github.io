from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.sync_douban import (
    CsvValidationError,
    DoubanClient,
    NeoDBClient,
    SubjectRef,
    normalize_subject_url,
    read_csv,
    replace_douban_images,
    sync_scan,
)


FIXTURES = Path(__file__).parent / "fixtures"
FIELDS = ("title", "rating", "tags", "image", "url", "summary")


class FakeDoubanClient:
    def fetch_subject(self, subject: SubjectRef) -> str:
        fixture = "book_subject.html" if subject.kind == "book" else "movie_subject.html"
        return (FIXTURES / fixture).read_text(encoding="utf-8")

    def fetch_movie_credits(self, subject: SubjectRef) -> tuple[list[str], list[str]]:
        return ["弗兰克·德拉邦特"], ["蒂姆·罗宾斯", "摩根·弗里曼"]


class FakeNeoDBClient:
    def fetch_cover(self, subject_url: str) -> str:
        return "https://neodb.social/m/test/cover.jpg"


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        *,
        url: str = "https://neodb.social/api/book/id",
        text: str = "",
        payload: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.text = text
        self._payload = payload

    def json(self) -> object:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class SequenceSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.headers: dict[str, str] = {}
        self.calls = 0

    def get(self, *args: object, **kwargs: object) -> FakeResponse:
        response = self.responses[self.calls]
        self.calls += 1
        return response


class CsvSyncTests(unittest.TestCase):
    def write_rows(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_normalize_subject_url(self) -> None:
        subject = normalize_subject_url("http://book.douban.com/subject/12345")
        self.assertEqual(subject.kind, "book")
        self.assertEqual(subject.subject_id, "12345")
        self.assertEqual(subject.url, "https://book.douban.com/subject/12345/")
        with self.assertRaises(ValueError):
            normalize_subject_url("https://example.com/subject/12345/")

    def test_scan_classifies_rows_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            self.write_rows(
                path,
                [
                    {
                        "title": "",
                        "rating": "",
                        "tags": "",
                        "image": "",
                        "url": "https://book.douban.com/subject/12345/",
                        "summary": "",
                    },
                    {
                        "title": "完整",
                        "rating": "8.0",
                        "tags": "作者 / 2026 / 出版社",
                        "image": "",
                        "url": "https://book.douban.com/subject/23456/",
                        "summary": "简介",
                    },
                    {
                        "title": "部分",
                        "rating": "",
                        "tags": "",
                        "image": "",
                        "url": "https://book.douban.com/subject/34567/",
                        "summary": "",
                    },
                ],
            )
            scan = read_csv(path, "book")
            self.assertEqual(len(scan.pending), 1)
            self.assertEqual(scan.complete, 1)
            self.assertEqual(scan.partial, [4])
            self.assertEqual(scan.invalid, [])

    def test_wrong_csv_header_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            path.write_text("url,title\nhttps://book.douban.com/subject/1/,x\n", encoding="utf-8")
            with self.assertRaises(CsvValidationError):
                read_csv(path, "book")

    def test_sync_writes_expected_format_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            self.write_rows(
                path,
                [
                    {
                        "title": "",
                        "rating": "",
                        "tags": "",
                        "image": "",
                        "url": "https://book.douban.com/subject/25697546/",
                        "summary": "",
                    }
                ],
            )
            result = sync_scan(read_csv(path, "book"), FakeDoubanClient(), FakeNeoDBClient())
            self.assertEqual(result.updated, 1)
            first_bytes = path.read_bytes()
            with path.open(encoding="utf-8", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["title"], "尼罗河上的惨案")
            self.assertEqual(row["rating"], "8.6")
            self.assertEqual(row["tags"], "[英] 阿加莎·克里斯蒂 / 2013-9 / 新星出版社")
            self.assertEqual(row["image"], "https://neodb.social/m/test/cover.jpg")
            second = sync_scan(read_csv(path, "book"), FakeDoubanClient(), FakeNeoDBClient())
            self.assertEqual(second.updated, 0)
            self.assertEqual(path.read_bytes(), first_bytes)

    def test_sync_reports_item_and_write_progress(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            self.write_rows(
                path,
                [
                    {
                        "title": "",
                        "rating": "",
                        "tags": "",
                        "image": "",
                        "url": "https://book.douban.com/subject/25697546/",
                        "summary": "",
                    }
                ],
            )
            messages: list[str] = []
            sync_scan(
                read_csv(path, "book"),
                FakeDoubanClient(),
                FakeNeoDBClient(),
                progress=messages.append,
            )
            self.assertTrue(any("[1/1]" in message for message in messages))
            self.assertTrue(any("parsing Douban metadata" in message for message in messages))
            self.assertTrue(any("write complete" in message for message in messages))

    def test_existing_manual_cover_wins(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            self.write_rows(
                path,
                [
                    {
                        "title": "",
                        "rating": "",
                        "tags": "",
                        "image": "https://example.com/manual.jpg",
                        "url": "https://book.douban.com/subject/25697546/",
                        "summary": "",
                    }
                ],
            )
            sync_scan(read_csv(path, "book"), FakeDoubanClient(), FakeNeoDBClient())
            with path.open(encoding="utf-8", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["image"], "https://example.com/manual.jpg")

    def test_replace_douban_images_changes_only_the_cover(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.csv"
            original = {
                "title": "完整条目",
                "rating": "8.8",
                "tags": "作者 / 2026 / 出版社",
                "image": "https://img3.doubanio.com/view/subject/l/public/example.jpg",
                "url": "https://book.douban.com/subject/12345/",
                "summary": "简介",
            }
            untouched = {
                "title": "远程封面",
                "rating": "8.0",
                "tags": "作者 / 2025 / 出版社",
                "image": "https://neodb.social/m/existing.jpg",
                "url": "https://book.douban.com/subject/23456/",
                "summary": "另一条简介",
            }
            self.write_rows(path, [original, untouched])
            result = replace_douban_images(
                read_csv(path, "book"),
                FakeNeoDBClient(),
                delay=0,
            )
            self.assertEqual(result.updated, 1)
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(
                rows[0],
                {**original, "image": "https://neodb.social/m/test/cover.jpg"},
            )
            self.assertEqual(rows[1], untouched)

    def test_neodb_polls_accepted_response(self) -> None:
        session = SequenceSession(
            [
                FakeResponse(202),
                FakeResponse(200, payload={"cover_image_url": "https://neodb.social/m/cover.jpg"}),
            ]
        )
        sleeps: list[float] = []
        messages: list[str] = []
        client = NeoDBClient(
            session=session,
            poll_interval=0.25,
            max_wait=1.0,
            sleep=sleeps.append,
            progress=messages.append,
        )
        self.assertEqual(
            client.fetch_cover("https://book.douban.com/subject/1/"),
            "https://neodb.social/m/cover.jpg",
        )
        self.assertEqual(sleeps, [0.25])
        self.assertTrue(any("still processing" in message for message in messages))

    def test_douban_security_redirect_is_rejected(self) -> None:
        session = SequenceSession(
            [FakeResponse(200, url="https://sec.douban.com/c", text="security")]
        )
        client = DoubanClient(session=session, delay=0)
        with self.assertRaises(Exception) as context:
            client.fetch_subject(
                SubjectRef("movie", "1292052", "https://movie.douban.com/subject/1292052/")
            )
        self.assertIn("security", str(context.exception).lower())


if __name__ == "__main__":
    unittest.main()
