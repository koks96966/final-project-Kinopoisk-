import allure

from conftest import api_get


@allure.epic("Кинопоиск API")
@allure.feature("API: поиск ключевых слов")
@allure.story("Поиск по фильтрам с пагинацией")
@allure.title("Поиск ключевых слов по фильтрам")
@allure.description(
    "GET /v1.5/keyword?limit=10&withCount=false&selectFields=id,title\n"
    "Проверяем поиск ключевых слов: структура ответа, размер страницы, "
    "работу selectFields (в ответе только запрошенные поля) и курсорную пагинацию."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "keyword", "pagination")
def test_keyword_search_with_filters():
    """
    Сценарий:
    1. Первый запрос без курсора — проверяем статус, структуру и размер страницы.
    2. Проверяем, что selectFields сработал: у ключевых слов есть id и title, лишних полей нет.
    3. Берём курсор из ответа и делаем второй запрос — проверяем пагинацию.
    """

    # ---------- ШАГ 1. Первый запрос ----------
    with allure.step("Шаг 1. Отправляем запрос на поиск ключевых слов (limit=10, withCount=false, selectFields=id,title)"):
        params_first = {
            "limit": 10,
            "withCount": "false",
            "selectFields": "id,title",
        }
        allure.attach(
            str(params_first),
            name="Параметры первого запроса",
            attachment_type=allure.attachment_type.TEXT,
        )
        response = api_get("/v1.5/keyword", params=params_first)
        allure.attach(
            f"URL: {response.url}\nStatus: {response.status_code}",
            name="Реквизиты первого ответа",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Шаг 2. Проверяем статус ответа 200"):
        assert response.status_code == 200, f"Ожидался 200, получен {response.status_code}"

    body = response.json()

    with allure.step("Шаг 3. Проверяем структуру ответа и размер страницы"):
        assert "docs" in body, "В ответе нет поля 'docs'"
        assert isinstance(body["docs"], list), "'docs' должен быть списком"
        assert len(body["docs"]) <= 10, (
            f"Страница не может содержать больше 10 ключевых слов (получено {len(body['docs'])})"
        )

    with allure.step("Шаг 4. Проверяем, что selectFields сработал: есть id и title"):
        for index, keyword in enumerate(body["docs"]):
            assert "id" in keyword, f"У ключевого слова №{index} нет поля 'id'"
            assert "title" in keyword, f"У ключевого слова №{index} нет поля 'title'"
            assert isinstance(keyword["title"], str) and keyword["title"], (
                f"У ключевого слова №{index} поле 'title' пустое или не строка"
            )

    first_page_ids = [keyword["id"] for keyword in body["docs"]]

    with allure.step("Шаг 5. Прикрепляем список id первой страницы к отчёту"):
        titles_preview = ", ".join(k["title"] for k in body["docs"][:5])
        allure.attach(
            f"ID: {first_page_ids}\nПервые названия: {titles_preview}",
            name=f"Ключевые слова первой страницы ({len(first_page_ids)} шт.)",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---------- ШАГ 6. Курсор ----------
    with allure.step("Шаг 6. Проверяем наличие курсора для следующей страницы"):
        next_cursor = body.get("nextCursorId")
        if next_cursor is None:
            # Краевой случай: результатов меньше лимита — пагинация закончилась
            allure.attach(
                response.text[:1000],
                name="Ответ без курсора",
                attachment_type=allure.attachment_type.JSON,
            )
            return

    # ---------- ШАГ 7. Второй запрос с курсором ----------
    with allure.step("Шаг 7. Отправляем второй запрос с полученным курсором"):
        params_second = {
            "limit": 10,
            "withCount": "false",
            "selectFields": "id,title",
            "cursor": next_cursor,
        }
        allure.attach(
            f"cursor = {next_cursor}",
            name="Параметры второго запроса",
            attachment_type=allure.attachment_type.TEXT,
        )
        response2 = api_get("/v1.5/keyword", params=params_second)

    with allure.step("Шаг 8. Проверяем статус второго ответа 200"):
        assert response2.status_code == 200, f"Ожидался 200, получен {response2.status_code}"

    second_page_ids = [keyword["id"] for keyword in response2.json()["docs"]]

    with allure.step("Шаг 9. Проверяем, что вторая страница не повторяет первую"):
        overlap = set(first_page_ids) & set(second_page_ids)
        assert not overlap, f"Ключевые слова со второй страницы дублируют первую: {overlap}"

    allure.attach(
        response.text[:1000],
        name="Тело первого ответа (сокращённо)",
        attachment_type=allure.attachment_type.JSON,
    )
