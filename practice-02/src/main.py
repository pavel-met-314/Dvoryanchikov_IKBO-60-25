import argparse
import json
import re
from http import HTTPStatus
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import urlopen


def is_repository_url(value):
    if any(char.isspace() for char in value):
        return False

    try:
        url = urlsplit(value)
    except ValueError:
        return False

    return url.scheme in ("http", "https") and bool(url.hostname)


def validate_args(parser, args):
    if args.test_mode:
        if not re.fullmatch(r"[A-Z]", args.package):
            parser.error("в тестовом режиме --package должен быть буквой A–Z")
        if not Path(args.repository).is_file():
            parser.error("--repository должен указывать на существующий файл")
    else:
        name_pattern = r"(@[a-z0-9._-]+/)?[a-z0-9][a-z0-9._-]*"
        if not re.fullmatch(name_pattern, args.package):
            parser.error("--package должен содержать имя npm-пакета")
        if not is_repository_url(args.repository):
            parser.error("--repository должен содержать URL с http или https")

    if Path(args.output).suffix.lower() != ".png":
        parser.error("--output должен быть именем файла с расширением .png")
    if args.filter is not None and not args.filter.strip():
        parser.error("--filter должен содержать непустую подстроку")


def get_dependencies(repository, package):
    package_path = quote(package, safe="")
    url = f"{repository.rstrip('/')}/{package_path}/latest"

    with urlopen(url, timeout=10) as response:
        metadata = json.load(response)

    if not isinstance(metadata, dict):
        raise ValueError("Реестр должен вернуть объект JSON")

    dependencies = metadata.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ValueError("Поле dependencies должно быть объектом JSON")

    return dependencies


def load_test_repository(path):
    repository = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(repository, dict):
        raise ValueError("тестовый репозиторий должен быть объектом JSON")

    for package, dependencies in repository.items():
        if not re.fullmatch(r"[A-Z]", package):
            raise ValueError(f"некорректное имя пакета: {package}")
        if not isinstance(dependencies, list):
            raise ValueError(f"зависимости {package} должны быть списком")
        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in repository:
                raise ValueError(f"пакет {dependency} для {package} не описан")

    return repository


def build_graph(args):
    graph = {}
    excluded = args.filter

    if excluded and excluded in args.package:
        return graph

    test_repository = None
    if args.test_mode:
        test_repository = load_test_repository(args.repository)
        if args.package not in test_repository:
            raise ValueError(f"пакет {args.package} не найден в тестовом файле")

    seen = {args.package}

    def visit_layer(layer):
        next_layer = []
        for package in layer:
            if test_repository is None:
                dependencies = get_dependencies(args.repository, package)
            else:
                dependencies = test_repository[package]

            graph[package] = []
            for dependency in sorted(set(dependencies)):
                if excluded and excluded in dependency:
                    continue
                graph[package].append(dependency)
                if dependency not in seen:
                    seen.add(dependency)
                    next_layer.append(dependency)

        if next_layer:
            visit_layer(next_layer)

    visit_layer([args.package])
    return graph


def show_graph(parser, args):
    try:
        graph = build_graph(args)
    except HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            parser.error(f"пакет не найден: {error.url}")
        parser.error(f"реестр вернул HTTP {error.code}")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    except RecursionError:
        parser.error("граф слишком глубокий для рекурсивного обхода")

    if not graph:
        print("Корневой пакет исключён фильтром")
        return

    for package, dependencies in graph.items():
        links = ", ".join(dependencies) if dependencies else "-"
        print(f"{package}: {links}")


def main():
    parser = argparse.ArgumentParser(
        description="Визуализация зависимостей npm-пакетов",
        allow_abbrev=False,
    )
    parser.add_argument("--package", required=True, help="Имя пакета")
    parser.add_argument(
        "--repository", required=True, help="URL или путь к тестовому файлу"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Использовать тестовый файл",
    )
    parser.add_argument(
        "--output", default="graph.png", help="Имя файла с графом"
    )
    parser.add_argument(
        "--ascii-tree", action="store_true", help="Вывести ASCII-дерево"
    )
    parser.add_argument("--filter", help="Подстрока для исключения пакетов")

    args = parser.parse_args()
    validate_args(parser, args)
    show_graph(parser, args)


if __name__ == "__main__":
    main()
