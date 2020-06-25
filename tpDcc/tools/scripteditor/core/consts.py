
#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains consts definitions for Script Editor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtGui import *


DEFAULT_SESSION_NAME = 'session.json'
DEFAULT_SCRIPTS_TAB_NAME = 'New Script'
INDENT_LENGTH = 4
TAB_STOP = 4
MIN_FONT_SIZE = 10
FONT_NAME = 'Courier'
FONT_STYLE = QFont.Monospace
ESCAPE_BUTTONS = [
    Qt.Key_Return, Qt.Key_Enter, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End,
    Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Delete, Qt.Key_Insert, Qt.Key_Escape
]
