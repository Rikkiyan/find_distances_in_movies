import asyncio
import re
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Set

import aiohttp
from bs4 import BeautifulSoup

# Граф, где ключи — это актёры, а значения — множества актёров,
# с которыми они снимались
ActorGraph = Dict[str, Set[str]]
actor_graph: ActorGraph = defaultdict(set)

# Глобальный таймер для отслеживания времени выполнения программы
global_start_time = time.time()


def get_elapsed_time() -> str:
    """Возвращает время, прошедшее с начала запуска программы."""
    elapsed_time = time.time() - global_start_time
    return f"{elapsed_time:.2f} seconds"


async def fetch_html(
        session: aiohttp.ClientSession, url: str
) -> Optional[str]:

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(
                url,
                headers=headers,
                allow_redirects=True
        ) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Failed to fetch {url}, status code: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_movie_ids(html_content: str) -> Set[str]:
    """Некоторые страницы с фильмами приходят в другом формате, в таком случае
    извлекаем идентификаторы фильмов (ttNNNNNNNN) с помощью регулярного
    выражения."""
    return set(re.findall(r'tt\d{7,8}', html_content))


def is_excluded_type(text: str) -> bool:
    """Исключает ненужные типы тайтлов."""
    excluded_types_regex = re.compile(
        r"(TV Series|Video Game|Short|TV Mini Series)", re.IGNORECASE
    )
    return bool(excluded_types_regex.search(text))


async def get_movies(
        actor_url: str,
        session: aiohttp.ClientSession
) -> Set[str]:
    """Получает список фильмов, в которых участвовал актёр, по его URL."""
    html = await fetch_html(session, actor_url)
    if html is None:
        print(f"Failed to fetch movies_urls for actor: {actor_url}")
        return set()

    soup = BeautifulSoup(html, "html.parser")
    filmography = soup.find_all("div", class_="filmo-row")
    movies_urls = set()

    if not filmography:
        movie_ids = extract_movie_ids(html)
        for movie_id in movie_ids:
            movie_fullcredits_link = (
                f'https://www.imdb.com/title/{movie_id}/fullcredits'
            )
            movies_urls.add(movie_fullcredits_link)
    else:
        for item in filmography:
            if "actor" in item["id"] or "actress" in item["id"]:
                if is_excluded_type(item.text):
                    continue
                movie_link = item.find("a")["href"]
                movie_fullcredits_link = (
                        'https://www.imdb.com'
                        + movie_link.split('?')[0]
                        + 'fullcredits'
                )
                movies_urls.add(movie_fullcredits_link)

    return movies_urls


async def get_actors_from_movie(
        movie_url: str,
        session: aiohttp.ClientSession
) -> Set[str]:
    """Получает список актёров, снимавшихся в фильме по его URL."""
    html = await fetch_html(session, movie_url)
    if html is None:
        print(f"Failed to fetch actors_urls for movie: {movie_url}")
        return set()

    soup = BeautifulSoup(html, "html.parser")
    project_type_div = soup.find(
        "div", class_="aux-content-widget-2 links subnav"
    )
    if project_type_div and is_excluded_type(project_type_div.text):
        return set()

    cast_list = soup.find("table", class_="cast_list")
    actors_urls = set()

    if cast_list:
        for row in cast_list.find_all("tr", class_=["odd", "even"]):
            actor_cell = row.find("td", class_="")
            if actor_cell:
                actor_link = actor_cell.find("a")["href"]
                actors_urls.add(
                    'https://www.imdb.com'
                    + actor_link.split('?')[0]
                    + 'fullcredits'
                )

    return actors_urls


async def build_graph(actor_url: str, session: aiohttp.ClientSession) -> None:
    """Строит граф актёров, с которыми работал данный актёр."""
    movies = await get_movies(actor_url, session)
    if not movies:
        return

    for movie_url in movies:
        actors_in_movie = await get_actors_from_movie(movie_url, session)
        for co_actor_url in actors_in_movie:
            if co_actor_url != actor_url:
                actor_graph[actor_url].add(co_actor_url)
                actor_graph[co_actor_url].add(actor_url)


async def bfs_find_distance(
        actor_url_1: str,
        actor_url_2: str
) -> Optional[int]:
    """Ищет кратчайшее расстояние между двумя актёрами в графе."""
    if actor_url_1 not in actor_graph or actor_url_2 not in actor_graph:
        print("One or both actors are not in the graph.")
        return None

    queue = deque([(actor_url_1, 0)])
    visited = set([actor_url_1])

    while queue:
        current_actor, distance = queue.popleft()
        if current_actor == actor_url_2:
            return distance

        for neighbor in actor_graph[current_actor]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    print("No connection found.")
    return None


async def report_progress(interval: int = 5) -> None:
    """Периодически выводит текущий размер графа и время выполнения."""
    while True:
        await asyncio.sleep(interval)
        print(
            f"Graph size: "
            f"{sum(len(connections) for connections in actor_graph.values())} "
            f"edges"
        )
        print(f"Elapsed time: {get_elapsed_time()}")


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        progress_task = asyncio.create_task(report_progress())

        # Пример актёров
        actor_url_1 = "https://www.imdb.com/name/nm0000123/fullcredits"  # Al Pacino
        actor_url_2 = "https://www.imdb.com/name/nm0000163/fullcredits"  # Kevin Bacon

        # Сначала строим граф для обоих актёров
        await asyncio.gather(
            build_graph(actor_url_1, session),
            build_graph(actor_url_2, session)
        )

        # Теперь ищем кратчайший путь в графе
        distance = await bfs_find_distance(actor_url_1, actor_url_2)
        if distance is not None:
            print(f"Distance between actors is: {distance}")
        else:
            print("No connection found between actors.")

        # Выводим время выполнения всей программы
        print(f"Total execution time: {get_elapsed_time()}")

        progress_task.cancel()

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
