#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

if hasattr(logging, 'NullHandler'):
    NullHandler = logging.NullHandler
else:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(30, 38)

# The background is set with 40 plus the number of the color, and the
# foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = '\033[0m'
COLOR_SEQ = '\033[1;{0}m'
BOLD_SEQ = '\033[1m'
COLOR_SENTENCE = COLOR_SEQ + '{1}' + RESET_SEQ


def colorize(text, color):
    return COLOR_SENTENCE.format(color, text)

DEFAULT_COLORS = {
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': BLUE,
    'CRITICAL': RED,
    'ERROR': MAGENTA
}


class ColoredFormatter(logging.Formatter, object):
    def __init__(self, format, colors=None, default=None):
        super(ColoredFormatter, self).__init__(format)
        self._colors = colors or DEFAULT_COLORS
        self._default = default or WHITE

    def colorize(self, record, text):
        color = self._colors.get(record.levelname, self._default)
        return colorize(text, color)


class ColoredLevelFormatter(ColoredFormatter):
    def format(self, record):
        record.levelname = self.colorize(record, record.levelname)
        return super(ColoredLevelFormatter, self).format(record)


class ColoredLineFormatter(ColoredFormatter):
    def format(self, record):
        return self.colorize(record, super(ColoredLineFormatter, self).format(record))
