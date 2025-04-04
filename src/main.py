import argparse
import os
import re
import asyncio
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, AsyncIterable


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
            
            
