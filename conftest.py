"""Общие фикстуры и хелперы проекта.

UI: фикстура page — Playwright-браузер с авторизацией из state.json
    и разрешением 1920x1080.
API: хелпер api_get — GET-запрос к Кинопоиск API с токеном из .env.
"""
import sys
from pathlib import Path
from typing import Generator

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pytest
import requests
from playwright.sync_api import sync_playwright, Page

import config

STATE_FILE = ROOT / "state.json"
VIEWPORT = {"width": 1920, "height": 1080}


# ---------- API ----------

def api_get(path: str, params: dict | None = None) -> requests.Response:
    """GET-запрос к Кинопоиск API с авторизационным заголовком.

    Возвращает объект requests.Response — статус и тело разбирает тест.
    """
    headers = {
        "X-API-KEY": config.API_TOKEN,
        "accept": "application/json",
    }
    return requests.get(
        f"{config.BASE_URL}{path}",
        headers=headers,
        params=params,
        timeout=config.REQUEST_TIMEOUT,
    )


# ---------- UI ----------

@pytest.fixture
def page() -> Generator[Page, None, None]:
    print(f"\n[conftest] state.json: {STATE_FILE} | существует: {STATE_FILE.exists()}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        kwargs = {"viewport": VIEWPORT}
        if STATE_FILE.exists():
            kwargs["storage_state"] = str(STATE_FILE)
        context = browser.new_context(**kwargs)
        yield context.new_page()
        context.close()
        browser.close()
