import sys
import pytest
from build_database import DatabaseBuilder
from unittest.mock import Mock
import csv

TEST_FILE = 'test_build_database.csv'


class MockFileObject:
    pass


class TestClass:

    def test_quotation_mark(self):

        f_output = MockFileObject
        f_output.write = Mock()

        with open(TEST_FILE, 'r') as f_input:
            builder = DatabaseBuilder(f_input, f_output)
            builder.build()

        for call in f_output.write.call_args_list:
            args, kwargs = call
            assert len(args) == 1
            line = args[0]
            # Remove escaped quotation marks
            line = line.replace(r'\"', r'')
            assert (line.count(r'"') == 0 or line.count(r'"') == 2)
