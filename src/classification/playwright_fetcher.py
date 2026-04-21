"""Fetch rendered HTML for a URL using Playwright.

Why Playwright and not `httpx.get`: modern local-business sites are often
SPA-ish (React, Next.js) or lazy-load chat widgets after the page is
otherwise interactive. Requests-style fetching gets the skeleton, not the
chat widget script tag the classifier needs to see.

Keeps one browser instance alive across many pages to amortize startup.
"""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from playwright.async_api import Browser, async_playwright


@dataclass
class FetchedPage:
    url: str
    html: str
    status: int


class PageFetcher:
    """Async context manager that keeps one browser hot across many fetches."""

    def __init__(self, *, headless: bool = True, timeout_ms: int = 15_000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser: Browser | None = None

    async def __aenter__(self) -> PageFetcher:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def fetch(self, url: str) -> FetchedPage | None:
        assert self._browser is not None
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            response = await page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            # Give chat widgets a chance to inject their script tags.
            await page.wait_for_timeout(1500)
            html = await page.content()
            status = response.status if response else 0
            return FetchedPage(url=url, html=html, status=status)
        except Exception as e:  # noqa: BLE001 — we want to log and move on, not explode.
            logger.warning(f"fetch failed for {url}: {e}")
            return None
        finally:
            await context.close()
