import json

from textual.app import App, ComposeResult, on
from textual.widgets import TextArea, Button, RichLog

from assembler import translate_to_ir_and_bytecode
from interpreter import UVMInterpreter


DEMO_PROGRAM = """
[
    {"op": "LC", "const": 1, "addr": 10},
    {"op": "LC", "const": 10, "addr": 20},
    {"op": "BR", "src_base": 20, "dst": 30, "offset": 0}
]
""".strip()


class UvmGUI(App):
    """Простейший GUI для УВМ: ввод JSON, кнопка, вывод дампа и байткода."""

    TITLE = "УВМ (вариант 26) — минимальный GUI"

    def compose(self) -> ComposeResult:
        # 1. Окно редактируемой программы (язык ассемблера в виде JSON)
        yield TextArea(text=DEMO_PROGRAM, id="input")

        # 2. Кнопка ассемблирования и запуска интерпретатора
        yield Button("АСЕМБЛИРОВАНИЕ И ЗАПУСК", id="run")

        # 3. Окно вывода дампа памяти и байткода
        yield RichLog(id="output")

    @on(Button.Pressed, "#run")
    def run_program(self) -> None:
        input_area = self.query_one("#input", TextArea)
        output = self.query_one("#output", RichLog)

        output.clear()
        src = input_area.text.strip()

        if not src:
            output.write("Ошибка: программа пуста.")
            return

        try:
            # Парсим JSON-программу
            ir_program = json.loads(src)

            # Ассемблируем
            bytecode, ir_list = translate_to_ir_and_bytecode(ir_program)

            # Запускаем интерпретатор
            interp = UVMInterpreter(bytecode)
            memory = interp.run()   # предполагаем, что это список или похожий объект

            # Простой дамп: первые 40 ячеек памяти
            dump_lines = [f"len(memory) = {len(memory)}"]
            for i in range(min(40, len(memory))):
                dump_lines.append(f"{i:03}: {memory[i]}")

            dump_text = "\n".join(dump_lines)

            # Выводим всё разом
            output.write("--- РЕЗУЛЬТАТ ---")
            output.write(f"Стек (если есть): []")  # в твоей модели стек не используется
            output.write(dump_text)
            output.write("\n--- БАЙТКОД ---")
            output.write(" ".join(f"0x{b:02X}" for b in bytecode))
            output.write(f"\nКоманд: {len(ir_list)}, байт: {len(bytecode)}")

        except Exception as e:
            output.write(f"ОШИБКА: {e!r}")


if __name__ == "__main__":
    app = UvmGUI()
    app.run()
