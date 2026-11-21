import allure

from conftest import api_get


@allure.epic("Кинопоиск API")
@allure.feature("API: поиск фильмов")
@allure.story("Обработка граничных случаев")
@allure.title("Поиск фильмов с некорректными категориями")
@allure.description(
    "Запрос с заведомо некорректными категориями (фильтрами): "
    "год в будущем, несуществующий жанр, диапазон рейтинга, признак сериала. "
    "Ожидаем статус 200 OK и тело null — API корректно обрабатывает отсутствие результата.\n\n"
)
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("api", "negative", "filters", "edge-case")
def test_random_movie_with_invalid_filters():
    """
    Поиск фильмов с некорректными категориями (фильтрами): год в будущем,
    несуществующий жанр, диапазон рейтинга, признак сериала.
    Ожидаемый результат: статус 200 OK, тело ответа — null.

    Эквивалентная проверка в Postman:

        pm.test("Статус код равен 200", function () {
            pm.response.to.have.status(200);
        });

        pm.test("Response body is valid JSON with null", () => {
            const data = pm.response.json();
            pm.expect(data).to.be.null;
        });
    """

    params = {
        "year": "2026",
        "genres.name": "пугалки",
        "rating.imdb": "5-7",
        "isSeries": "true",
        "seriesLength": "60",
    }

    with allure.step("Отправляем запрос с некорректными категориями (фильтрами)"):
        allure.attach(str(params), name="Параметры запроса", attachment_type=allure.attachment_type.TEXT)
        response = api_get("/v1.5/movie/random", params=params)
        allure.attach(f"URL: {response.url}\nStatus: {response.status_code}", name="Реквизиты ответа", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Проверяем статус 200 OK"):
        assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    with allure.step("Проверяем, что тело ответа — null"):
        body = response.json()
        allure.attach(repr(body) if body is not None else "null", name="Тело ответа", attachment_type=allure.attachment_type.TEXT)
        assert body is None, f"Ожидалось null, получено: {str(body)[:300]}"

    with allure.step("Дополнительная проверка: ответ не пустой"):
        assert len(response.content) > 0, "Ответ полностью пуст — подозрительно"
        assert response.text.strip() == "null", f"Тело должно быть ровно 'null', получено: {response.text[:100]!r}"
