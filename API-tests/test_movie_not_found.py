import allure

from conftest import api_get


@allure.epic("Кинопоиск API")
@allure.feature("API: получение фильма по ID")
@allure.story("Обработка ошибок и граничные случаи")
@allure.title("Поиск фильма по id вне допустимого диапазона (вызов метода GET v1.5/movie/122)")
@allure.description(
    "Проверяем реакцию API на некорректный ID фильма (вне диапазона 250–99999999): "
    "ожидаем статус 400 и JSON с описанием ошибки. "
    "});"
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("api", "negative", "error-handling", "400")
def test_movie_by_invalid_id():
    """
    GET /v1.5/movie/122 — ID вне валидного диапазона (250–99999999).
    Ожидаемый результат: статус 400 + JSON с описанием ошибки.

    Эквивалентная проверка в Postman:

        pm.test("Status 400 and error body: Bad Request, statusCode 400", () => {
            pm.response.to.have.status(400);
            const data = pm.response.json();
            pm.expect(data.error).to.eql("Bad Request");
            pm.expect(data.statusCode).to.eql(400);
            pm.expect(data.message).to.be.an("array").and.to.have.lengthOf(1);
        });
    """

    with allure.step("Шаг 1. Отправляем запрос на несуществующий фильм (ID=122)"):
        response = api_get("/v1.5/movie/122")
        allure.attach(
            f"URL: {response.url}\nStatus: {response.status_code}",
            name="Реквизиты ответа",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Шаг 2. Проверяем, что статус — 400 (Bad Request)"):
        assert response.status_code == 400, (
            f"Ожидался статус 400 для некорректного ID, получен {response.status_code}"
        )

    # Пытаемся распарсить JSON; если не получится — тест упадёт явно, и это тоже полезно
    with allure.step("Шаг 3. Проверяем, что ответ — валидный JSON"):
        try:
            body = response.json()
        except ValueError as e:
            allure.attach(
                response.text,
                name="Сырой ответ (не JSON)",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert False, f"Ожидался JSON-ответ, но получен невалидный JSON: {e}"

    with allure.step("Шаг 4. Проверяем структуру JSON-ошибки"):
        has_error_field = "error" in body or "message" in body
        assert has_error_field, (
            "В ответе на 400 желательно наличие поля error/message, "
            f"но получен JSON без них: {body}"
        )

        # message может быть строкой или списком строк — API возвращает оба варианта
        if "message" in body:
            msg = body["message"]
            if isinstance(msg, list):
                assert len(msg) > 0, "Поле 'message' — пустой список"
                assert all(isinstance(m, str) and m for m in msg), (
                    f"Поле 'message' должно быть списком непустых строк, получено: {msg}"
                )
            else:
                assert isinstance(msg, str) and msg, (
                    f"Поле 'message' должно быть непустой строкой, получено: {msg}"
                )

        # error также допускает строку или список
        if "error" in body:
            err = body["error"]
            if isinstance(err, list):
                assert len(err) > 0, "Поле 'error' — пустой список"
                assert all(isinstance(e, str) and e for e in err), (
                    f"Поле 'error' должно быть списком непустых строк, получено: {err}"
                )
            else:
                assert isinstance(err, str) and err, (
                    f"Поле 'error' должно быть непустой строкой, получено: {err}"
                )

    with allure.step("Шаг 5. Прикрепляем тело ответа к отчёту"):
        allure.attach(
            response.text[:1000],
            name="Тело ответа API (сокращённо)",
            attachment_type=allure.attachment_type.JSON,
        )
