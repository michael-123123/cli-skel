import unittest
from copy import copy, deepcopy

from cli_skel.utils.sentinels import MissingType


class TestSentinels(unittest.TestCase):
    def _test_missing_obj(self, missing: MissingType):
        self.assertTrue(missing == MissingType(missing.name))
        self.assertTrue(missing is MissingType(missing.name))
        self.assertTrue(missing == copy(MissingType(missing.name)))
        self.assertTrue(missing is copy(MissingType(missing.name)))
        self.assertTrue(missing == deepcopy(MissingType(missing.name)))
        self.assertTrue(missing is deepcopy(MissingType(missing.name)))

    def test_missing_basics(self):
        self._test_missing_obj(MissingType())

    def test_missing_named(self):
        missing1 = MissingType('hello')
        self._test_missing_obj(missing1)

        missing2 = MissingType('world')
        self._test_missing_obj(missing2)

        self.assertTrue(missing1 is not missing2)
        self.assertTrue(missing1 != missing2)
        self.assertTrue(missing1 is not copy(missing2))
        self.assertTrue(missing1 != copy(missing2))
        self.assertTrue(missing1 is not deepcopy(missing2))
        self.assertTrue(missing1 != deepcopy(missing2))

    def test_missing_str(self):
        missing1 = MissingType('bye')
        self.assertTrue(str(missing1).casefold().startswith('missing'))
        self.assertTrue(repr(missing1).casefold().startswith('missing'))
