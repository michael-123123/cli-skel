import importlib.metadata
import logging
import pathlib


__version__ = importlib.metadata.version("cli-skel")
""" Package version -- read only value """


__version_tuple__ = tuple(__version__.split('.'))
""" Package version tuple -- read only value """


__package_root__ = pathlib.Path(__file__).parent.parent
""" Path of package root in filesystem -- read only value """


__package_logger_name__ = "cli_skel"
""" Name of default package logger -- read only value """


__package_default_log_level__ = logging.WARNING
""" Default log level for package logger -- read only value """


from . import argparse_skel
from . import cmd_skel
from . import utils
