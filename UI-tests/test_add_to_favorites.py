import allure
import pytest
from playwright.sync_api import Page

from pages import FilmPage


@pytest.mark.ui
@allure.feature("Избранное")
@allure.story("Буду смотреть")
@allure.title("Добавление фильма в избранное")
def test_add_to_favorites(page: Page):
    film = FilmPage(page)

    with allure.step("Нажать на обложку или название любого фильма"):
        film.open_first_card()

    with allure.step("Очистка: если фильм уже в избранном — убрать его"):
        if film.is_in_wishlist():
            film.remove_from_wishlist()

    with allure.step("Нажать кнопку «Буду смотреть»"):
        film.add_to_wishlist()
        assert film.is_in_wishlist(), "Кнопка «Буду смотреть» не перешла в состояние добавлено"

    with allure.step("Сверху справа от строки поиска нажать «флажок»"):
        film.open_wishlist_flag()

    with allure.step("Проверка: фильм отображается на странице избранного"):
        assert film.is_film_in_wishlist(), (
            f"Фильм {film.current_href} не отображается на странице избранного"
        )
