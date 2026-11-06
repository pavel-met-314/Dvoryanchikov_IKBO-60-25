
import tkinter as tk

VFS_NAME = "vfs9"
PREFIX = f"{VFS_NAME}$ "
MAX_LS_ARGUMENTS = 1
REQUIRED_CD_ARGUMENTS = 1


def on_enter(event):
    line = terminal.get("end-1c linestart", "end-1c")
    prefix_length = len(PREFIX)
    user_input = line[prefix_length:]
    parts = user_input.split()

    terminal.insert("end", "\n")

    if parts:
        command = parts[0]
        arguments = parts[1:]
        if command not in ("ls", "cd", "exit"):
            message = f"Ошибка: неизвестная команда {command}.\n"
        elif command == "ls" and len(arguments) > MAX_LS_ARGUMENTS:
            message = "Ошибка: ls принимает не более одного аргумента.\n"
        elif command == "cd" and len(arguments) != REQUIRED_CD_ARGUMENTS:
            message = "Ошибка: cd ожидает ровно один аргумент.\n"
        elif command == "exit" and arguments:
            message = "Ошибка: exit не принимает аргументы.\n"
        elif command == "ls":
            message = f"ls: аргументы = {arguments}\n"
        elif command == "cd":
            message = f"cd: аргументы = {arguments}\n"
        elif command == "exit":
            window.destroy()
            return "break"

        terminal.insert("end", message)

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
