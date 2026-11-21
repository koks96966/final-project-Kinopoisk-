import allure

from conftest import api_get


@allure.title("Поиск фильмов по id")
@allure.feature("API: поиск фильмов")
@allure.severity(allure.severity_level.CRITICAL)
def test_get_movie_by_id():
    """GET /v1.5/movie/666: статус 200, в ответе фильм с id 666 и обязательными полями."""

    with allure.step("Отправляем запрос GET /v1.5/movie/666"):
        response = api_get("/v1.5/movie/666")

    with allure.step("Проверяем статус ответа 200"):
        assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    with allure.step("Проверяем, что вернулся фильм с запрошенным id"):
        body = response.json()
        assert body["id"] == 666, f"Ожидался id=666, получен {body.get('id')}"

    with allure.step("Проверяем наличие обязательных полей фильма"):
        for field in ("name", "type", "year"):
            assert field in body, f"В ответе нет поля '{field}'"
        assert isinstance(body["year"], int), "Год выпуска должен быть числом"
        assert isinstance(body["name"], str) and body["name"], "Название должно быть непустой строкой"

    # Бонус: прикрепим тело ответа к отчёту
    allure.attach(
        response.text[:1000],
        name="Тело ответа API",
        attachment_type=allure.attachment_type.JSON,
    )
