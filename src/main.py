import argparse
import asyncio
import os
from re import Match, search
from typing import Dict, List, Tuple, Optional, AsyncIterable


class LogParser:
    """Класс для парсинга строк логов"""
    def __init__(self, log_pattern: str, handler_pattern: str, log_levels: List[str]):
        self.log_pattern = log_pattern
        self.handler_pattern = handler_pattern
        self.log_levels = log_levels

    def parse_log_line(self, line: str) -> Tuple[str, Optional[str]]:
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
        level = search(self.log_pattern, line).group()
        handler = search(self.handler_pattern, line)
        if handler:
            handler = handler.group()
            return level, handler
        return level, None


class AsyncLogFileReader:
    """Асинхронный класс для чтения и обработки файлов логов"""
    def __init__(self, parser: LogParser):
        self.parser = parser

    async def read_file_lines(self, file_path: str) -> AsyncIterable[str]:
        """
        Функция асинхронно и и построчно читает файл, доступ 
        к которому происходит через file_path

        Args:
            file_path (str): Путь к файлу с логами

        Returns:
            AsyncIterable[str]: Возвращает корутину после обработки файла
        """
        with open(file_path, mode='r', encoding='utf-8') as f:
            for line in f:
                yield line

    async def parse_log_file(self, file_path: str) -> Dict[str, Dict[str, int]]:
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
        cache = None

        async for line in self.read_file_lines(file_path):
            level, handler = self.parser.parse_log_line(line)
            
            if handler and handler not in data:
                data[handler] = {level_info: 0 for level_info in self.parser.log_levels}
                cache = handler
            
            if handler:
                data[handler][level] += 1
                cache = handler
            
            if not handler and cache:
                data[cache][level] += 1
                
        return data


class LogDataMerger:
    """Класс для объединения данных из нескольких файлов"""
    def __init__(self, log_levels: List[str]):
        self.log_levels = log_levels

    def merge(self, data_list: List[Dict[str, Dict[str, int]]]) -> Dict[str, Dict[str, int]]:
        """
        Функция, созданная для для получения общей статистики по файлам логов

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
                    final_result[handler] = {level: 0 for level in self.log_levels}
                for level, count in levels.items():
                    if level in self.log_levels:  
                        final_result[handler][level] += count
        return final_result


class ReportGenerator:
    """Класс для генерации отчетов"""
    def __init__(self, log_levels: List[str]):
        self.log_levels = log_levels

    def format_out(self, handler: str, levels: Dict[str, int]) -> str:
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
        levels_out = [str(levels.get(level, 0)).ljust(8) for level in self.log_levels]
        return handler_out + "\t" + "\t".join(levels_out)

    def report_out(self, data: Dict[str, Dict[str, int]]) -> str:
        """
        Функция генерации отчета о handlers на основании вайлов логов

        Args:
            final_result (Dict[str, Dict[str, int]]): итоговое инфо полученное
            из файлов логов

        Returns:
            str: возвращает строку вывода
        """
        sorted_handlers = sorted(data.keys())
        header = "HANDLER".ljust(25) + "\t" + "\t".join(level.ljust(8) for level in self.log_levels)
        lines = [header]
        
        total_requests = 0
        requests_by_level = {level: 0 for level in self.log_levels}
        
        for handler in sorted_handlers:
            levels = data[handler]
            lines.append(self.format_out(handler, levels))
            
            for level in self.log_levels:
                count = levels.get(level, 0)
                requests_by_level[level] += count
                total_requests += count
                
        total_line = "".ljust(25) + "\t" + "\t".join(
            str(requests_by_level[level]).ljust(8) for level in self.log_levels
        )
        lines.append(total_line)
        
        return "\n".join([
            f"Total requests: {total_requests}",
            "",
            *lines
        ])


class AsyncLogAnalyzer:
    """Асинхронный класс для анализа логов"""
    def __init__(self, config: Dict):
        self.config = config
        self.parser = LogParser(config['LOG_PATTERN'], config['HANDLER_PATTERN'], config['LOG_LEVELS'])
        self.reader = AsyncLogFileReader(self.parser)
        self.merger = LogDataMerger(config['LOG_LEVELS'])
        self.reporter = ReportGenerator(config['LOG_LEVELS'])

    async def validate_files(self, file_paths: List[str]) -> None:
        """Функция для проверки существования файлов

        Args:
            file_paths (List[str]): пути к обрабатываемым файлам

        Raises:
            FileNotFoundError: вызывается, если файл не найден
        """
        for file_path in file_paths:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File {file_path} not found")

    async def analyze(self, file_paths: List[str], report_type: str) -> str:
        """Асинхронный основной метод для анализа логов

        Args:
            file_paths (List[str]): пути к файлам для анализа
            report_type (str): название отчета по логам

        Raises:
            ValueError: возникает при неправильном указании названия

        Returns:
            str: возвращает саму строку для вывода информации
        """
        await self.validate_files(file_paths)
        
        tasks = [self.reader.parse_log_file(file_path) for file_path in file_paths]
        data_list = await asyncio.gather(*tasks)
        
        merged_data = self.merger.merge(data_list)
        
        if report_type == "handlers":
            return self.reporter.report_out(merged_data)
        
        raise ValueError(f"Unknown report type: {report_type}")


async def async_main():
    from config import LOG_PATTERN, HANDLER_PATTERN, LOG_LEVELS
    
    config = {
        'LOG_PATTERN': LOG_PATTERN,
        'HANDLER_PATTERN': HANDLER_PATTERN,
        'LOG_LEVELS': LOG_LEVELS
    }
    
    parser = argparse.ArgumentParser(
        description="Process Django log files and generate reports."
    )
    parser.add_argument(
        "log_files", 
        nargs="+", 
        help="Paths to log files"
    )
    parser.add_argument(
        "--report", 
        choices=["handlers"], 
        required=True, 
        help="Type of report"
    )
    
    args = parser.parse_args()
    
    try:
        analyzer = AsyncLogAnalyzer(config)
        report = await analyzer.analyze(args.log_files, args.report)
        print(report)
    except Exception as e:
        print(f"Error: {e}")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()