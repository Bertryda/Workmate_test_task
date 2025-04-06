import argparse
import os
import re
from typing import Dict, List, Tuple, Optional, Iterable

from config import LOG_PATTERN, LOG_LEVELS, HANDLER_PATTERN

def read_file_lines(file_path: str) -> Iterable[str]:
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
    # print(line)
    level = re.search(LOG_PATTERN, line)
    handler = re.search(HANDLER_PATTERN, line)

    if handler:
        level = level.group()
        handler = handler.group()
        return level, handler
    return level.group(), None


def parse_log_file(file_path: str) -> Dict[str, Dict[str, int]]:
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

    for line in read_file_lines(file_path):
        level, handler = parse_log_line(line)
        if handler and handler not in data:
            data[handler] = {level_info: 0 for level_info in LOG_LEVELS}
            cache = handler
        if handler:
            data[handler][level] += 1
            cache = handler
        if not handler:
            data[cache][level] += 1
            
    return data


def parse_log_files(
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
    return result


def merge_data(
    data_list: List[Dict[str, Dict[str, int]]]
) -> Dict[str, Dict[str, int]]:
    """
    Функция, созданная для работы с parse_log_files для получения 
    общей статистики по файлам логов

    Args:
        data_list (List[Dict[str, Dict[str, int]]]): Общие данные из
        файлов логов

    Returns:
        Dict[str, Dict[str, int]]: Возвращает итоговый словарь с 
        информацией о логах
    """
    final_result = {}
    
    for data in data_list:
        for handler, levels in data.items():
            if handler not in final_result:
                final_result[handler] = {level_info: 0 for level_info in LOG_LEVELS}
            for level, count in levels.items():
                final_result[handler][level] += count
    return final_result


def format_out(handler: str, levels: Dict[str, int]) -> str:
    """
    Функция Форматирует строку вывода инфо для одного handler,
    создано для использования в функции report_out

    Args:
        handler (str): сам handler вывода
        levels (Dict[str, int]): инфо по каждому уровню логирования

    Returns:
        str: возвращает результирующую строку
    """
    handler_out = handler[:25].ljust(25)
    levels_out = [str(levels[level]).ljust(8) for level in LOG_LEVELS]
    return handler_out + "\t" + "\t".join(levels_out)


def report_out(final_result: Dict[str, Dict[str, int]]) -> str:
    """
    Функция генерации отчета о handlers на основании вайлов логов

    Args:
        final_result (Dict[str, Dict[str, int]]): итоговое инфо полученное
        из файлов логов

    Returns:
        str: возвращает строку вывода
    """
    handler_sorted = sorted(final_result.keys())
    header = "HANDLER".ljust(25) + "\t" + "\t".join(level.ljust(8) for level in LOG_LEVELS)
    lines = [header]
    
    all_requests = 0
    request_by_level = {level: 0 for level in LOG_LEVELS}
    
    for handler in handler_sorted:
        levels = final_result[handler]
        lines.append(format_out(handler, levels))
        
        for level in LOG_LEVELS:
            k = levels[level]
            request_by_level[level] += k
            all_requests += k
            
    all_req_line = "".ljust(25) + "\t" + "\t".join(
        str(request_by_level[level]).ljust(8) for level in LOG_LEVELS
    )
    lines.append(all_req_line)
    
    return ("\n".join([
        f"Total requests: {all_requests}",
        "",
        *lines
    ]))
    
    
def validate_files(file_paths: List[str]) -> None:
    """Проводит валидацию файлов"""
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"file {file_path} not found") 
        
        
def async_main():
    parser = argparse.ArgumentParser(
        description="Processing django log files and creating a report."
    )   
    parser.add_argument(
        "log_files",
        nargs="+",
        help="Specify the paths to the log files"
    )
    parser.add_argument(
        "--report",
        choices=["handlers"],
        required=True,
        help="Name of the report"
    )
    
    args = parser.parse_args()
    
    try:
        validate_files(args.log_files)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 
    
    data_list = parse_log_files(args.log_files)
    merged_data_list = merge_data(data_list)
        
    if args.report == "handlers": 
        report = report_out(merged_data_list)
    print(report)
        
        
def main():
    async_main()
    

if __name__ == "__main__":
    main()
    
    




    
        


            
            
