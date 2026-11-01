import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.optimize_journal_images import normalize_image_for_encoding


class OptimizeJournalImageTests(unittest.TestCase):
    def test_exif_orientation_is_applied_before_encoding(self):
        with tempfile.TemporaryDirectory() as temporary_directory_name:
            temporary_directory = Path(temporary_directory_name)
            source = temporary_directory / "rotated.jpg"
            image = Image.new("RGB", (4, 2), "red")
            exif = Image.Exif()
            exif[274] = 6
            image.save(source, exif=exif)

            normalized_path, width, height = normalize_image_for_encoding(source, temporary_directory)

            self.assertNotEqual(normalized_path, source)
            self.assertEqual((width, height), (2, 4))
            with Image.open(normalized_path) as normalized:
                self.assertEqual(normalized.size, (2, 4))
                self.assertEqual(normalized.getexif().get(274, 1), 1)


if __name__ == "__main__":
    unittest.main()
