import sys
import pytest
from build_database import DatabaseBuilder
from unittest.mock import Mock
import csv

TEST_QUOTATION_MARK_CSV = 'build_database_test_files/test_quotation_mark.csv'
TEST_REDIRECTING = 'build_database_test_files/test_redirecting.csv'


class MockFileObject:
    pass


class TestClass:

    def test_quotation_mark(self):

        f_output = MockFileObject
        f_output.write = Mock()

        with open(TEST_QUOTATION_MARK_CSV, 'r') as f_input:
            builder = DatabaseBuilder(f_input, f_output, 'nutriscore.model')
            builder.build()

        for call in f_output.write.call_args_list:
            args, kwargs = call
            assert len(args) == 1
            line = args[0]
            # Remove escaped quotation marks
            line = line.replace(r'\"', r'')
            assert (line.count(r'"') == 0 or line.count(r'"') == 2)

    def test_redirecting(self):

        f_output = MockFileObject
        f_output.write = Mock()

        with open(TEST_REDIRECTING, 'r') as f_input:
            builder = DatabaseBuilder(f_input, f_output, 'nutriscore.model')
            builder.build(build_ingredients=False)

        # DatabaseBuilder should skip when redirection is detected (i.e. a
        # mismatching id and url from the csv)
        f_output.write.assert_not_called()
