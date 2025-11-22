import argparse
import json
import pprint
import sys

# КОНСТАНТЫ ВАРИАНТА №26

# INSTRUCTION_SIZE = 11

# Спецификация полей: (A_code, B_size, C_size, D_size, JSON_fields, Name)
CMD_SPEC = {
    "LC": (4, 23, 26, 0, ('const', 'addr'), "LoadConst"),
    "RM": (12, 26, 26, 0, ('src', 'dst'), "ReadMem"),
    "WM": (3, 26, 26, 0, ('src', 'dst'), "WriteMem"),
    "BR": (9, 26, 26, 7, ('src_base', 'dst', 'offset'), "bitreverse"),
}


# ФУНКЦИИ КОНВЕРТАЦИИ (IR -> Machine Code)

def make_instruction_word(op, args):
    """(Этап 2) Должна собирать поля в одно слово и возвращать 11 байт."""
    return b'\x00' * 11


# ТРАНСЛЯТОРЫ И CLI

def translate_to_ir(ir_program):
    """Преобразует JSON-представление в промежуточное представление (IR)."""
    bytecode = bytes()
    ir_list = []

    for instruction in ir_program:
        op = instruction['op']
        args = {k: v for k, v in instruction.items() if k != 'op'}

        if op not in CMD_SPEC:
            raise ValueError(f"Неизвестная команда: {op}")

        # Формирование IR (Требование 5 Этапа 1)
        ir_entry = {'op': op}
        a_code, b_size, c_size, d_size, json_fields, _ = CMD_SPEC[op]
        ir_entry['A'] = a_code
        ir_entry['B'] = args[json_fields[0]]
        ir_entry['C'] = args[json_fields[1]]
        if d_size > 0:
            ir_entry['D'] = args[json_fields[2]]

        ir_list.append(ir_entry)

        bytecode += b'\x00' * 11

    return bytecode, ir_list


def main():
    parser = argparse.ArgumentParser(description="Ассемблер для УВМ (Вариант 26)")
    # Ассемблер принимает на вход 3 аргумента (Требование 1 Этапа 1)
    parser.add_argument('input', help="Путь к исходному JSON-файлу с текстом программы.")
    parser.add_argument('output', help="Путь к двоичному файлу-результату.")
    parser.add_argument('--test', action='store_true', help="Режим тестирования: выводит IR.")
    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as file:
            program_text = file.read()
            ir_program = json.loads(program_text)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка чтения/парсинга файла: {e}")
        sys.exit(1)

    try:
        # Используем функцию IR
        bytecode, ir_list = translate_to_ir(ir_program)

    except ValueError as e:
        print(f"Ошибка трансляции: {e}")
        sys.exit(1)

    if args.test:
        # Требование 5 Этапа 1 (IR)
        print(f"Число ассемблированных команд: {len(ir_list)}")  # Добавим вывод команд сюда
        print("\n--- Промежуточное представление (IR) ---")
        pprint.pprint(ir_list)


if __name__ == "__main__":
    main()