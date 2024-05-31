import unittest

from cli_skel.utils.result import get_result, Ok, Err


class TestResult(unittest.TestCase):
    def test_result_ok(self):
        result = get_result(lambda: None)
        self.assertTrue(isinstance(result, Ok))
        self.assertTrue(result.value is None)

    def test_result_err(self):
        def raise_():
            raise Exception

        with self.assertRaises(Exception):
            _ = get_result(raise_)

        result = get_result(raise_, strict=False)
        self.assertTrue(isinstance(result, Err))
        with self.assertRaises(Exception):
            _ = result.value
