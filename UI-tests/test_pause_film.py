import os
import allure
import pytest
from playwright.sync_api import sync_playwright, Page

from pages import FilmPage

STATE_FILE = "state.json"


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=STATE_FILE if os.path.exists(STATE_FILE) else None,
            viewport={"width": 1920, "height": 1080},
        )
        page: Page = context.new_page()
        yield page
        browser.close()


@pytest.mark.ui
@allure.feature("Плеер")
@allure.story("Управление воспроизведением")
@allure.title("Работоспособность паузы фильма")
def test_pause_film(page: Page):
    film = FilmPage(page)

    with allure.step("Открыть главную и кликнуть по любой карточке тайтла"):
        film.open_first_card()
        assert film.current_href in page.url, "Не открылась страница тайтла"

    with allure.step("Нажать кнопку «Смотреть»"):
        film.start_watch()

    with allure.step("Клик по экрану — воспроизведение остановлено"):
        film.pause_player()
        assert film.is_video_paused() is True, (
            "После клика воспроизведение не остановилось"
        )

    with allure.step("Повторный клик — воспроизведение продолжается"):
        film.resume_player()
        assert film.is_video_paused() is False, (
            "После второго клика воспроизведение не возобновилось"
        )
