import argparse
import json
import sys

# КОНСТАНТЫ И СПЕЦИФИКАЦИЯ КОМАНД (для декодирования)

INSTRUCTION_SIZE = 11

# Спецификация полей: (A_code, B_size, C_size, D_size, Name)
CMD_SPEC = {
    4: (4, 23, 26, 0, "LC"),  # LoadConst
    12: (4, 26, 26, 0, "RM"),  # ReadMem
    3: (4, 26, 26, 0, "WM"),  # WriteMem
    9: (4, 26, 26, 7, "BR"),  # bitreverse
}

# Размер памяти и слова данных
DATA_WORD_SIZE = 4
MEMORY_SIZE = 1024


# ДЕКОДИРОВАНИЕ

def decode_instruction(word_bytes):
    """Декодирует 11-байтовое машинное слово обратно в поля A, B, C, D."""

    instruction_word = int.from_bytes(word_bytes, byteorder='little')

    A_code = instruction_word & 0b1111

    if A_code not in CMD_SPEC:
        raise ValueError(f"Неизвестный код операции A: {A_code}")

    A_size, B_size, C_size, D_size, op_name = CMD_SPEC[A_code]

    bit_offset = A_size

    # 3. Выделяем поле B
    B_mask = (1 << B_size) - 1
    B_value = (instruction_word >> bit_offset) & B_mask
    bit_offset += B_size

    # 4. Выделяем поле C
    C_mask = (1 << C_size) - 1
    C_value = (instruction_word >> bit_offset) & C_mask
    bit_offset += C_size

    # 5. Выделяем поле D (если есть)
    D_value = None
    if D_size > 0:
        D_mask = (1 << D_size) - 1
        D_value = (instruction_word >> bit_offset) & D_mask

    return {
        'op': op_name,
        'A': A_code,
        'B': B_value,
        'C': C_value,
        'D': D_value
    }


# МОДЕЛЬ ПАМЯТИ И ИНТЕРПРЕТАЦИЯ

class UVMInterpreter:
    """Интерпретатор Учебной Виртуальной Машины."""

    def __init__(self, bytecode):
        # Реализация модели памяти (Требование 3 Этапа 3)
        self.memory = [0] * MEMORY_SIZE
        self.bytecode = bytecode
        self.pc = 0  # Program Counter

    def run(self):
        """Основной цикл интерпретации (Требование 4 Этапа 3)."""

        program_length = len(self.bytecode)

        while self.pc < program_length:
            # 1. Чтение команды (Fetch)
            word_bytes = self.bytecode[self.pc:self.pc + INSTRUCTION_SIZE]

            if len(word_bytes) < INSTRUCTION_SIZE:
                break

            # 2. Декодирование команды (Decode)
            try:
                instruction = decode_instruction(word_bytes)
            except ValueError as e:
                print(f"Ошибка декодирования по адресу {self.pc}: {e}")
                break

            # 3. Выполнение команды (Execute)
            self._execute_instruction(instruction)

            self.pc += INSTRUCTION_SIZE

        return self.memory

    def _execute_instruction(self, instr):
        """Выполняет команды LC, RM, WM (Требование 5 Этапа 3)."""
        op = instr['op']
        B = instr['B']
        C = instr['C']

        if op == "LC":  # LoadConst: mem[C] = B
            # LC: B=Константа, C=Адрес.
            if 0 <= C < MEMORY_SIZE:
                self.memory[C] = B

        elif op == "RM":  # ReadMem: mem[C] = mem[B]
            # RM: B=Адрес источника, C=Адрес назначения.
            if 0 <= B < MEMORY_SIZE and 0 <= C < MEMORY_SIZE:
                self.memory[C] = self.memory[B]

        elif op == "WM":  # WriteMem: mem[mem[C]] = mem[B]
            # WM: B=Адрес значения, C=Адрес адреса назначения.
            if 0 <= B < MEMORY_SIZE and 0 <= C < MEMORY_SIZE:
                value_at_B = self.memory[B]
                target_address = self.memory[C]

                if 0 <= target_address < MEMORY_SIZE:
                    self.memory[target_address] = value_at_B
                else:
                    print(f"Ошибка WM: Недопустимый косвенный адрес {target_address}")

        elif op == "BR":
            pass  # Реализация в Этапе 4

        else:
            raise NotImplementedError(f"Команда {op} не реализована.")


# CLI и Утилиты

def dump_memory(memory, range_str, output_file):
    """Сохраняет дамп памяти в JSON (Требование 2 Этапа 3)."""

    # Парсинг диапазона (Требование 1 Этапа 3)
    try:
        start, end = map(int, range_str.split('-'))
        if start < 0 or end >= MEMORY_SIZE or start > end:
            raise ValueError
    except ValueError:
        print(f"Ошибка: Неверный формат диапазона '{range_str}' или он выходит за пределы (0-{MEMORY_SIZE - 1}).")
        sys.exit(1)

    # Формирование дампа
    memory_dump = {
        "start_address": start,
        "end_address": end,
        "data": {}
    }
    for i in range(start, end + 1):
        memory_dump["data"][str(i)] = memory[i]

    # Запись в JSON файл
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(memory_dump, f, indent=4)

    print(f"Дамп памяти сохранен в {output_file} (адреса {start}-{end})")


def main():
    # Реализация CLI (Требование 1 Этапа 3)
    parser = argparse.ArgumentParser(description="Интерпретатор для УВМ (Вариант 26)")
    parser.add_argument('input', help="Путь к бинарному файлу с программой.")
    parser.add_argument('output', help="Путь к файлу, куда будет сохранен дамп памяти.")
    parser.add_argument('range', help="Диапазон адресов памяти для вывода дампа (например, '0-100').")
    args = parser.parse_args()

    try:
        with open(args.input, "rb") as file:
            bytecode = file.read()
    except FileNotFoundError:
        print(f"Ошибка: Бинарный файл не найден: {args.input}")
        sys.exit(1)

    print(f"Загружено {len(bytecode) // INSTRUCTION_SIZE} команд.")

    interpreter = UVMInterpreter(bytecode)
    final_memory = interpreter.run()

    dump_memory(final_memory, args.range, args.output)


if __name__ == "__main__":
    main()