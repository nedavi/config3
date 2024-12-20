import argparse
import json
import re
import sys

# python config_parser.py -i input_config1.txt -o output.json

class ConfigParser:
    def __init__(self):
        self.constants = {}

    def parse(self, text):
        """Парсинг входного текста."""
        self.constants = {}
        lines = text.split("\n")
        result = []
        buffer = ""  # Для объединения строк словаря
        depth = 0  # Уровень вложенности

        for line in lines:
            line = line.strip()
            print(f"Processing line: {line}")  # Отладочный вывод

            if not line or line.startswith("*") or line.startswith("//"):  # Комментарии
                continue

            if "table(" in line:  # Начало словаря
                depth += 1
                buffer += line
                print(f"Starting table: {buffer}")  # Отладочный вывод
                continue

            if depth > 0:  # Если внутри table(...)
                buffer += line
                print(f"Appending to table buffer: {buffer}")  # Отладочный вывод
                if ")" in line:
                    depth -= 1
                    if depth == 0:  # Конец внешнего table(...)
                        print(f"Completed table: {buffer}")  # Отладочный вывод
                        result.append(self._parse_dict(buffer.strip()))
                        buffer = ""
                continue

            if line.startswith("const"):  # Объявление константы
                self._parse_constant(line)
            elif line.startswith("|") and line.endswith("|"):  # Вычисление константы
                result.append(self._evaluate_constant(line))
            else:
                result.append(self._parse_structure(line))

        return result

    def _parse_constant(self, line):
        """Обработка строк вида const name = value;"""
        match = re.match(r"const\s+([a-z][a-z0-9_]*)\s*=\s*(.+);", line)
        if not match:
            raise SyntaxError(f"Invalid constant declaration: {line}")
        name, value = match.groups()
        self.constants[name] = self._parse_value(value)

    def _evaluate_constant(self, line):
        """Вычисление значения константы |name|."""
        name = line.strip("|")
        if name not in self.constants:
            raise ValueError(f"Undefined constant: {name}")
        return self.constants[name]

    def _parse_structure(self, line):
        """Определяет, что парсить: массив или словарь."""
        if line.startswith("["):  # Массив
            return self._parse_array(line)
        if line.startswith("table("):  # Словарь
            return self._parse_dict(line)
        raise SyntaxError(f"Unknown structure: {line}")

    def _parse_array(self, line):
        """Парсинг массива."""
        try:
            return json.loads(line)
        except json.JSONDecodeError as e:
            raise SyntaxError(f"Invalid array syntax: {line}") from e

    def _parse_dict(self, line):
        """Парсинг словаря table(...)."""
        if not line.startswith("table("):
            raise SyntaxError(f"Invalid table syntax: {line}")
        content = line[6:].strip()  # Обрезаем "table("
        if content.endswith(")"):
            content = content[:-1]  # Убираем закрывающую скобку
        result = {}
        buffer = ""
        depth = 0

        for char in content:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1

            if char == "," and depth == 0:  # Разделитель пар вне вложенности
                if buffer.strip():  # Пропускаем пустые строки
                    key, value = self._split_key_value(buffer.strip())
                    result[key] = self._parse_value(value)
                buffer = ""
            else:
                buffer += char

        if buffer.strip():  # Последняя пара ключ-значение
            key, value = self._split_key_value(buffer.strip())
            result[key] = self._parse_value(value)

        return result

    def _split_key_value(self, pair):
        """Разделение строки ключ => значение."""
        if "=>" not in pair:
            raise SyntaxError(f"Invalid key-value pair: {pair}")
        key, value = pair.split("=>", 1)
        return key.strip(), value.strip()

    def _parse_value(self, value):
        """Обработка значения: строка, число, массив, словарь или константа."""
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):  # Строка
            return value[1:-1]
        if value.isdigit():  # Число
            return int(value)
        if value.startswith("["):  # Массив
            return self._parse_array(value)
        if value.startswith("table("):  # Словарь
            return self._parse_dict(value)
        if value.startswith("|") and value.endswith("|"):  # Константа
            return self._evaluate_constant(value)
        if value in self.constants:  # Константа без скобок
            return self.constants[value]
        raise SyntaxError(f"Invalid value: {value}")


def main():
    """Главная функция для запуска CLI."""
    parser = argparse.ArgumentParser(description="CLI for educational config language.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input file.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output JSON file.")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as infile:
            text = infile.read()

        config_parser = ConfigParser()
        parsed_data = config_parser.parse(text)

        with open(args.output, "w", encoding="utf-8") as outfile:
            json.dump(parsed_data, outfile, indent=4)

        print(f"Conversion successful. JSON saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
