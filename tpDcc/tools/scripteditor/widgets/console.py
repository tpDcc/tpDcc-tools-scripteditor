
#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains output console widget for tpDcc-tools-scripteditor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *


class OutputConsole(QTextEdit, object):
    def __init__(self, parent=None):
        super(OutputConsole, self).__init__(parent)

        self.setWordWrapMode(QTextOption.NoWrap)
        font = QFont('Courier')
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self._font_size = 14
        self.document().setDefaultFont(QFont('Courier', self._font_size, QFont.Monospace))
        metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopWidth(4 * metrics.width(' '))
        self.setMouseTracking(True)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def wheelEvent(self, event):
        """
        Overrides wheelEvent function to allow the change of font size when the user scrolls mouse wheel up and down
        :param event: QWheelEvent
        """

        if event.modifiers() == Qt.ControlModifier:
            if event.delta() > 0:
                self.change_font_size(True)
            else:
                self.change_font_size(False)
        QTextBrowser.wheelEvent(self, event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def show_message(self, msg):
        """
        Shows a new message in the console
        :param msg: str, message to show in the console
        """

        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        cursor.insertText(str(msg)+'\n')
        self.setTextCursor(cursor)
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()

    def set_text_edit_font_size(self, size):
        """
        Sets the font size of the text
        :param size: float
        """

        pass

        # self.setStyleSheet('''
        # QTextEdit
        # {
        #     font-size: {}px
        # }
        # '''.format(size))

    def change_font_size(self, up):
        """
        Increases/Decreases the font size of the text
        :param up: bool, Whether to increase or decrease the font size
        """

        font = self.font()
        font_size = font.pointSize()
        if up:
            font_size = min(30, font_size + 1)
        else:
            font_size = max(8, font_size - 1)
        font.setPointSize(font_size)
        self.setFont(font)
