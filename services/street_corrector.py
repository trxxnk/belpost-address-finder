from rapidfuzz import fuzz, process
from typing import Optional

def correct_street_name(input_street: str, correct_streets_file: str, threshold: int = 80) -> str:
    """
    Исправляет опечатки в названии улицы с использованием fuzzy matching.
    
    Args:
        input_street (str): Входное название улицы для проверки
        correct_streets_file (str): Путь к файлу с корректными названиями улиц
        threshold (int): Пороговое значение совпадения (0-100), по умолчанию 80
    
    Returns:
        str: Исправленное название улицы или исходное, если совпадение слабое
    """
    try:
        # Загружаем корректные названия улиц из файла
        with open(correct_streets_file, 'r', encoding='utf-8') as file:
            correct_streets = [line.strip().lower() for line in file if line.strip()]
        
        if not correct_streets:
            return input_street
        
        # Ищем лучшее совпадение
        best_match, score, _ = process.extractOne(input_street.lower(), correct_streets, scorer=fuzz.ratio)
        
        # Если совпадение выше порога, возвращаем исправленное название
        if score >= threshold:
            print(f"[DEBUG] Исправление улицы: '{input_street}' -> '{best_match}' (score: {score}%)")
            return best_match.lower().capitalize()
        else:
            print(f"[DEBUG] Нет совпадения: '{input_street}' -> '{best_match}' (score: {score}%)")
            return input_street
            
    except FileNotFoundError:
        print(f"[ERROR]Файл {correct_streets_file} не найден")
        return input_street
    except Exception as e:
        print(f"[ERROR]Произошла ошибка: {e}")
        return input_street