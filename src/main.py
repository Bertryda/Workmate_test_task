import argparse
import os
import re
import asyncio
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, AsyncIterable

from .config import LOG_PATTERN


async def read_file_lines(file_path: str) -> AsyncIterable[str]:
    """
    Функция асинхронно и и построчно читает файл, доступ 
    к которому происходит через file_path

    Args:
        file_path (str): Путь к файлу с логами

    Returns:
        AsyncIterable[str]: Возвращает корутину после обработки файла
    """
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield line
            

def parse_log_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Функция для преобразования строки в кортеж, 
    где первый элемент: уровень логирования,
    второй элемент: заголовок,

    Args:
        line (str): строка, в дальнейшем будет передеваться 
        функцией read_file_lines

    Returns:
        Tuple[Optional[str], Optional[str]]: Возвращает кортеж с 
        указанными выше значениями, Optional необходим для 
        дальнейшей проверки
    """
    
    cache = LOG_PATTERN.match(line.strip())
    
    if cache:
        level = cache.group("level").upper()
        handler = cache.group("handler")
        return level, handler
    return None, None


async def parse_log_file(file_path: str) -> Dict[str, Dict[str, int]]:
    """
    Функция асинхронно обрабатывает файл логов и возвращает
    полученную статистику

    Args:
        file_path (str): путь к файлу, который анализируется

    Returns:
        Dict[str, Dict[str, int]]: возвращается словарь с вложенными 
        словарями для каждого уровня
    """
    data = {}

    async for line in read_file_lines(file_path):
        level, handler = parse_log_line(line)
        if handler and handler not in data:
            data[handler] = {}
        if level in LOG_LEVELS and handler:
            stats[handler][level] += 1
            
    return data


async def parse_log_files(
        file_path_list: List[str],
    ) -> List[Dict[str, Dict[str, int]]]:
    """
    Функция для асинхронной обработки нескольких файлов логов

    Args:
        file_path_list (List[str]): список путей к файлам

    Returns:
        List[Dict[str, Dict[str, int]]]: результат тот же что и в функции
        parse_log_file но несколько значений
    """
    result = [parse_log_file(file_path) for file_path in file_path_list]
    return await asyncio.gather(*result)




    
        


            
            
