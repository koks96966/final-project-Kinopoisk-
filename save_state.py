"""Сохранение сессии Кинопоиска в state.json.

Запускает браузер, ждёт, пока пользователь войдёт в аккаунт,
и сохраняет куки и localStorage в state.json для UI-тестов.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import config


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport=config.VIEWPORT)
        page = context.new_page()

        page.goto(config.SITE_URL, timeout=30000)

        input(
            ">>> Войдите в аккаунт в этом окне. Дождитесь аватара в шапке, "
            "затем вернитесь в терминал и нажмите Enter..."
        )

        context.storage_state(path=config.STATE_FILE)
        print(f"[OK] Сессия сохранена: {config.STATE_FILE}")

        browser.close()


if __name__ == "__main__":
    main()
