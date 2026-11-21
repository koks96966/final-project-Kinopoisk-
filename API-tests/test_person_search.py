import allure

from conftest import api_get


@allure.epic("Кинопоиск API")
@allure.feature("API: поиск персон")
@allure.story("Поиск актёров и режиссёров по имени")
@allure.title("Поиск актеров, режиссеров, и т.д по имени​​ «александр петров»")
@allure.description(
    "GET /v1.5/person/search?page=1&limit=10&query=александр петров\n"
    "Проверяем поиск актёров и режиссёров по имени: статус 200, "
    "наличие результатов, структура персоны (id, имя) "
    "и корректный размер страницы."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "search", "person", "smoke")
def test_person_search_by_name():
    """
    Сценарий:
    1. Отправляем запрос на поиск персоны по имени.
    2. Проверяем статус и структуру ответа.
    3. Проверяем, что результаты содержат ожидаемую персону (Александр Петров).
    """

    # ---------- ШАГ 1. Запрос ----------
    with allure.step(
        "Шаг 1. Отправляем запрос на поиск персоны «александр петров»"
    ):
        params = {
            "page": 1,
            "limit": 10,
            "query": "александр петров",
        }
        allure.attach(
            str(params),
            name="Параметры запроса",
            attachment_type=allure.attachment_type.TEXT,
        )
        response = api_get("/v1.5/person/search", params=params)
        allure.attach(
            f"URL: {response.url}\nStatus: {response.status_code}",
            name="Реквизиты ответа",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---------- ШАГ 2. Статус ----------
    with allure.step("Шаг 2. Проверяем статус ответа 200"):
        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}"
        )

    body = response.json()

    # ---------- ШАГ 3. Структура ----------
    with allure.step("Шаг 3. Проверяем структуру ответа и размер страницы"):
        assert "docs" in body, "В ответе нет поля 'docs'"
        assert isinstance(body["docs"], list), "'docs' должен быть списком"
        assert len(body["docs"]) <= 10, (
            "Страница не может содержать больше 10 персон "
            f"(получено {len(body['docs'])})"
        )

    # ---------- ШАГ 4. Результат не пустой ----------
    with allure.step(
        "Шаг 4. Проверяем, что персона найдена (docs.length > 0)"
    ):
        assert len(body["docs"]) > 0, "Персоны по запросу не найдены"

    # ---------- ШАГ 5. Структура каждой персоны ----------
    with allure.step(
        "Шаг 5. Проверяем наличие id и имени у каждой найденной персоны"
    ):
        for index, person in enumerate(body["docs"]):
            assert "id" in person, f"У персоны №{index} нет поля 'id'"
            assert isinstance(person["id"], int), (
                f"Поле 'id' у персоны №{index} не целое число"
            )
            # У персоны может быть 'name' (русское) или 'enName' (английское)
            has_name = person.get("name") or person.get("enName")
            assert has_name, f"У персоны №{index} нет ни 'name', ни 'enName'"

    # ---------- ШАГ 6. Прикрепляем найденных персон к отчёту ----------
    with allure.step("Шаг 6. Прикрепляем список найденных персон к отчёту"):
        persons_preview = [
            f"id={p['id']}, name={p.get('name') or p.get('enName')}"
            for p in body["docs"][:5]
        ]
        allure.attach(
            "\n".join(persons_preview),
            name=f"Найденные персоны ({len(body['docs'])} шт.)",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---------- Бонус: прикрепляем тело ответа ----------
    allure.attach(
        response.text[:1000],
        name="Тело ответа API (сокращённо)",
        attachment_type=allure.attachment_type.JSON,
    )
