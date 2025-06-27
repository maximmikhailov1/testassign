import re
from collections import defaultdict
from html import unescape
import os
from typing import Any


def remove_html_tags(text: str):
    """
    Удаляет все HTML-теги и содержимое тегов style, script и textarea
    """
    # Удаляем содержимое тегов <script> и <style>
    text = re.sub(r'<(script|style|textarea)[^>]*>.*?</\1>', ' ', text, flags=re.DOTALL)
    # Удаляем все оставшиеся HTML-теги
    text = re.sub(r'<[^>]+>', ' ', text)
    # Заменяем множественные пробелы на один
    text = re.sub(r'\s+', ' ', text)
    return unescape(text).strip()

def get_words(text: str):
    """Извлекает слова из текста (только буквы, минимум 3 символа)"""
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]{3,}\b', text, flags=re.IGNORECASE)
    return [word.lower() for word in words]


def count_words(words: list[str]) -> defaultdict[str, int]:
    """Подсчитывает частоту слов"""
    word_counts = defaultdict(int)
    for word in words:
        word_counts[word] += 1
    return word_counts


def get_top_words(file_path:str, n: int=15) -> list[tuple[str, int]]:
    """
    :param file_path: путь к файлу
    :param n: кол-во слов
    :returns: топ-N самых частых слов
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")

    text_without_tags = remove_html_tags(html_content)
    words = get_words(text_without_tags)
    word_counts = count_words(words)
    top_words = sorted(word_counts.items(), key=lambda x: (-x[1], x[0]))
    return top_words[:n]



if __name__ == "__main__":
    file_path = input("Введите путь к HTML файлу: ")
    if not file_path.endswith(".html"):
        file_path = file_path.strip() + ".html"

    while not os.path.exists(file_path):
        file_path = input("Неверный путь. Введите путь к HTML файлу: ")
        if not file_path.endswith(".html"):
            file_path = file_path.strip() + ".html"

    top_words = get_top_words(file_path)

    for word, count in top_words:
        print(f"{word:<20} {count:>10}")