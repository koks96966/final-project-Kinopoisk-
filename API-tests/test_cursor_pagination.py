import allure

from conftest import api_get


@allure.epic("Кинопоиск API")
@allure.feature("API: универсальный поиск")
@allure.story("Пагинация с курсором")
@allure.title("Универсальный поиск фильмов с фильтрами(cursor)​")
@allure.description(
    "Тест проверяет работу курсорной пагинации: первый запрос возвращает "
    "первую страницу с курсором на следующую, второй запрос с этим курсором "
    "возвращает следующую страницу без дубликатов первой."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "pagination", "smoke")
def test_movie_cursor_pagination():
    """
    GET /v1.5/movie?limit=10&withCount=false

    Сценарий:
    1. Первый запрос без курсора — получаем первую страницу и nextCursorId.
    2. Проверяем структуру ответа и размер страницы.
    3. Второй запрос с полученным курсором — получаем вторую страницу.
    4. Убеждаемся, что страницы не пересекаются.
    """

    # ---------- ШАГ 1. Первый запрос ----------
    with allure.step(
        "Шаг 1. Отправляем первый запрос (limit=10, withCount=false)"
    ):
        params_first = {
            "limit": 10,
            "withCount": "false",
        }
        # Фиксируем параметры запроса в отчёте
        allure.attach(
            str(params_first),
            name="Параметры первого запроса",
            attachment_type=allure.attachment_type.TEXT,
        )
        response = api_get("/v1.5/movie", params=params_first)
        # Прикрепляем URL и статус ответа
        allure.attach(
            f"URL: {response.url}\nStatus: {response.status_code}",
            name="Реквизиты первого ответа",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Шаг 2. Проверяем статус ответа 200"):
        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}"
        )

    # ---------- ШАГ 3. Структура первой страницы ----------
    body = response.json()

    with allure.step("Шаг 3. Проверяем структуру ответа"):
        assert "docs" in body, "В ответе нет поля 'docs'"
        assert isinstance(body["docs"], list), "'docs' должен быть списком"
        assert len(body["docs"]) <= 10, (
            "Страница не может содержать больше 10 фильмов "
            f"(получено {len(body['docs'])})"
        )

    with allure.step("Шаг 4. Проверяем, что каждый фильм имеет id"):
        for index, movie in enumerate(body["docs"]):
            assert "id" in movie, f"У фильма №{index} нет поля 'id'"
            assert isinstance(movie["id"], int), (
                "У фильма № {index} поле 'id' не целое число: "
                f"{type(movie['id'])}"
            )

    first_page_ids = [movie["id"] for movie in body["docs"]]

    with allure.step("Шаг 5. Прикрепляем список id первой страницы к отчёту"):
        allure.attach(
            "\n".join(str(i) for i in first_page_ids),
            name=f"ID фильмов первой страницы ({len(first_page_ids)} шт.)",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---------- ШАГ 6. Курсор ----------
    with allure.step(
        "Шаг 6. Проверяем наличие курсора для следующей страницы"
    ):
        next_cursor = body.get("nextCursorId")
        allure.attach(
            f"nextCursorId: {next_cursor}",
            name="Значение курсора",
            attachment_type=allure.attachment_type.TEXT,
        )
        if next_cursor is None:
            # Краевой случай: фильмов меньше 10 — пагинация закончилась.
            allure.attach(
                response.text[:1000],
                name="Ответ без курсора",
                attachment_type=allure.attachment_type.JSON,
            )
            return  # тест корректно завершается

    # ---------- ШАГ 7. Второй запрос с курсором ----------
    with allure.step("Шаг 7. Отправляем второй запрос с полученным курсором"):
        params_second = {
            "limit": 10,
            "withCount": "false",
            "cursor": next_cursor,
        }
        allure.attach(
            f"cursor = {next_cursor}",
            name="Параметры второго запроса",
            attachment_type=allure.attachment_type.TEXT,
        )
        response2 = api_get("/v1.5/movie", params=params_second)
        allure.attach(
            f"URL: {response2.url}\nStatus: {response2.status_code}",
            name="Реквизиты второго ответа",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Шаг 8. Проверяем статус второго ответа 200"):
        assert response2.status_code == 200, (
            f"Ожидался 200, получен {response2.status_code}"
        )

    second_body = response2.json()
    second_page_ids = [movie["id"] for movie in second_body["docs"]]

    with allure.step("Шаг 9. Прикрепляем список id второй страницы к отчёту"):
        allure.attach(
            "\n".join(str(i) for i in second_page_ids),
            name=f"ID фильмов второй страницы ({len(second_page_ids)} шт.)",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---------- ШАГ 10. Проверка на дубликаты ----------
    with allure.step(
        "Шаг 10. Проверяем, что вторая страница не повторяет первую"
    ):
        overlap = set(first_page_ids) & set(second_page_ids)
        allure.attach(
            f"Пересечение: {sorted(overlap) if overlap else 'нет'}",
            name="Результат сравнения страниц",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert not overlap, (
            f"Фильмы со второй страницы дублируют первую: {overlap}"
        )

    # ---------- Финальное вложение: тело первого ответа ----------
    allure.attach(
        response.text[:1000],
        name="Тело первого ответа (сокращённо)",
        attachment_type=allure.attachment_type.JSON,
    )
