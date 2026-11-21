import re

import allure
from playwright.sync_api import Page, expect


class FilmPage:
    """Страница фильма/сериала на Кинопоиске."""

    WATCH_BUTTON = 'button[title="Буду смотреть"]'
    CARD_LINK = 'a[data-test-id="next-link"]'
    WISHLIST_LINK = 'a[aria-label="Буду смотреть"]'
    WISHLIST_URL_PART = "planned-to-watch"

    def __init__(self, page: Page):
        self.page = page
        self.current_href = None

    @allure.step("Открыть главную страницу")
    def open_main_page(self):
        self.page.goto("https://www.kinopoisk.ru/")
        self.page.wait_for_load_state("domcontentloaded")
        # Ждём, пока SPA дорисует карточки
        expect(
            self.page.locator(self.CARD_LINK).first
        ).to_be_visible(timeout=12000)

    @allure.step("Открыть страницу тайтла по прямой ссылке: {film_url}")
    def open_film(self, film_url: str):
        self.page.goto(film_url)
        self.page.wait_for_load_state("domcontentloaded")

    @allure.step("Нажать на обложку или название любого фильма")
    def open_first_card(self):
        self.open_main_page()

        posters = self.page.locator(
            f'{self.CARD_LINK}[class*="styles_posterLink"]'
        )
        card = posters.first
        expect(card).to_be_visible(timeout=12000)

        self.current_href = card.get_attribute("href")
        card.scroll_into_view_if_needed()

        try:
            card.click(timeout=3000)
        except Exception:
            card.click(timeout=3000, force=True)

        self.page.wait_for_url(
            lambda url: self.current_href in url, timeout=15000
        )
        self.page.wait_for_load_state("domcontentloaded")

    def watch_button(self):
        return self.page.locator(self.WATCH_BUTTON)

    @allure.step("Проверить, что тайтл в списке «Буду смотреть» (по кнопке)")
    def is_in_wishlist(self) -> bool:
        expect(self.watch_button()).to_be_visible(timeout=5000)
        return self.watch_button().get_attribute("aria-pressed") == "true"

    @allure.step("Добавить тайтл в «Буду смотреть»")
    def add_to_wishlist(self):
        btn = self.watch_button()
        expect(btn).to_be_visible(timeout=5000)
        if self.is_in_wishlist():
            return

        # Слушаем ответы сайта на запросы — увидим, что он ответил на клик
        api_responses = []

        def _on_response(response):
            if any(k in response.url for k in (
                "favorite", "wish", "collection"
            )):
                api_responses.append((response.status, response.url))

        self.page.on("response", _on_response)

        try:
            for attempt in range(3):
                try:
                    btn.click(timeout=3000)
                except Exception:
                    btn.dispatch_event("click")

                self.page.wait_for_timeout(1500)
                if self.is_in_wishlist():
                    return
                print(
                    f"[diag] попытка {attempt + 1}: "
                    f"aria-pressed осталась false"
                )

            print(f"[diag] URL после кликов: {self.page.url}")
            print(f"[diag] ответы API: {api_responses}")

            allure.attach(
                self.page.screenshot(),
                name="wishlist_fail.png",
                attachment_type=allure.attachment_type.PNG,
            )

            raise AssertionError(
                f"Клик «Буду смотреть» не изменил состояние кнопки. "
                f"Ответы API: {api_responses}. Смотри скриншот в отчёте."
            )
        finally:
            self.page.remove_listener("response", _on_response)

    @allure.step("Убрать тайтл из «Буду смотреть»")
    def remove_from_wishlist(self):
        btn = self.watch_button()
        expect(btn).to_be_visible(timeout=5000)

        for attempt in range(3):
            if not self.is_in_wishlist():
                return
            btn.click()
            try:
                expect(btn).to_have_attribute(
                    "aria-pressed", "false", timeout=3000
                )
                return
            except AssertionError:
                self.page.wait_for_timeout(500)

        btn.click(force=True)
        expect(btn).to_have_attribute("aria-pressed", "false", timeout=3000)

    @allure.step("Сверху справа от строки поиска нажать «флажок»")
    def open_wishlist_flag(self):
        """
        Клик по «флажку» в шапке — иконке «Буду смотреть» справа
        от строки поиска. Для авторизованного пользователя сайт
        редиректит на персональный URL /user/<id>/movies/planned-to-watch/,
        поэтому ждём страницу по подстроке, а не по точному адресу.
        """
        link = self.page.locator(self.WISHLIST_LINK).first
        expect(link).to_be_visible(timeout=5000)
        try:
            link.click(timeout=3000)
        except Exception:
            link.click(timeout=3000, force=True)

        self.page.wait_for_url(
            lambda url: self.WISHLIST_URL_PART in url, timeout=15000
        )
        self.page.wait_for_load_state("domcontentloaded")
        expect(
            self.page.locator(self.CARD_LINK).first
        ).to_be_visible(timeout=15000)

    @allure.step("Проверка: тайтл отображается на странице избранного")
    def is_film_in_wishlist(self) -> bool:
        """
        Есть ли тайтл из self.current_href на странице списка.
        Сравнение по подстроке href: на странице списка ссылка может
        отличаться от исходной query-параметрами. Проверка опрашивается
        до 15 секунд — карточки списка могут отрисоваться с задержкой.
        """
        if not self.current_href:
            raise RuntimeError(
                "Сначала откройте тайтл через open_first_card()"
            )

        needle = self.current_href.split("?")[0].rstrip("/")
        if not needle:
            return False

        deadline = self.page.evaluate("() => Date.now()") + 15000
        while True:
            cards = self.page.locator(f'a[href*="{needle}"]')
            if cards.count() > 0:
                try:
                    if cards.first.is_visible():
                        return True
                except Exception:
                    pass

            if self.page.evaluate("() => Date.now()") > deadline:
                break
            self.page.wait_for_timeout(400)

        # Диагностика: что реально лежит на странице списка
        actual_hrefs = []
        for a in self.page.locator(
            f'{self.CARD_LINK}, a[href^="/series/"], a[href^="/film/"]'
        ).all()[:15]:
            try:
                actual_hrefs.append(a.get_attribute("href"))
            except Exception:
                continue

        raise AssertionError(
            f"Тайтл {self.current_href} не отображается "
            f"на странице избранного. Искали подстроку: {needle}. "
            f"Фактические ссылки: {actual_hrefs}"
        )

    @allure.step("Нажать кнопку «Смотреть сериал»")
    def start_watch(self):
        btn = self.page.locator('a[data-test-id="Watch"]').first

        if btn.count() == 0:
            btn = self.page.get_by_role(
                "link", name=re.compile(r"Смотреть", re.IGNORECASE)
            ).first

        expect(btn).to_be_visible(timeout=5000)
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(timeout=3000, force=True)

        try:
            self.page.wait_for_url(
                lambda url: "hd.kinopoisk.ru" in url or "/watch" in url,
                timeout=15000,
            )
        except Exception:
            for p in self.page.context.pages:
                if "hd.kinopoisk.ru" in p.url:
                    self.page = p
                    break

        self.page.wait_for_load_state("domcontentloaded")

    @allure.step("Проверить, что открыт плеер с 1 сезоном 1 серией")
    def is_first_episode_open(self) -> bool:
        url = self.page.url
        url_ok = "season=1" in url and "episode=1" in url

        episode_text = self.page.get_by_text(
            re.compile(r"(1\s*сезон)|(сезон\s*1)|(1\s*серия)|(серия\s*1)",
                       re.IGNORECASE)
        )
        text_ok = episode_text.count() > 0

        return url_ok or text_ok

    # ---------- Плеер: чтение состояния видео ----------

    def _video_paused(self):
        try:
            return self.page.evaluate(
                "() => { const v = document.querySelector('video'); "
                "return v ? v.paused : null; }"
            )

        except Exception:
            return None

    def _wait_for_paused(self, expected: bool, timeout_s: float = 6.0):
        deadline = self.page.evaluate(
            "() => Date.now()"
        ) + int(timeout_s * 1000)
        while True:
            value = self._video_paused()
            if value == expected:
                return True
            if self.page.evaluate("() => Date.now()") > deadline:
                return False
            self.page.wait_for_timeout(500)

    def _wait_for_video(self, timeout_ms: int = 15000):
        deadline = self.page.evaluate("() => Date.now()") + timeout_ms
        while True:
            for frame in self.page.frames:
                try:
                    found = frame.evaluate(
                        "() => !!document.querySelector('video')"
                    )
                except Exception:
                    continue
                if found:
                    return frame
            if self.page.evaluate("() => Date.now()") > deadline:
                return None
            self.page.wait_for_timeout(500)

    @allure.step("Получить текущую позицию воспроизведения")
    def get_video_time(self):
        frame = self._wait_for_video(timeout_ms=2000)
        if frame is None:
            return None
        try:
            return frame.evaluate(
                "() => { const v = document.querySelector('video'); "
                "return v ? v.currentTime : null; }"
            )
        except Exception:
            return None

    @allure.step("Проверить, что видео на паузе (с опросом состояния)")
    def is_video_paused(self, timeout_s: float = 3.0) -> bool:
        return self._wait_for_paused(expected=True, timeout_s=timeout_s)

    # ---------- Плеер: пауза и возобновление ----------

    @allure.step("Кликнуть по экрану плеера")
    def click_on_screen(self):
        vp = self.page.viewport_size or {"width": 1920, "height": 1080}
        self.page.mouse.click(vp["width"] // 2, vp["height"] // 2)
        self.page.wait_for_timeout(500)

    @allure.step("Остановить воспроизведение кликом по экрану")
    def pause_player(self):
        self.click_on_screen()
        if self._wait_for_paused(expected=True, timeout_s=5.0):
            return

        paused = self._video_paused()
        raise AssertionError(
            f"После клика по экрану воспроизведение не остановилось: "
            f"video.paused={paused}"
        )

    @allure.step("Возобновить воспроизведение повторным кликом по экрану")
    def resume_player(self):
        self.click_on_screen()
        if self._wait_for_paused(expected=False, timeout_s=5.0):
            return

        paused = self._video_paused()
        raise AssertionError(
            f"После повторного клика воспроизведение не возобновилось: "
            f"video.paused={paused}"
        )

    # ---------- Плеер: перемотка ----------

    def _seek_button(self, backward: bool):
        if backward:
            name_pattern = r"Назад.*10|10.*Назад"
        else:
            name_pattern = r"Вперёд.*10|Вперед.*10|10.*Вперёд"

        btn = self.page.get_by_role(
            "button", name=re.compile(name_pattern, re.IGNORECASE)
        )
        if btn.count() > 0:
            return btn.first

        btn = self.page.locator("button").filter(
            has_text=re.compile(r"^\s*10\s*$")
        )
        if btn.count() > 0:
            return btn.first
        return None

    def _show_controls(self):
        vp = self.page.viewport_size or {"width": 1920, "height": 1080}
        self.page.mouse.move(vp["width"] // 2, vp["height"] // 2)
        self.page.wait_for_timeout(400)

    def _check_seek_delta(self, before, after, direction: str):
        delta = after - before
        if direction == "forward":
            ok = 7 <= delta <= 15
            expected = "около +10"
        else:
            ok = -15 <= delta <= -7
            expected = "около -10"

        if not ok:
            raise AssertionError(
                f"Перемотка {'назад' if direction == 'backward' else 'вперёд'}"
                f" не сработала как ожидалось: было {before:.1f} с, "
                f"стало {after:.1f} с (дельта {delta:.1f} с, "
                f"ожидалось {expected} с)"
            )

    def _seek_by_keyboard(self, direction: str):
        self._show_controls()
        key = "ArrowRight" if direction == "forward" else "ArrowLeft"
        before = self.get_video_time()
        if before is None:
            raise AssertionError(
                "Элемент <video> не найден — не с чем сравнивать позицию"
            )

        self.page.keyboard.press(key)
        self.page.wait_for_timeout(1200)
        after = self.get_video_time()

        self._check_seek_delta(before, after, direction)

    @allure.step("Перемотать на 10 секунд {direction}")
    def seek_by_10(self, direction: str):
        if direction not in ("forward", "backward"):
            raise ValueError("direction должен быть 'forward' или 'backward'")

        if self._wait_for_video(timeout_ms=15000) is None:
            raise AssertionError(
                "Элемент <video> не появился за 15 секунд. "
                f"URL: {self.page.url}"
            )

        self._show_controls()
        btn = self._seek_button(backward=(direction == "backward"))

        if btn is None:
            self._seek_by_keyboard(direction)
            return

        expect(btn).to_be_visible(timeout=5000)
        before = self.get_video_time()
        if before is None:
            raise AssertionError(
                "Элемент <video> не найден — не с чем сравнивать позицию"
            )

        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(timeout=3000, force=True)

        self.page.wait_for_timeout(1200)
        after = self.get_video_time()

        self._check_seek_delta(before, after, direction)

    # ---------- Плеер: сезоны и серии ----------

    _EPISODE_ROW_PATTERN = re.compile(
        r"(?:\d+\s*серия)|(?:серия\s*\d+)|(?:\d+\s*эпизод)|(?:эпизод\s*\d+)|"
        r"(?:\d+\s*выпуск)|(?:выпуск\s*\d+)",
        re.IGNORECASE,
    )

    def _episodes_button(self):
        btn = self.page.get_by_role(
            "button", name=re.compile(r"Сезоны и серии", re.IGNORECASE)
        )
        if btn.count() > 0:
            return btn.first

        btn = self.page.locator("button, [role='button']").filter(
            has_text=re.compile(r"Сезоны и серии", re.IGNORECASE)
        )
        if btn.count() > 0:
            return btn.first
        return None

    def _show_episodes_panel(self):
        if self._wait_for_video(timeout_ms=15000) is None:
            raise AssertionError(
                "Элемент <video> не появился за 15 секунд. "
                f"URL: {self.page.url}"
            )

        self._show_controls()
        btn = self._episodes_button()
        if btn is None:
            raise AssertionError(
                "Кнопка «Сезоны и серии» не найдена в нижней панели"
            )

        expect(btn).to_be_visible(timeout=5000)
        try:
            btn.hover(timeout=3000)
        except Exception:
            btn.hover(timeout=3000, force=True)
        self.page.wait_for_timeout(800)
        return btn

    def _is_episodes_panel_visible(self, timeout_s: float = 5.0) -> bool:
        deadline = self.page.evaluate(
            "() => Date.now()"
        ) + int(timeout_s * 1000)
        while True:
            # 1. Явная кнопка/ссылка «Все сезоны»
            for role in ("button", "link"):
                el = self.page.get_by_role(
                    role, name=re.compile(r"Все\s*сезоны", re.IGNORECASE)
                )
                if el.count() > 0:
                    return True

            # 2. Строки серий: кнопки И ссылки с «N серия»
            for role in ("button", "link"):
                rows = self.page.get_by_role(
                    role, name=self._EPISODE_ROW_PATTERN
                )
                if rows.count() > 0:
                    return True

            # 3. Обычные элементы (div/span/li) с текстом «N серия» —
            #    но не подпись плеера «N сезон, N серия», она одна
            text_rows = self.page.get_by_text(self._EPISODE_ROW_PATTERN)
            if text_rows.count() > 1:
                return True

            # 4. Контейнеры панели по классам: seasons / episodes / playlist
            panel = self.page.locator(
                "[class*='seasons' i], [class*='Seasons' i], "
                "[class*='episode' i], [class*='Episode' i], "
                "[class*='playlist' i]"
            )
            if panel.count() > 0:
                try:
                    if panel.first.is_visible():
                        return True
                except Exception:
                    pass

            if self.page.evaluate("() => Date.now()") > deadline:
                return False
            self.page.wait_for_timeout(400)

    @allure.step("Навести курсор на «Сезоны и серии» и проверить панель серий")
    def hover_episodes_panel(self):
        self._show_episodes_panel()

        # Попытка 1: наведение (как в задании)
        if self._is_episodes_panel_visible(timeout_s=3.0):
            return

        # Попытка 2: клик — некоторые сборки плеера открывают панель по клику
        btn = self._episodes_button()
        if btn is not None:
            try:
                btn.click(timeout=3000, force=True)
                self.page.wait_for_timeout(1200)
            except Exception:
                pass
            if self._is_episodes_panel_visible(timeout_s=3.0):
                return

            # Попытка 3: снова наведение — если клик закрыл панель,
            # открытую наведением
            try:
                btn.hover(timeout=3000, force=True)
                self.page.wait_for_timeout(1500)
            except Exception:
                pass
            if self._is_episodes_panel_visible(timeout_s=3.0):
                return

            raise AssertionError(
                f"После наведения на «Сезоны и серии» панель "
                f"с сериями не появилась. Кнопки на экране: "
                f"{self._buttons_snapshot()}"
            )

    def _click_named_button(self, patterns, description: str):
        for pattern in patterns:
            rx = re.compile(pattern, re.IGNORECASE)
            btn = self.page.get_by_role("button", name=rx)
            if btn.count() == 0:
                btn = self.page.get_by_role("link", name=rx)
            if btn.count() > 0:
                target = btn.first
                expect(target).to_be_visible(timeout=3000)
                try:
                    target.click(timeout=3000)
                except Exception:
                    target.click(timeout=3000, force=True)
                self.page.wait_for_timeout(800)
                return

        raise AssertionError(
            f"Кнопка «{description}» не найдена на экране "
            f"(ни по aria-label, ни по тексту). "
            f"Кнопки на экране: {self._buttons_snapshot()}"
        )

    def _buttons_snapshot(self, limit: int = 30):
        names = []
        for b in self.page.locator("button, [role='button']").all():
            try:
                name = b.get_attribute("aria-label") or b.inner_text()
                name = (name or "").strip().replace("\n", " ")[:60]
                if name:
                    names.append(name)
            except Exception:
                continue
        return names[:limit]

    @allure.step("Нажать кнопку «Все сезоны» и проверить панель сезонов")
    def open_all_seasons(self):
        self._click_named_button([r"Все\s*сезоны"], "Все сезоны")

        deadline = self.page.evaluate("() => Date.now()") + 5000
        while True:
            seasons = self.page.get_by_role(
                "button", name=re.compile(r"\d+\s*сезон", re.IGNORECASE)
            )
            if seasons.count() > 0:
                return
            seasons_text = self.page.get_by_text(
                re.compile(r"\d+\s*сезон", re.IGNORECASE)
            )
            if seasons_text.count() > 0:
                return
            if self.page.evaluate("() => Date.now()") > deadline:
                break
            self.page.wait_for_timeout(400)

        raise AssertionError(
            f"После нажатия «Все сезоны» панель с сезонами не появилась. "
            f"Кнопки на экране: {self._buttons_snapshot()}"
        )

    @allure.step(
            "Нажать кнопку «{season_number} сезон» и проверить панель серий"
        )
    def select_season(self, season_number: int):
        self._click_named_button(
            [rf"{season_number}\s*сезон"], f"{season_number} сезон"
        )

        if self._is_episodes_panel_visible(timeout_s=6.0):
            return

        raise AssertionError(
            f"После выбора «{season_number} сезон» "
            f"панель с сериями не найдена. "
            f"Кнопки на экране: {self._buttons_snapshot()}"
        )

    def _find_episode_tile(self, number: int):
        patterns = [
            rf"^{number}\.\s",
            rf"серия\s*{number}\b",
            rf"{number}\s*серия\b",
            rf"эпизод\s*{number}\b",
            rf"{number}\s*эпизод\b",
            rf"выпуск\s*{number}\b",
        ]
        for pat in patterns:
            rx = re.compile(pat, re.IGNORECASE)
            loc = self.page.get_by_role("button", name=rx)
            if loc.count() > 0:
                return loc.first
            loc = self.page.locator("a").filter(has_text=rx)
            if loc.count() > 0:
                return loc.first

        exact = {
            str(number),
            f"E{number}",
            f"Е{number}",
            f"e{number}",
        }
        for el in self.page.locator(
            "button, a, [role='button'], [role='listitem'], li"
        ).all():
            try:
                name = (
                    el.get_attribute("aria-label") or el.inner_text() or ""
                ).strip()
            except Exception:
                continue
            if name in exact:
                return el
        return None

    @allure.step("Нажать кнопку «{episode_number} серия»")
    def select_episode(self, episode_number: int):
        tile = self._find_episode_tile(episode_number)
        if tile is None:
            raise AssertionError(
                f"Плитка «{episode_number} серия» не найдена в панели. "
                f"Кнопки на экране: {self._buttons_snapshot()}"
            )

        expect(tile).to_be_visible(timeout=3000)
        try:
            tile.click(timeout=3000)
        except Exception:
            tile.click(timeout=3000, force=True)

        try:
            self.page.wait_for_url(
                lambda url: "season=" in url and "episode=" in url,
                timeout=8000,
            )
        except Exception:
            pass

        self.page.wait_for_timeout(1500)

    @allure.step(
            "Проверить, что воспроизводится {season_number} "
            "сезон {episode_number} серия"
    )
    def is_episode_open(self, season_number: int, episode_number: int) -> bool:
        url = self.page.url

        url_ok = (
            f"season={season_number}" in url
            and f"episode={episode_number}" in url
        )

        episode_text = self.page.get_by_text(
            re.compile(
                rf"({season_number}\s*сезон)|(сезон\s*{season_number})",
                re.IGNORECASE,
            )
        )
        text_ok = episode_text.count() > 0

        return url_ok or text_ok


class SearchPage(FilmPage):
    """Поиск по Кинопоиску. Наследует методы FilmPage."""

    SEARCH_PLACEHOLDER = "Фильмы, сериалы, персоны"

    def __init__(self, page: Page):
        super().__init__(page)

    def search_input(self):
        return self.page.get_by_placeholder(self.SEARCH_PLACEHOLDER)

    @allure.step("Нажать на строку поиска")
    def open_search(self):
        field = self.search_input()
        expect(field).to_be_visible(timeout=5000)
        field.click()

    @allure.step("Ввести в поиск ключевое слово: {query}")
    def type_query(self, query: str):
        field = self.search_input()
        field.press_sequentially(query, delay=80)

    @allure.step("Выбрать в подсказках тайтл «{title}»")
    def open_suggestion(self, title: str):
        item = self.page.locator(
            'a[data-test-id="suggest-list__item"]'
        ).filter(has_text=title).first

        if item.count() == 0:
            item = self.page.get_by_role(
                "link", name=re.compile(re.escape(title), re.IGNORECASE)
            ).first

        expect(item).to_be_visible(timeout=10000)
        try:
            item.click(timeout=3000)
        except Exception:
            item.click(timeout=3000, force=True)
