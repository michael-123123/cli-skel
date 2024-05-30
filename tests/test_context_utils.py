import io
import sys
import unittest
from typing import Optional

from cli_skel.utils.context_utils import enable_if, compose_context_managers, redirect_outputs


class Counter:
    value: int

    def __init__(self, value: int = 0) -> None:
        self.value = value


class Ctx:
    cnt: Counter

    def __init__(self, cnt: Optional[Counter] = None) -> None:
        self.cnt = cnt if cnt else Counter()

    def __enter__(self) -> None:
        self.cnt.value += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Msg:
    def __init__(self, msg, out=None):
        self.msg = msg
        self.out = sys.stdout if out is None else out

    def __enter__(self):
        print("START", self.msg, file=self.out)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("END", self.msg, file=self.out)


class TestEnableIf(unittest.TestCase):
    def test_enable_if_false(self):
        cnt = Counter()

        with enable_if([Ctx(cnt), Ctx(cnt), Ctx(cnt)], enable=False):
            pass

        # since enable=False -- Ctx should not have changed the counter value
        self.assertEqual(cnt.value, 0)

    def test_enable_if_true(self):
        cnt = Counter()

        with enable_if([Ctx(cnt), Ctx(cnt), Ctx(cnt)], enable=True):
            pass

        # since enable=True -- Ctx should have changed the counter value
        self.assertEqual(cnt.value, 3)


class TestComposeCtx(unittest.TestCase):
    def test_compose(self):
        out = io.StringIO()
        with compose_context_managers([Msg("hello", out=out), Msg("world", out=out), Msg("!", out=out)]):
            pass

        output = out.getvalue().splitlines()
        out.close()
        self.assertEqual(
            output,
            ["START hello", "START world", "START !", "END !", "END world", "END hello"]
        )


class TestOutputRedirection(unittest.TestCase):
    def test_redirect_null(self):
        stdout, sys.stdout = sys.stdout, io.StringIO()
        with redirect_outputs(silent=True, strict=True)[2]:
            with Msg("hello???"):
                pass

        stdout, sys.stdout = sys.stdout, stdout
        output = stdout.getvalue()
        stdout.close()
        self.assertEqual(output, "")
