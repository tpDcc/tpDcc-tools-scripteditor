#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains script widget for tpDcc-tools-scripteditor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import tabs

from tpDcc.tools.scripteditor.core import consts


class ScriptsTab(tabs.BaseEditableTabWidget, object):
    def __init__(self, script=None, add_empty_tab=True, parent=None):
        super(ScriptsTab, self).__init__(parent=parent)

        self._last_search = [0, None]
        self._parent = parent
        self._desktop = QApplication.desktop()
        self._ask_save_before_close = True

        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.currentChanged.connect(self._on_hide_all_completers)
        self.tabBar().customContextMenuRequested.connect(self._on_open_menu)
        self.tabBar().addTabClicked.connect(self._on_add_new_tab)

        if script and os.path.isfile(script):
            self.add_new_tab(os.path.basename(script), script)
        else:
            if add_empty_tab:
                self.add_new_tab()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def removeTab(self, index):
        """
        Overrides removeTab function to ask persmission to the user before closing the tab
        :param index: int, index of the tab we want to close
        """

        if self.count() > 1:
            if self.get_current_text(tab_index=index).strip():
                if self._ask_save_before_close:
                    if qtutils.show_question(
                            title='Closing Script',
                            question='Close this tab without saving?\n'.format(self.tabText(index)),
                            parent=None) == QMessageBox.Yes:
                        super(ScriptsTab, self).removeTab(index)
                else:
                    super(ScriptsTab, self).removeTab(index)
            else:
                super(ScriptsTab, self).removeTab(index)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def add_new_tab(self, script_name=consts.DEFAULT_SCRIPTS_TAB_NAME, script_file=''):
        """
        Adds a new empty tab into the scripts tab
        :param script_name: str
        :param script_name: str
        :return: ScriptCodeEditor
        """

        script_widget = ScriptWidget(file_path=script_file, parent=self._parent, desktop=self._desktop)
        script_widget.editor.scriptSaved.connect(self._on_save_session)
        self.addTab(script_widget, script_name)
        script_widget.editor.moveCursor(QTextCursor.Start)
        self.setCurrentIndex(self.count() - 1)

        return script_widget.editor

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _on_hide_all_completers(self):
        pass

    def _on_open_menu(self):
        pass

    def _on_add_new_tab(self):
        pass
    
    def _on_save_session(self):
        pass


class ScriptWidget(base.BaseWidget, object):
    def __init__(self, file_path, desktop=None, parent=None):

        self._file_path = file_path
        self._desktop = desktop
        self._parent = parent
        self._editor = None

        super(ScriptWidget, self).__init__(parent=parent)

        self._fill_editor()

    @property
    def file_path(self):
        return self._file_path

    @property
    def editor(self):
        return self._editor

    def get_main_layout(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        return main_layout

    def ui(self):
        super(ScriptWidget, self).ui()

        self._editor = ScriptEditor(desktop=self._desktop, parent=self._parent)
        self._line_num = ScriptEditorNumberBar(editor=self._editor, parent=self)

        self.main_layout.addWidget(self._line_num)
        self.main_layout.addWidget(self._editor)


    def _fill_editor(self):
        pass


class ScriptEditor(QTextEdit, object):

    scriptExecuted = Signal()
    scriptSaved = Signal()
    scriptInput = Signal()

    def __init__(self, desktop=None, parent=None):
        super(ScriptEditor, self).__init__(parent)

        self._font_size = 12
        self._desktop = desktop
        self._parent = parent
        self._syntax_highlighter = None

        font = QFont(consts.FONT_NAME)
        font.setStyleHint(consts.FONT_STYLE)
        font.setFixedPitch(True)
        self.setFont(font)
        self.document().setDefaultFont(QFont(consts.FONT_NAME, consts.MIN_FONT_SIZE, consts.FONT_STYLE))
        metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopWidth(consts.TAB_STOP * metrics.width(' '))
        self.setAcceptDrops(True)
        self.setWordWrapMode(QTextOption.NoWrap)

    def set_settings(self, settings):
        if not settings:
            return

        self.apply_highlighter(settings.get('theme'))

    def apply_highlighter(self, theme=None):
        """
        Applies highlighter with the settings of the given theme
        :param theme: str
        """

        pass


class ScriptEditorNumberBar(QWidget, object):
    def __init__(self, editor, parent=None):
        super(ScriptEditorNumberBar, self).__init__(parent)

        self.editor = editor
        self.highest_line = 0
        self.setMinimumWidth(30)
        self.bg = None

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def eventFilter(self, object, event):

        # Update the liner numbers for all events on the text edit and the viepwort
        # This is easier that connecting all necessary signals
        if object in (self.editor, self.editor.viewport()):
            self.update()
            return False
        return QWidget.eventFilter(object, event)

    def update(self, *args):
        """
        Updates the number bar to display the current set of numbers and adjusts the width of the
        number bar if necessary
        """

        font_size = self.editor.font().pointSize()
        width = (self.fontMetrics().width(str(self.highest_line)) + 7) * (font_size/13.0)
        if self.width() != width and width > 10:
            self.setFixedWidth(width)
        bg = self.palette().brush(QPalette.Normal, QPalette.Window).color().toHsv()
        v = bg.value()
        v = int(bg.value()*0.8) if v > 20 else int(bg.value() * 1.1)
        self.bg = QColor.fromHsv(bg.hue(), bg.saturation(), v)
        super(ScriptEditorNumberBar, self).update(*args)

    def paintEvent(self, event):
        contents_y = self.editor.verticalScrollBar().value()
        page_bottom = contents_y + self.editor.viewport().height()
        font_metrics = self.fontMetrics()
        current_block = self.editor.document().findBlock(self.editor.textCursor().position())
        painter = QPainter(self)
        line_count = 0

        # Iterate over all text blocks in the document
        block = self.editor.document().begin()
        font_size = self.editor.font().pointSize()
        font = painter.font()
        font.setPixelSize(font_size)
        offset = font_metrics.ascent() + font_metrics.descent()
        color = painter.pen().color()
        painter.setFont(font)
        align = Qt.AlignRight
        while block.isValid():
            line_count += 1

            # Get top left position of the block in the document and check if the position of the block is
            # outside of the visible area
            position = self.editor.document().documentLayout().blockBoundingRect(block).topLeft()
            if position.y() == page_bottom:
                break

            rect = QRect(0, round(position.y()) - contents_y, self.width()-5, font_size + offset)

            # Draw line rect
            if block == current_block:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(self.bg))
                painter.drawRect(QRect(0, round(position.y()) - contents_y, self.width(), font_size + (offset/2)))
                painter.setPen(QPen(color))

            # Draw text
            painter.drawText(rect, align, str(line_count))
            block = block.next()

        self.highest_line = line_count
        painter.end()
        super(ScriptEditorNumberBar, self).paintEvent(event)
