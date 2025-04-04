import re

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

LOG_PATTERN = re.compile(
    r"^\[(?P<timestamp>.+?)\] "
    r"\[(?P<level>.+?)\] "
    r"\[django\.requests\] "
    r"\[(?P<handler>.+?)\]"
)