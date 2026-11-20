import argparse
import json
import re
import subprocess
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
        raise ValueError("реестр должен вернуть объект JSON")

    dependencies = metadata.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ValueError("поле dependencies должно быть объектом JSON")

    return dependencies


def load_test_repository(path, root):
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

    if root not in repository:
        raise ValueError(f"пакет {root} не найден в тестовом файле")

    return repository


def build_graph(args):
    excluded = args.filter
    if excluded and excluded in args.package:
        return {}

    test_repository = None
    if args.test_mode:
        test_repository = load_test_repository(args.repository, args.package)

    graph = {args.package: []}

    def visit_layer(layer):
        next_layer = []
        for package in layer:
            if test_repository is None:
                dependencies = get_dependencies(args.repository, package)
            else:
                dependencies = test_repository[package]

            for dependency in sorted(set(dependencies)):
                if excluded and excluded in dependency:
                    continue

                graph[package].append(dependency)
                if dependency not in graph:
                    graph[dependency] = []
                    next_layer.append(dependency)

        if next_layer:
            visit_layer(next_layer)

    visit_layer([args.package])
    return graph


def create_dot(graph):
    lines = ["digraph dependencies {", "    rankdir=LR;"]
    for package, dependencies in graph.items():
        source = json.dumps(package, ensure_ascii=False)
        lines.append(f"    {source};")
        for dependency in dependencies:
            target = json.dumps(dependency, ensure_ascii=False)
            lines.append(f"    {source} -> {target};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def save_graph(graph, filename):
    output = Path(filename).resolve()
    dot_file = output.with_suffix(".dot")
    dot_file.write_text(create_dot(graph), encoding="utf-8")

    try:
        subprocess.run(
            ["dot", "-Tpng", str(dot_file), "-o", str(output)], check=True
        )
    except FileNotFoundError as error:
        raise ValueError(
            "Graphviz не найден. Проверь команду dot -V"
        ) from error

    print(f"DOT: {dot_file}")
    print(f"PNG: {output}")


def print_ascii_tree(graph, root):
    print(root)
    shown = {root}

    def print_children(package, prefix):
        dependencies = graph[package]
        for index, dependency in enumerate(dependencies, start=1):
            last = index == len(dependencies)
            branch = "\\-- " if last else "|-- "
            repeated = dependency in shown
            note = " [already shown]" if repeated else ""
            print(f"{prefix}{branch}{dependency}{note}")
            if repeated:
                continue

            shown.add(dependency)
            padding = "    " if last else "|   "
            print_children(dependency, prefix + padding)

    print_children(root, "")


def show_graph(parser, args):
    try:
        graph = build_graph(args)
        if not graph:
            print("Корневой пакет исключён фильтром")
            return

        save_graph(graph, args.output)
        if args.ascii_tree:
            print_ascii_tree(graph, args.package)
    except HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            parser.error(f"пакет не найден: {error.url}")
        parser.error(f"реестр вернул HTTP {error.code}")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    except subprocess.CalledProcessError as error:
        parser.error(f"Graphviz завершился с кодом {error.returncode}")
    except RecursionError:
        parser.error("граф слишком глубокий для рекурсивного обхода")


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
        "--test-mode", action="store_true", help="Использовать тестовый файл"
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
