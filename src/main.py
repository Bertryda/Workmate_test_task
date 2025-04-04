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



            
            
