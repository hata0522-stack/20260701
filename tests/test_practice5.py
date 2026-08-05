from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LESSON_DIR = Path(__file__).resolve().parents[1] / "lesson10"
sys.path.insert(0, str(LESSON_DIR))

import practice5  # noqa: E402


class FakeResponse:
    status = 200


class FakeElement:
    def inner_text(self) -> str:
        return "測試主標題"


class FakePage:
    def __init__(self) -> None:
        self.url = "https://example.test/final"
        self.goto_args: tuple[str, str, int] | None = None

    def goto(self, url: str, wait_until: str, timeout: int) -> FakeResponse:
        self.goto_args = (url, wait_until, timeout)
        return FakeResponse()

    def title(self) -> str:
        return "測試頁面"

    def query_selector(self, selector: str) -> FakeElement | None:
        return FakeElement() if selector == "h1" else None

    def screenshot(self, path: Path, full_page: bool) -> None:
        self.screenshot_path = Path(path)
        self.full_page = full_page
        self.screenshot_path.write_bytes(b"fake-png")


class FakeBrowser:
    def __init__(self) -> None:
        self.page = FakePage()
        self.closed = False

    def new_page(self, viewport: dict[str, int]) -> FakePage:
        self.viewport = viewport
        return self.page

    def close(self) -> None:
        self.closed = True


class FakeBrowserType:
    def __init__(self, browser: FakeBrowser) -> None:
        self.browser = browser

    def launch(self, headless: bool) -> FakeBrowser:
        self.headless = headless
        return self.browser


class FakePlaywright:
    def __init__(self, browser: FakeBrowser) -> None:
        self.chromium = FakeBrowserType(browser)
        self.firefox = FakeBrowserType(browser)
        self.webkit = FakeBrowserType(browser)


class FakePlaywrightContext:
    def __init__(self, browser: FakeBrowser) -> None:
        self.playwright = FakePlaywright(browser)

    def __enter__(self) -> FakePlaywright:
        return self.playwright

    def __exit__(self, *args: object) -> None:
        return None


class ValidationTests(unittest.TestCase):
    def test_validate_url_accepts_http_and_trims_spaces(self) -> None:
        self.assertEqual(
            practice5.validate_url("  https://example.com/path  "),
            "https://example.com/path",
        )

    def test_validate_url_rejects_missing_scheme(self) -> None:
        with self.assertRaisesRegex(ValueError, "http://"):
            practice5.validate_url("example.com")

    def test_validate_timeout_rejects_non_numeric_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "整數毫秒"):
            practice5.validate_timeout("很久")


class CoreCheckTests(unittest.TestCase):
    def test_core_collects_page_data_and_screenshot(self) -> None:
        browser = FakeBrowser()
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                practice5,
                "sync_playwright",
                return_value=FakePlaywrightContext(browser),
            ):
                result = practice5.check_website_core(
                    "https://example.test/start",
                    browser_name="chromium",
                    headless=True,
                    timeout_ms=5000,
                    output_dir=temp_dir,
                )

            self.assertTrue(result.success)
            self.assertEqual(result.http_status, 200)
            self.assertEqual(result.page_title, "測試頁面")
            self.assertEqual(result.main_heading, "測試主標題")
            self.assertEqual(result.final_url, "https://example.test/final")
            self.assertTrue(Path(result.screenshot_path or "").exists())
            self.assertEqual(
                browser.page.goto_args,
                ("https://example.test/start", "domcontentloaded", 5000),
            )
            self.assertTrue(browser.closed)

    def test_core_returns_friendly_validation_error(self) -> None:
        result = practice5.check_website_core("not-a-url")

        self.assertFalse(result.success)
        self.assertIn("http://", result.error_message)


if __name__ == "__main__":
    unittest.main()
