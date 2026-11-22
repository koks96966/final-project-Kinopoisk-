import allure

from conftest import api_get

# Здесь будем хранить id найденного фильма
MOVIE_ID_FILE = "movie_id.txt"


@allure.epic("Кинопоиск API")
@allure.feature("API: поиск по названию")
@allure.title("Поиск фильма по названию «один дома»")
@allure.description(
    "Отправляем поисковый запрос, "
    "проверяем статус 200 и что найден хотя бы один фильм. "
    "id первого найденного фильма сохраняем."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "search", "smoke")
def test_search_one_movie():
    """
    GET /v1.5/movie/search?query=один дома

    Аналог Postman-скрипта:
    - pm.expect(json.docs.length).to.be.above(0)      → assert len(docs) > 0
    - pm.collectionVariables.set("movieId", docs[0].id) → сохраняем id в файл
    """

    with allure.step("Отправляем запрос на поиск фильма «один дома»"):
        response = api_get("/v1.5/movie/search", params={
            "page": 1,
            "limit": 10,
            "query": "один дома",
        })

    with allure.step("Проверяем статус ответа 200"):
        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}"
        )

    with allure.step("Проверяем, что фильм найден (docs.length > 0)"):
        body = response.json()
        assert "docs" in body, "В ответе нет поля 'docs'"
        # Это и есть аналог pm.expect(json.docs.length).to.be.above(0)
        assert len(body["docs"]) > 0, (
            f"Фильм не найден: docs пуст ({len(body['docs'])} элементов)"
        )

    with allure.step("Проверяем структуру первого фильма"):
        first = body["docs"][0]
        assert "id" in first and "name" in first, (
            "У фильма нет полей 'id'/'name'"
        )
        assert isinstance(first["id"], int)

    with allure.step("Сохраняем id первого фильма (аналог movieId в Postman)"):
        movie_id = first["id"]
        with open(MOVIE_ID_FILE, "w", encoding="utf-8") as f:
            f.write(str(movie_id))
        allure.attach(
            f"movieId = {movie_id}",
            name="Сохранённый movieId",
            attachment_type=allure.attachment_type.TEXT,
        )

    allure.attach(
        response.text[:1000],
        name="Тело ответа API",
        attachment_type=allure.attachment_type.JSON,
    )
