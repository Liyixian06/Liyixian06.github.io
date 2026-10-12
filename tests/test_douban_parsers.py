from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.sync_douban import (
    BlockedError,
    parse_book_page,
    parse_movie_credits,
    parse_movie_page,
)


FIXTURES = Path(__file__).parent / "fixtures"


class DoubanParserTests(unittest.TestCase):
    def fixture(self, name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    def test_book_format_matches_existing_csv(self) -> None:
        metadata = parse_book_page(
            self.fixture("book_subject.html"),
            "https://book.douban.com/subject/25697546/",
        )
        self.assertEqual(metadata.title, "尼罗河上的惨案")
        self.assertEqual(metadata.rating, "8.6")
        self.assertEqual(metadata.tags, "[英] 阿加莎·克里斯蒂 / 2013-9 / 新星出版社")
        self.assertEqual(metadata.summary, "第一段，包含逗号。 第二段包含“引号”。")
        self.assertEqual(
            metadata.image,
            "https://img3.doubanio.com/view/subject/l/public/s27027698.jpg",
        )

    def test_movie_format_matches_existing_csv(self) -> None:
        metadata = parse_movie_page(
            self.fixture("movie_subject.html"),
            "https://movie.douban.com/subject/1292052/",
            (["弗兰克·德拉邦特"], ["蒂姆·罗宾斯", "摩根·弗里曼"]),
        )
        self.assertEqual(metadata.title, "肖申克的救赎 The Shawshank Redemption")
        self.assertEqual(metadata.rating, "9.7")
        self.assertEqual(
            metadata.tags,
            "1994 / 美国 / 剧情 犯罪 / 弗兰克·德拉邦特 / 蒂姆·罗宾斯 摩根·弗里曼",
        )
        self.assertEqual(metadata.summary, "一场谋杀案使银行家安迪蒙冤入狱。 最终，他重获自由。")

    def test_movie_credits_use_douban_categories(self) -> None:
        payload = json.loads(
            """{
              "items": [
                {"name": "弗兰克·德拉邦特", "category": "导演"},
                {"name": "蒂姆·罗宾斯", "category": "演员"},
                {"name": "摩根·弗里曼", "category": "演员"},
                {"name": "蒂姆·罗宾斯", "category": "演员"},
                {"name": "罗杰·狄金斯", "category": "摄影"}
              ]
            }"""
        )
        directors, actors = parse_movie_credits(payload)
        self.assertEqual(directors, ["弗兰克·德拉邦特"])
        self.assertEqual(actors, ["蒂姆·罗宾斯", "摩根·弗里曼"])

    def test_security_check_is_rejected(self) -> None:
        with self.assertRaises(BlockedError):
            parse_book_page(
                self.fixture("blocked.html"),
                "https://book.douban.com/subject/1/",
            )
        with self.assertRaises(BlockedError):
            parse_movie_page(
                self.fixture("blocked.html"),
                "https://movie.douban.com/subject/1/",
            )


if __name__ == "__main__":
    unittest.main()
