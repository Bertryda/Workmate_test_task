from typing import Dict, List, Tuple
import asyncio
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import (
    LogParser,
    AsyncLogFileReader,
    LogDataMerger,
    ReportGenerator,
    AsyncLogAnalyzer
)
from src.config import LOG_LEVELS, HANDLER_PATTERN, LOG_PATTERN


# Фикстуры
@pytest.fixture
def sample_config():
    return {
        'log_pattern': LOG_PATTERN,
        'handler_pattern': HANDLER_PATTERN,
        'log_levels': LOG_LEVELS
    }


@pytest.fixture
def sample_log_lines():
    return [
        "[DEBUG] [/api/v1/test/] Test message",
        "[INFO] [/api/v1/test/] Another message",
        "[WARNING] No handler here",
        "[ERROR] [/api/v1/error/] Error message",
        "[CRITICAL] [/api/v1/critical/] Critical error"
    ]


# Тесты для LogParser
class TestLogParser:
    def test_init(self, sample_config):
        parser = LogParser(**sample_config)
        assert parser.log_pattern == sample_config['log_pattern']
        assert parser.handler_pattern == sample_config['handler_pattern']
        assert parser.log_levels == sample_config['log_levels']


    @pytest.mark.parametrize("line,expected_level,expected_handler", [
        ("[DEBUG] [/api/v1/test/] Test", "DEBUG", "/api/v1/test/"),
        ("[INFO] [/api/v1/user/] User", "INFO", "/api/v1/user/"),
        ("[WARNING] No handler", "WARNING", None),
        ("[ERROR] [/api/v1/error/] Error", "ERROR", "/api/v1/error/"),
        ("[CRITICAL] [/api/v1/crit/] Crit", "CRITICAL", "/api/v1/crit/"),
    ])
    
    def test_parse_log_line(self, sample_config, line, expected_level, expected_handler):
        parser = LogParser(**sample_config)
        level, handler = parser.parse_log_line(line)
        assert level == expected_level
        assert handler == expected_handler


    def test_parse_log_line_empty(self, sample_config):
        parser = LogParser(**sample_config)
        with pytest.raises(AttributeError):
            parser.parse_log_line("")


# Тесты для AsyncLogFileReader
class TestAsyncLogFileReader:
    @pytest.mark.asyncio
    async def test_init(self, sample_config):
        parser = LogParser(**sample_config)
        reader = AsyncLogFileReader(parser)
        assert reader.parser == parser


    @pytest.mark.asyncio
    async def test_empty_file(self, tmp_path, sample_config):
        test_file = tmp_path / "empty.log"
        test_file.write_text("")
        
        parser = LogParser(**sample_config)
        reader = AsyncLogFileReader(parser)
        result = await reader.parse_log_file(str(test_file))
        assert result == {}


    @pytest.mark.asyncio
    async def test_file_without_handlers(self, tmp_path, sample_config):
        test_file = tmp_path / "no_handlers.log"
        test_file.write_text("[INFO] No handler\n[WARNING] Another no handler")
        
        
        parser = LogParser(**sample_config)
        reader = AsyncLogFileReader(parser)
        result = await reader.parse_log_file(str(test_file))
        assert result == {}


# Тесты для LogDataMerger
class TestLogDataMerger:
    def test_init(self, sample_config):
        merger = LogDataMerger(sample_config['log_levels'])
        assert merger.log_levels == sample_config['log_levels']


    def test_merge_empty(self, sample_config):
        merger = LogDataMerger(sample_config['log_levels'])
        assert merger.merge([]) == {}


    def test_merge_multiple(self, sample_config):
        merger = LogDataMerger(sample_config['log_levels'])
        data1 = {'/test': {'DEBUG': 1, 'INFO': 2}}
        data2 = {'/test': {'DEBUG': 3, 'ERROR': 1}}
        expected = {'/test': {'DEBUG': 4, 'INFO': 2, 'ERROR': 1, 
                            'WARNING': 0, 'CRITICAL': 0}}
        assert merger.merge([data1, data2]) == expected


# Тесты для ReportGenerator
class TestReportGenerator:
    def test_init(self, sample_config):
        generator = ReportGenerator(sample_config['log_levels'])
        assert generator.log_levels == sample_config['log_levels']


    def test_format_out(self, sample_config):
        generator = ReportGenerator(sample_config['log_levels'])
        formatted = generator.format_out(
            '/api/v1/test/', 
            {'DEBUG': 1, 'INFO': 2}
        )
        assert '/api/v1/test/' in formatted
        assert '1' in formatted  # DEBUG
        assert '2' in formatted  # INFO


    def test_report_out_empty(self, sample_config):
        generator = ReportGenerator(sample_config['log_levels'])
        report = generator.report_out({})
        assert "Total requests: 0" in report
        assert "HANDLER" in report  # Header


    def test_report_out_with_data(self, sample_config):
        generator = ReportGenerator(sample_config['log_levels'])
        data = {
            '/api/v1/test/': {'DEBUG': 1, 'INFO': 2},
            '/api/v1/error/': {'ERROR': 3}
        }
        report = generator.report_out(data)
        assert "Total requests: 6" in report
        assert '/api/v1/test/' in report
        assert '/api/v1/error/' in report


# Тесты для AsyncLogAnalyzer
class TestAsyncLogAnalyzer:
    @pytest.mark.asyncio
    async def test_init(self, sample_config):
        analyzer = AsyncLogAnalyzer(sample_config)
        assert analyzer.config == sample_config
        assert isinstance(analyzer.parser, LogParser)
        assert isinstance(analyzer.reader, AsyncLogFileReader)
        assert isinstance(analyzer.merger, LogDataMerger)
        assert isinstance(analyzer.reporter, ReportGenerator)


    @pytest.mark.asyncio
    async def test_validate_files(self, tmp_path, sample_config):
        test_file = tmp_path / "exists.log"
        test_file.write_text("test")
        
        analyzer = AsyncLogAnalyzer(sample_config)
        await analyzer.validate_files([str(test_file)])  # Should not raise


    @pytest.mark.asyncio
    async def test_validate_files_missing(self, sample_config):
        analyzer = AsyncLogAnalyzer(sample_config)
        with pytest.raises(FileNotFoundError):
            await analyzer.validate_files(["nonexistent.log"])


    @pytest.mark.asyncio
    async def test_analyze(self, tmp_path, sample_config):
        test_file = tmp_path / "test.log"
        test_file.write_text("[INFO] [/api/v1/test/] Test\n[ERROR] [/api/v1/error/] Error")
        
        analyzer = AsyncLogAnalyzer(sample_config)
        report = await analyzer.analyze([str(test_file)], "handlers")
        
        assert "Total requests: 2" in report
        assert "/api/v1/test/" in report
        assert "/api/v1/error/" in report