import allure
import pytest
from playwright.sync_api import Page, expect

from pages import SearchPage


@pytest.mark.ui
@allure.feature("Поиск")
@allure.story("Поиск сериала по ключевому слову")
@allure.title("Поиск сериала по ключевому слову (Реальные пацаны)")
def test_search_series_by_keyword(page: Page):
    search_page = SearchPage(page)

    with allure.step("Открыть сайт и нажать на строку поиска"):
        search_page.open_main_page()
        search_page.open_search()

    with allure.step("Ввести в поиске слово «пацаны»"):
        search_page.type_query("пацаны")

    with allure.step("Нажать на сериал «Реальные пацаны» в подсказках"):
        search_page.open_suggestion("Реальные пацаны")

    with allure.step("Проверить, что открылась страница сериала"):
        expect(search_page.page.locator("h1").first).to_contain_text(
            "Реальные пацаны", timeout=15000
        )

    with allure.step("Нажать кнопку «Смотреть сериал»"):
        search_page.start_watch()

    with allure.step("Проверить, что открыт плеер с 1 сезоном 1 серией"):
        assert search_page.is_first_episode_open(), \
            f"Плеер не открылся на 1 сезоне 1 серии. URL: {search_page.page.url}"
