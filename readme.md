Этот скрипт на Python предназначен для нахождения кратчайшего расстояния между двумя актёрами на основе их совместной работы в фильмах.
## Принцип работы

1. **Парсинг данных с IMDb:**
   - Скрипт отправляет асинхронные HTTP-запросы к страницам IMDb, чтобы получить информацию о фильмах, в которых участвовали актёры.
   - Используя библиотеку `BeautifulSoup`, извлекается HTML-код, из которого извлекаются ссылки на фильмы и актёров.

2. **Построение графа актёров:**
   - Каждый актёр представляется как узел графа. Ребро между двумя узлами (актерами) добавляется, если эти актёры снимались вместе в одном фильме.
   - Граф строится для каждого актёра, с которым происходит работа. Все их коллеги по съемочной площадке добавляются в граф, создавая связи между актёрами.

3. **Алгоритм поиска кратчайшего пути (BFS):**
   - Для поиска кратчайшего пути между двумя актёрами используется алгоритм поиска в ширину (BFS).
   - BFS проходит по графу, начиная с одного актёра и передвигаясь по связям (фильмам), пока не найдёт второго актёра или пока не будут исследованы все возможные связи.

4. **Отчёт о прогрессе и времени выполнения:**
   - В процессе работы скрипт периодически выводит информацию о размере построенного графа и времени выполнения, что помогает отслеживать прогресс.

5. **Асинхронность:**
   - Благодаря использованию библиотеки `asyncio`, скрипт может обрабатывать несколько запросов одновременно, что значительно ускоряет процесс парсинга и построения графа.
   
## Требования
Необходимо установить зависимости
pip install -r requirements.txt

Настройка: Отредактируйте скрипт, чтобы указать URL-адреса актёров, между которыми вы хотите найти кратчайшее расстояние. Например:

actor_url_1 = "https://www.imdb.com/name/nm0000123/fullcredits"  # Al Pacino

actor_url_2 = "https://www.imdb.com/name/nm0000163/fullcredits"  # Kevin Bacon
