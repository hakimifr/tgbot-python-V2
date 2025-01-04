# SPDX-License-Identifier: GPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright (c) 2024, Firdaus Hakimi <hakimifirdaus944@gmail.com>

import os
import logging

GLOBAL_DEBUG: bool = False
if os.getenv("TGBOT_DEBUG") is not None:
    GLOBAL_DEBUG = True

log_additional_args: dict = {"filename": "bot.log",
                             "level": logging.INFO}
if GLOBAL_DEBUG:
    log_additional_args.clear()
    log_additional_args.update({"level": logging.DEBUG})


#
# Adapted from https://stackoverflow.com/a/56944256
#
class ColouredFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[0;32m"
    blue = "\x1b[0;34m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record: logging.LogRecord):
        if record.name.startswith("httpx") and record.levelno <= logging.INFO:
            return ""

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    **log_additional_args)


for handler in logging.root.handlers:
    if issubclass(logging.StreamHandler, type(handler)):
        logging.root.removeHandler(handler)

_sh = logging.StreamHandler()
_sh.setFormatter(ColouredFormatter())
logging.root.addHandler(_sh)
logging.getLogger(__name__).info("Coloured log output initialized")
