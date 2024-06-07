import unittest


class TestImportLib(unittest.TestCase):
    def test_imports(self):
        import cli_skel
        self.assertTrue(isinstance(cli_skel.__version__, str))
