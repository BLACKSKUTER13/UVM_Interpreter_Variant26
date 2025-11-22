import argparse
import json
import pprint
import sys

# --- КОНСТАНТЫ ВАРИАНТА №26 ---

INSTRUCTION_SIZE = 11

# Спецификация полей: (A_code, B_size, C_size, D_size, JSON_fields, Name)
# Размеры: A=4, B_LC=23, B_RWM=26, C=26, D=7. Задается порядок: A, B, C, D.
CMD_SPEC = {
    "LC": (4, 23, 26, 0, ('const', 'addr'), "LoadConst"),  # A=4 (4), B=Const(23), C=Addr(26). Всего 53 бита.
    "RM": (12, 26, 26, 0, ('src', 'dst'), "ReadMem"),  # A=12 (4), B=Addr(26), C=Addr(26). Всего 56 бит.
    "WM": (3, 26, 26, 0, ('src', 'dst'), "WriteMem"),  # A=3 (4), B=Addr(26), C=Addr(26). Всего 56 бит.
    "BR": (9, 26, 26, 7, ('src_base', 'dst', 'offset'), "bitreverse"),
    # A=9 (4), B=Addr(26), C=Addr(26), D=Offset(7). Всего 63 бита.
}


# ФУНКЦИИ КОНВЕРТАЦИИ (IR -> Machine Code)

def make_instruction_word(op, args):
    """Собирает поля в одно слово и возвращает 11 байт (Little-Endian)."""

    a_code, b_size, c_size, d_size, json_fields, _ = CMD_SPEC[op]
    instruction_word = 0
    bit_offset = 0

    # 1. A (4 бита) - Биты 0-3
    instruction_word |= (a_code << bit_offset)
    bit_offset += 4

    # 2. B (Размер B)
    B = args[json_fields[0]]
    instruction_word |= (B << bit_offset)
    bit_offset += b_size

    # 3. C (Размер C)
    C = args[json_fields[1]]
    instruction_word |= (C << bit_offset)
    bit_offset += c_size

    # 4. D (Размер D, если есть)
    if d_size > 0:
        D = args[json_fields[2]]
        instruction_word |= (D << bit_offset)
        bit_offset += d_size

    # Конвертируем в 11 байт (88 бит) в Little-Endian.
    return instruction_word.to_bytes(INSTRUCTION_SIZE, byteorder='little')


# ТРАНСЛЯТОРЫ И CLI

def translate_to_ir_and_bytecode(ir_program):
    """Преобразует JSON-представление в IR и генерирует машинный код."""
    bytecode = bytes()
    ir_list = []

    for instruction in ir_program:
        op = instruction['op']
        args = {k: v for k, v in instruction.items() if k != 'op'}

        if op not in CMD_SPEC:
            raise ValueError(f"Неизвестная команда: {op}")

        # Формирование IR
        ir_entry = {'op': op}
        a_code, b_size, c_size, d_size, json_fields, _ = CMD_SPEC[op]
        ir_entry['A'] = a_code
        ir_entry['B'] = args[json_fields[0]]
        ir_entry['C'] = args[json_fields[1]]
        if d_size > 0:
            ir_entry['D'] = args[json_fields[2]]

        ir_list.append(ir_entry)

        # Генерация байт-кода
        bytecode += make_instruction_word(op, args)

    return bytecode, ir_list


def main():
    parser = argparse.ArgumentParser(description="Ассемблер для УВМ (Вариант 26)")
    parser.add_argument('input', help="Путь к исходному JSON-файлу с текстом программы.")
    parser.add_argument('output', help="Путь к двоичному файлу-результату.")
    parser.add_argument('--test', action='store_true', help="Режим тестирования: выводит IR и байты.")
    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as file:
            ir_program = json.loads(file.read())

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка чтения/парсинга файла: {e}")
        sys.exit(1)

    try:
        bytecode, ir_list = translate_to_ir_and_bytecode(ir_program)

    except ValueError as e:
        print(f"Ошибка трансляции: {e}")
        sys.exit(1)

    # Требование 3 Этапа 2
    print(f"Число ассемблированных команд: {len(ir_list)}")

    # Требование 2 Этапа 2
    with open(args.output, 'wb') as output_file:
        output_file.write(bytecode)

    if args.test:
        # Требование 5 Этапа 1
        print("\n--- Промежуточное представление (IR) ---")
        pprint.pprint(ir_list)

        # Требование 4 Этапа 2
        print("\n--- Результат ассемблирования (Байты) ---")
        hex_output = []
        for i in range(0, len(bytecode), INSTRUCTION_SIZE):
            chunk = bytecode[i:i + INSTRUCTION_SIZE]
            hex_chunk = ' '.join([f"0x{b:02X}" for b in chunk])
            hex_output.append(hex_chunk)

        print('\n'.join(hex_output))


if __name__ == "__main__":
    main()