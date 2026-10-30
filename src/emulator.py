"""Консольный прототип эмулятора с заглушками команд ls и cd."""

SUPPORTED_COMMANDS = ("ls", "cd", "exit")
MAX_LS_ARGUMENTS = 1
REQUIRED_CD_ARGUMENTS = 1


def handle_ls(arguments):
    """Вывести имя команды ls и полученные аргументы без работы с VFS."""
    print(f"ls: аргументы = {arguments}")


def handle_cd(arguments):
    """Вывести имя команды cd и аргументы без смены каталога."""
    print(f"cd: аргументы = {arguments}")


while True:
    user_input = input("vfs9$ ")
    parts = user_input.split()

    if not parts:
        continue

    command = parts[0]
    arguments = parts[1:]

    if command not in SUPPORTED_COMMANDS:
        print(f"Ошибка: неизвестная команда {command}.")
        continue

    if command == "ls" and len(arguments) > MAX_LS_ARGUMENTS:
        print("Ошибка: ls принимает не более одного аргумента-пути.")
        continue

    if command == "cd" and len(arguments) != REQUIRED_CD_ARGUMENTS:
        print("Ошибка: cd ожидает ровно один аргумент-путь.")
        continue

    if command == "exit":
        if arguments:
            print("Ошибка: exit не принимает аргументы.")
            continue
        break

    if command == "ls":
        handle_ls(arguments)
    elif command == "cd":
        handle_cd(arguments)
