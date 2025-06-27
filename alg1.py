import sys
from collections import defaultdict

err = ValueError("Недопустимое выражение")


class Term:
    def __init__(self, coefficient, variables):
        self.coefficient = coefficient
        self.variables = variables

    def __eq__(self, other):
        return self.coefficient == other.coefficient and self.variables == other.variables

    def __hash__(self):
        return hash((self.coefficient, self.variables))

    def __str__(self):
        if len(self.variables) == 0:
            return str(self.coefficient)
        var_str = " * ".join(self.variables)
        if self.coefficient == 1:
            return var_str
        elif self.coefficient == -1:
            return "-1 * " + var_str
        else:
            return f"{self.coefficient} * {var_str}"


class Expression:
    def __init__(self):
        self.terms = defaultdict(int)  # Терм -> Коэффицент

    def add_term(self, term):
        key = term.variables
        self.terms[key] += term.coefficient

    def simplify(self):
        simplified = Expression()
        for vars_, coeff in self.terms.items():
            if coeff != 0:
                simplified.terms[vars_] = coeff
        return simplified

    def __add__(self, other):
        result = Expression()
        for vars_, coeff in self.terms.items():
            result.terms[vars_] += coeff
        for vars_, coeff in other.terms.items():
            result.terms[vars_] += coeff
        return result.simplify()

    def __sub__(self, other):
        result = Expression()
        for vars_, coeff in self.terms.items():
            result.terms[vars_] += coeff
        for vars_, coeff in other.terms.items():
            result.terms[vars_] -= coeff
        return result.simplify()

    def __mul__(self, other):
        result = Expression()
        for vars1, coeff1 in self.terms.items():
            for vars2, coeff2 in other.terms.items():
                combined_vars = tuple(sorted(vars1 + vars2))
                total_coeff = coeff1 * coeff2
                result.terms[combined_vars] += total_coeff
        return result.simplify()

    def to_string(self):
        parts = []
        # Сортируем по самому длинному ключу
        for vars_, coeff in sorted(self.terms.items(), key=lambda x: (-len(x[0]), x[0])):
            term = Term(coeff, vars_)
            parts.append(str(term))
        if not parts:
            return "0"
        return " + ".join(parts)


def parse_expression(tokens, pos=0):
    """
    Парсер токенов выражения
    :param tokens: Массив токенов
    :param pos: Текущий номер токена
    :return: Выражение (type Expression) и позицию
    """
    if pos >= len(tokens):
        raise err
    expr, pos = parse_additive(tokens, pos)
    return expr, pos


def parse_additive(tokens, pos):
    """
    Обработчик аддитивных операция
    :param tokens: Массив токенов
    :param pos: Текущий номер токена
    :return: Выражение (type Expression) и позицию
    """
    left_expr, pos = parse_multiplicative(tokens, pos)
    while pos < len(tokens) and tokens[pos] in ('+', '-'):
        op = tokens[pos]
        pos += 1
        right_expr, pos = parse_multiplicative(tokens, pos)
        if op == '+':
            left_expr = left_expr + right_expr
        else:
            left_expr = left_expr - right_expr
    return left_expr, pos


def parse_multiplicative(tokens, pos):
    """
    Обработчик умножения
    :param tokens: Массив токенов
    :param pos: Текущий номер токена
    :return: Выражение (type Expression) и позицию
    """
    left_expr, pos = parse_primary(tokens, pos)
    while pos < len(tokens) and tokens[pos] == '*':
        pos += 1
        right_expr, pos = parse_primary(tokens, pos)
        left_expr = left_expr * right_expr
    return left_expr, pos


def parse_primary(tokens, pos):
    """
    Обработчик термов и компоновщик цифр в числа
    :param tokens: Массив токенов
    :param pos: Текущий номер токена
    :return: Выражение (type Expression) и позицию
    """
    token = tokens[pos]
    expr = Expression()
    if token in ('x', 'y', 'z'):
        term = Term(1, (token,))
        expr.add_term(term)
        pos += 1
        return expr, pos
    elif token.isdigit() or (token == '-' and pos + 1 < len(tokens) and tokens[pos + 1].isdigit()):
        if token == '-':
            sign = -1
            pos += 1
            number = tokens[pos]
            pos += 1
            coeff = sign * int(number)
        else:
            coeff = int(token)
            pos += 1
        term = Term(coeff, tuple())
        expr.add_term(term)
        return expr, pos
    elif token == '(':
        pos += 1
        expr, pos = parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise err
        pos += 1
        return expr, pos
    else:
        raise err


def tokenize(expr_str):
    """
    Удаляет пробелы и разбивает строку на массив токенов
    :param expr_str: Выражение
    :return: Массив токенов для упрощения
    """
    expr_str = expr_str.replace(' ', '')
    tokens = []
    i = 0
    while i < len(expr_str):
        c = expr_str[i]
        if c in "+-*()xyz":
            tokens.append(c)
            if c == "-" and i + 1 < len(expr_str) and expr_str[i + 1] in "xyz":
                # добавляем умножение на единичку перед пустой переменной для упрощения
                tokens.extend(["1", "*"])
            i += 1
        elif c.isdigit():
            num = c
            # собираем число из цифр
            while i + 1 < len(expr_str) and expr_str[i + 1].isdigit():
                i += 1
                num += expr_str[i]
            tokens.append(num)
            i += 1
        else:
            raise err
    return tokens


def algebra_calc(expr_str):
    """
    Разбивает выражение на токены и упрощает его
    :param expr_str: Выражение (строка)
    :return: Упрощённое выражение (строка)
    """
    try:
        tokens = tokenize(expr_str)
        expr, pos = parse_expression(tokens)
        if pos != len(tokens):
            return err.__str__()
        return expr.to_string()
    except Exception as e:
        return e.__str__()


if __name__ == "__main__":
    # import sys
    test_inputs = [
        "2 * (3 * x + 4 * y) - 7 * y + 9",
        "z + z + 2 + 3 - 2 * z",
        "3 * ((",
        "3 * a + 5 * b + 3 * c",
        "x * y + 2 * x * y",
        "x * 5 - 5 * x",
        "5 * (x + 1)",
        "(x + 1) * (x + 1) * (x + 1)",
        "(x + (1 + x + x * (x + 1)))",
        "3 * 5 * 2 * x",
        "3 * y * x - 2 * x * y",
        "(x + 7) * 3",
        "-5 * x * y + 20 * y - 5 * z * ( - x + 25 * y)"
    ]
    test_outputs = [
        "6 * x + y + 9",
        "5",
        err.__str__(),
        err.__str__(),
        "3 * x * y",
        "0",
        "5 * x + 5",
        "x * x * x + 3 * x * x + 3 * x + 1",
        "x * x + 3 * x + 1",
        "30 * x",
        "x * y",
        "3 * x + 21",
        "-5 * x * y + 5 * x * z + -125 * y * z + 20 * y"
    ]

    for i, inp in enumerate(test_inputs):
        print("=" * 10, i + 1, sep="\n")
        if (simplified_expression := algebra_calc(inp)) == test_outputs[i]:
            print("+")
        else:
            print("-")
        print(
            f"Вход: {inp}",
            f"Результат функции: {simplified_expression}",
            f"Ожидаемый результат: {test_outputs[i]}",
            sep="\n")

    for line in sys.stdin:
        print(algebra_calc(line.strip()))