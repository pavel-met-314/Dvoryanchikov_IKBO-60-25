import tkinter as tk

VFS_NAME = "vfs9"
PREFIX = f"{VFS_NAME}$ "
MAX_LS_ARGUMENTS = 1
REQUIRED_CD_ARGUMENTS = 1


def command_message(command, arguments):
    if command == "ls":
        if len(arguments) > MAX_LS_ARGUMENTS:
            return "Ошибка: ls принимает не более одного аргумента.\n"
        return f"ls: аргументы = {arguments}\n"

    if command == "cd":
        if len(arguments) != REQUIRED_CD_ARGUMENTS:
            return "Ошибка: cd ожидает ровно один аргумент.\n"
        return f"cd: аргументы = {arguments}\n"

    if command == "exit":
        return "Ошибка: exit не принимает аргументы.\n"

    return f"Ошибка: неизвестная команда {command}.\n"


def on_enter(event):
    line = terminal.get("end-1c linestart", "end-1c")
    prefix_length = len(PREFIX)
    user_input = line[prefix_length:]
    parts = user_input.split()

    terminal.insert("end", "\n")

    if parts:
        command = parts[0]
        arguments = parts[1:]
        if command == "exit" and not arguments:
            window.destroy()
            return "break"

        terminal.insert("end", command_message(command, arguments))

    terminal.insert("end", PREFIX)
    terminal.mark_set("insert", "end-1c")
    return "break"


window = tk.Tk()
window.title("Эмулятор")
window.geometry("900x550")

terminal = tk.Text(
    window, bg="black", fg="white", insertbackground="white",
    font=("Consolas", 14))
terminal.pack(fill="both", expand=True)
terminal.insert("end", PREFIX)
terminal.bind("<Return>", on_enter)
terminal.focus_set()

if __name__ == "__main__":
    window.mainloop()
