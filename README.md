# Лог-анализатор Django

Асинхронное cli приложение для анализа логов Django и генерации отчетов.

## Структура проекта

## Основные классы

### `LogParser`

Класс для парсинга строк логов.

**Методы:**
- `parse_log_line(line: str) -> Tuple[str, Optional[str]]`  
  Парсит строку лога, возвращает уровень логирования и handler.

### `AsyncLogFileReader`

Асинхронный класс для чтения и обработки файлов логов.

**Методы:**
- `read_file_lines(file_path: str) -> AsyncIterable[str]`  
  Асинхронно читает файл построчно.
- `parse_log_file(file_path: str) -> Dict[str, Dict[str, int]]`  
  Обрабатывает файл логов и возвращает статистику.

### `LogDataMerger`

Класс для объединения данных из нескольких файлов.

**Методы:**
- `merge(data_list: List[Dict[str, Dict[str, int]]]) -> Dict[str, Dict[str, int]]`  
  Объединяет данные из нескольких источников.

### `ReportGenerator`

Класс для генерации отчетов.

**Методы:**
- `format_out(handler: str, levels: Dict[str, int]) -> str`  
  Форматирует строку для вывода.
- `report_out(data: Dict[str, Dict[str, int]]) -> str`  
  Генерирует полный отчет.

### `AsyncLogAnalyzer`

Основной класс для анализа логов.

**Методы:**
- `validate_files(file_paths: List[str]) -> None`  
  Проверяет существование файлов.
- `analyze(file_paths: List[str], report_type: str) -> str`  
  Основной метод анализа.

## Пример использования

python -m log_analyzer.main app1.log app2.log --report handlers


Пример вывода:

Total requests: 1000

HANDLER                DEBUG   INFO    WARNING ERROR   CRITICAL
/api/v1/auth/login/    23      78      14      15      18
/api/v1/orders/        26      77      12      19      22