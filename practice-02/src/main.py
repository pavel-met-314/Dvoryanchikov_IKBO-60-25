import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit


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

    for key, value in vars(args).items():
        if value is None:
            value = ""
        print(f"{key}={value}")


if __name__ == "__main__":
    main()