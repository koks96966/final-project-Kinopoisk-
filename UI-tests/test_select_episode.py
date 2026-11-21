import os
import allure
import pytest
from playwright.sync_api import sync_playwright, Page

from pages import FilmPage

STATE_FILE = "state.json"

# «Универ» (2008–2011): 4 сезона по ~46 эпизодов — предусловие
# «минимум 2 сезона по 5 серий» выполняется с запасом.
SERIES_URL = "https://www.kinopoisk.ru/series/421897/"


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
@allure.title("Выбрать серию при просмотре сериала")
def test_select_episode(page: Page):
    film = FilmPage(page)

    with allure.step("Предусловие: открыть страницу сериала с 2+ сезонами («Универ»)"):
        film.open_film(SERIES_URL)

    with allure.step("Кликнуть по обложке или названию сериала"):
        # Обложка на странице тайтла — постер-ссылка с data-test-id="next-link"
        poster = page.locator('a[data-test-id="next-link"]').first
        poster.click(timeout=5000, force=True)
        page.wait_for_load_state("domcontentloaded")

    with allure.step("Нажать кнопку «Смотреть сериал»"):
        film.start_watch()

    with allure.step("Навести курсор на «Сезоны и серии» — отображается панель с сериями"):
        film.hover_episodes_panel()

    with allure.step("Нажать «Все сезоны» — отображается панель с сезонами"):
        film.open_all_seasons()

    with allure.step("Нажать «2 сезон» — отображается панель серий 2 сезона"):
        film.select_season(2)

    with allure.step("Нажать «2 серия» — воспроизведение идёт со 2 сезона 2 серии"):
        film.select_episode(2)
        assert film.is_episode_open(2, 2), "Не открылся 2 сезон 2 серия"
        assert film.is_video_paused() is False, "Видео не воспроизводится после выбора серии"
