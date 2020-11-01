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
import re
import jedi
import logging
import traceback

from Qt.QtCore import Qt, Signal, QPoint, QRect
from Qt.QtWidgets import QApplication, QWidget, QMessageBox, QMenu, QTextEdit, QShortcut, QAction
from Qt.QtGui import QCursor, QTextCursor, QTextOption, QFont, QFontMetrics, QKeySequence, QColor, QPalette
from Qt.QtGui import QPen, QBrush, QPainter

from tpDcc import dcc
from tpDcc.dcc import completer
from tpDcc.libs.python import path as path_utils
from tpDcc.libs.qt.core import base, qtutils
from tpDcc.libs.qt.widgets import layouts, tabs

from tpDcc.tools.scripteditor.core import consts
from tpDcc.tools.scripteditor.widgets import completer
from tpDcc.tools.scripteditor.syntax import python

logger = logging.getLogger('tpDcc-tools-scripteditor')


class ScriptsTab(tabs.BaseEditableTabWidget, object):

    lastTabClosed = Signal()

    def __init__(self, script=None, add_empty_tab=False, settings=None, parent=None):
        super(ScriptsTab, self).__init__(parent=parent)

        self._last_search = [0, None]
        self._settings = settings
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

    def removeTab(self, index, force=False):
        """
        Overrides removeTab function to ask permission to the user before closing the tab
        :param index: int, index of the tab we want to close
        """

        total_tabs = self.count()

        if force:
            super(ScriptsTab, self).removeTab(index)
        else:
            if total_tabs > 1:
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

        if total_tabs == 1:
            self.lastTabClosed.emit()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def add_new_tab(self, script_name=consts.DEFAULT_SCRIPTS_TAB_NAME, script_file='', skip_if_exists=True):
        """
        Adds a new empty tab into the scripts tab
        :param script_name: str
        :param script_name: str
        :return: ScriptCodeEditor
        """

        if script_file and skip_if_exists:
            for i in range(self.count()):
                widget = self.widget(i)
                if path_utils.clean_path(script_file) == path_utils.clean_path(widget.file_path):
                    self.setCurrentIndex(i)
                    return widget.editor

        script_widget = ScriptWidget(
            file_path=script_file, settings=self._settings, parent=self._parent, desktop=self._desktop)
        script_widget.editor.scriptSaved.connect(self._on_save_session)
        self.addTab(script_widget, script_name)
        script_widget.editor.moveCursor(QTextCursor.Start)
        self.setCurrentIndex(self.count() - 1)

        return script_widget.editor

    def close_all_tabs(self):
        """
        Closes all current tabs
        """

        for i in reversed(range(self.count())):
            self.removeTab(i, force=True)

    def current(self):
        """
        Returns the current script editor
        :return: ScriptCodeEditor
        """

        return self.widget(self.currentIndex()).editor

    def get_current_tab_name(self):
        """
        Returns the name of the current selected tab
        :return: str
        """

        index = self.currentIndex()
        text = self.tabText(index)

        return text

    def set_current_tab_name(self, new_text):
        """
        Sets the name of the current selected tab name
        :return:
        """
        index = self.currentIndex()
        text = self.tabText(index)
        if text == new_text:
            return
        self.setTabText(index, new_text)

    def get_tab_text(self, tab_widget):
        """
        Returns the text in the given tab
        :param tab_widget: int, tab index to get text from. If None, current selected tab text is retrieved
        :return: str
        """

        text = self.widget(tab_widget).editor.toPlainText()

        return text

    def get_current_text(self, tab_index=None):
        """
        Returns the text in the current tab
        :param tab_index: int, tab index to get text from. If None, current selected tab text is retrieved
        :return: str
        """

        if tab_index is None:
            tab_index = self.currentIndex()
        tab_widget = self.widget(tab_index)
        text = tab_widget.editor.toPlainText() if tab_widget else ''

        return text

    def get_current_file(self, tab_index=None):
        """
        Returns the file path (if possible) of the current path
        :param tab_index: int
        :return: str
        """

        if tab_index is None:
            tab_index = self.currentIndex()
        file_path = self.widget(tab_index).file_path

        return file_path

    def get_current_selected_text(self, tab_index=None):
        """
        Returns the selected text in the given tab
        :param tab_index: int, tab index to get text from. If None, current selected tab text is retrieved
        :return: str
        """

        if tab_index is None:
            tab_index = self.currentIndex()
        text = self.widget(tab_index).editor.get_selection()

        return text

    def add_text_to_current(self, text):
        """
        Adds given text to current selected tab script editor
        :param text: str, text to add
        """

        i = self.currentIndex()
        self.widget(i).editor.insertPlainText(text)

    def set_current_text(self, text):
        """
        Set the text of the current tab script editor
        :param text: str, text to set
        """

        i = self.currentIndex()
        self.widget(i).editor.setPlainText(text)

    def undo(self):
        """
        Undo command
        """

        self.current().undo()

    def redo(self):
        """
        Redo command
        """

        self.current().redo()

    def copy(self):
        """
        Copy command
        """

        self.current().copy()

    def cut(self):
        """
        Cut command
        """

        self.current().cut()

    def paste(self):
        """
        Paste command
        """

        self.current().paste()

    def search(self, text=None):
        """
        Search given text in current text editor
        :param text: str
        """

        if text:
            if text == self._last_search[0]:
                self._last_search[1] += 1
            else:
                self._last_search = [text, 0]
            self._last_search[1] = self.current().select_word(text, self._last_search[1])

    def replace(self, parts):
        """
        Replaces text
        :param parts: list
        """

        find, rep = parts
        self._last_search = [find, 0]
        self._last_search[1] = self.current().select_word(find, self._last_search[1], rep)
        self.current().selectWord(find, self._last_search[1])

    def replace_all(self, pat):
        """
        Replaces all texts
        :param pat: list
        """

        find, rep = pat
        text = self.current().toPlainText()
        text = text.replace(find, rep)
        self.current().setPlainText(text)

    def comment(self):
        """
        Comment selected text
        """

        self.current().comment_selected()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _on_hide_all_completers(self):
        """
        Internal function that is called anytime the user selects a tab
        Disable all completers
        """

        for i in range(self.count()):
            self.widget(i).editor.completer.hide_me()

    def _on_open_menu(self):
        """
        Internal function that is called when the user opens the context menu of the tab menu bar
        :param pos: QPos
        """

        menu = QMenu(self)
        menu.addAction(QAction('Rename Current Tab', self, triggered=self._on_rename_tab))
        menu.exec_(QCursor.pos())

    def _on_rename_tab(self):
        """
        Internal function used to rename the current selected tab
        """

        index = self.currentIndex()
        text = self.tabText(index)
        result = qtutils.get_string_input(message='Enter New Script Name', title='New Script Name', old_name=text)
        if result and result != text:
            self.setTabText(index, result)

    def _on_add_new_tab(self):
        """
        Internal callback function that is called when add button in tab bar is clicked by the user
        """

        self.add_new_tab()
    
    def _on_save_session(self):
        """
        Internal callback function that is called when session is saved ...
        """

        self._parent.save_current_session()


class ScriptWidget(base.BaseWidget, object):
    def __init__(self, file_path, settings=None, desktop=None, parent=None):

        self._file_path = file_path
        self._settings = settings
        self._desktop = desktop
        self._parent = parent
        self._editor = None

        super(ScriptWidget, self).__init__(parent=parent)

        self.refresh()

    @property
    def file_path(self):
        return self._file_path

    @property
    def editor(self):
        return self._editor

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(ScriptWidget, self).ui()

        self._editor = ScriptEditor(desktop=self._desktop, parent=self._parent, settings=self._settings)
        self._line_num = ScriptEditorNumberBar(editor=self._editor, parent=self)

        self.main_layout.addWidget(self._line_num)
        self.main_layout.addWidget(self._editor)

    def setup_signals(self):
        if self._parent and hasattr(self._parent, 'execute_selected'):
            self._editor.scriptExecuted.connect(self._parent.execute_selected)
        self._editor.scriptInput.connect(self._line_num.update)

    def refresh(self):
        if self._file_path and os.path.isfile(self._file_path):
            with open(self._file_path) as file_handler:
                text = file_handler.read()
                self._editor.add_text(text)


class ScriptEditor(QTextEdit, object):

    scriptExecuted = Signal()
    scriptSaved = Signal()
    scriptInput = Signal()

    def __init__(self, desktop=None, settings=None, parent=None):
        super(ScriptEditor, self).__init__(parent)

        self._font_size = 12
        self._completer = completer.ScriptCompleter(parent=parent, editor=self)
        self._desktop = desktop
        self._parent = parent
        self._settings = settings
        self._syntax_highlighter = None
        self._use_jedi = True

        font = QFont(consts.FONT_NAME)
        font.setStyleHint(consts.FONT_STYLE)
        font.setFixedPitch(True)
        self.setFont(font)
        self.document().setDefaultFont(QFont(consts.FONT_NAME, consts.MIN_FONT_SIZE, consts.FONT_STYLE))
        metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopWidth(consts.TAB_STOP * metrics.width(' '))
        self.setAcceptDrops(True)
        self.setWordWrapMode(QTextOption.NoWrap)

        shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut.activated.connect(self.scriptSaved.emit)

        if settings:
            self.apply_highlighter(settings.get('theme'))

        self.change_font_size(True)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    @property
    def completer(self):
        return self._completer

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def focusOutEvent(self, event):
        self.scriptSaved.emit()
        super(ScriptEditor, self).focusOutEvent(event)

    def hideEvent(self, event):
        self._completer.update_complete_list()
        try:
            super(ScriptEditor, self).hideEvent(event)
        except Exception:
            pass

    def mousePressEvent(self, event):
        self._completer.update_complete_list()
        super(ScriptEditor, self).mousePressEvent(event)

    def keyPressEvent(self, event):
        """
        Overrides keyPressEvent
        :param event: QKeyEvent
        """

        self.scriptInput.emit()
        parse = 0

        if event.modifiers() == Qt.NoModifier and event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            if self._completer and self._completer.isVisible():
                self._completer.apply_current_complete()
                return
            else:
                # Auto indent
                add = self.get_current_indent()
                if add:
                    super(ScriptEditor, self).keyPressEvent(event)
                    cursor = self.textCursor()
                    cursor.insertText(add)
                    self.setTextCursor(cursor)
                    return
        elif  event.modifiers() == Qt.NoModifier and event.key() == Qt.Key_Backspace:
            # Remove 4 spaces
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.KeepAnchor)
            line = cursor.selectedText()
            if line:
                p = r"    $"
                m = re.search(p, line)
                if m:
                    cursor.removeSelectedText()
                    line = line[:-3]
                    cursor.insertText(line)
                    self.setTextCursor(cursor)
            parse = 1
        elif event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_Q:
            # Comment
            self._parent._scripts_tab.comment()
            return
        elif event.modifiers() == Qt.ControlModifier and event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            # Execute selected code
            if self._completer:
                self._completer.update_complete_list()
            self.scriptExecuted.emit()
            return
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
            # Duplicate selected code
            self.duplicate()
            self.update()
        elif event.modifiers() == Qt.ShiftModifier and event.key() == [Qt.Key_Return, Qt.Key_Enter]:
            # Ignore Shift + Enter
            return
        elif event.key() == Qt.Key_Tab:
            # increase indent
            if self._completer:
                if self._completer.isVisible():
                    self._completer.applyCurrentComplete()
                    return
            if self.textCursor().selection().toPlainText():
                self.selectBlocks()
                self.moveSelected(True)
                return
            else:
                self.insertPlainText(' ' * consts.INDENT_LENGTH)
                return
        elif event.key() == Qt.Key_Backtab:
            # Decrease indent
            self.select_blocks()
            self.move_selected(False)
            if self._completer:
                self._completer.update_complete_list()
            return
        elif event.key() in consts.ESCAPE_BUTTONS:
            # close completer
            if self._completer:
                self._completer.update_complete_list()
            self.setFocus()
        elif event.key() == Qt.Key_Down or event.key() == Qt.Key_Up:
            # go to completer
            if self._completer.isVisible():
                self._completer.activateCompleter(event.key())
                self._completer.setFocus()
                return
        elif not event.modifiers() == Qt.NoModifier and not event.modifiers() == Qt.ShiftModifier:
            # just close completer
            self._completer.update_complete_list()
        else:
            parse = 1

        super(ScriptEditor, self).keyPressEvent(event)
        if parse and event.text():
            self.parse_text()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()
        super(ScriptEditor, self).dragEnterEvent(event)

    def dropEvent(self, event):
        event.acceptProposedAction()
        if event.mimeData().hasText():
            mime_data = event.mimeData()
            text = mime_data.text()
            namespace = self._parent.namespace
            text = completer.Completer.wrap_dropped_text(namespace, text, event)
            mime_data.setText(text)
            super(ScriptEditor, self).dropEvent(event)
        else:
            super(ScriptEditor, self).dropEvent(event)

    def dragMoveEvent(self, event):
        event.acceptProposedAction()
        super(ScriptEditor, self).dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        event.acceptProposedAction()
        super(ScriptEditor, self).dragLeaveEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if self.completer:
                self.completer.update_complete_list()
            if event.delta() > 0:
                self.change_font_size(True)
        else:
            super(ScriptEditor, self).wheelEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_settings(self, settings):
        if not settings:
            return

        self.apply_highlighter(settings.get('theme'))

    def get_selection(self):
        """
        Returns selected text
        :return: str
        """

        cursor = self.textCursor()
        selected_text = cursor.selection().toPlainText()

        return selected_text

    def add_text(self, text):
        """
        Adds new text to the script editor
        :param text: str
        """

        if self._completer:
            self._completer.update_complete_list()

        self.blockSignals(True)
        try:
            self.append(text)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.blockSignals(False)

    def insert_text(self, comp):
        """
        Inserts given text and the end of the script editor
        :param comp: str
        """

        cursor = self.textCursor()
        self.document().documentLayout().blockSignals(True)
        try:
            cursor.insertText(comp.complete)
            cursor = self._fix_line(cursor, comp)
            self.document().documentLayout().blockSignals(False)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.document().documentLayout().blockSignals(False)
        self.setTextCursor(cursor)
        self.update()

    def change_font_size(self, up):
        """
        Changes the current font size by the given delta value
        :param up: float
        """

        if dcc.is_houdini():
            if up:
                self._font_size = min(30, self._font_size + 1)
            else:
                self._font_size = max(8, self._font_size - 1)
        else:
            f = self.font()
            size = f.pointSize()
            if up:
                size = min(30, size + 1)
            else:
                size = max(8, size - 1)
            f.setPointSize(size)
            f.setFamily(consts.FONT_NAME)
            self.setFont(f)

    def get_font_size(self):
        """
        Returns size of the current editor font
        :return: int
        """

        return self.font().pointSize()

    def set_font_size(self, font_size):
        """
        Sets the size of the current font used
        :param font_size: int
        """

        if font_size > consts.MIN_FONT_SIZE:
            if dcc.is_houdini():
                self._font_size = font_size
                self._set_text_editor_font_size(self.font_size)
            else:
                f = self.font()
                f.setPointSize(font_size)
                self.setFont(f)

    def get_current_indent(self):
        """
        Returns current indent text
        :return: str
        """

        cursor = self.textCursor()
        auto = self._char_before_cursor(cursor) == ':'
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()

        result = ''
        if line.strip():
            p = r"(^\s*)"
            m = re.search(p, line)
            if m:
                result = m.group(0)
            if auto:
                result += '    '

        return result

    def select_blocks(self):
        """
        Select script blocks
        :return:
        """

        self.document().documentLayout().blockSignals(True)
        try:
            cursor = self.textCursor()
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.document().documentLayout().blockSignals(False)

    def move_completer(self):
        """
        Moves completer to a proper position
        """

        rect = self.cursorRect()
        pt = self.mapToGlobal(rect.bottomRight())
        x = 0
        y = 0
        if self._completer.isVisible() and self._desktop:
            current_screen = self._desktop.screenGeometry(self.mapToGlobal(rect.bottomRight()))
            future_comp_geo = self.completer.geometry()
            future_comp_geo.moveTo(pt)
            if not current_screen.contains(future_comp_geo):
                try:
                    i = current_screen.intersect(future_comp_geo)
                except Exception:
                    i = current_screen.intersected(future_comp_geo)
                x = future_comp_geo.width() - i.width()
                y = future_comp_geo.height() + self.completer.line_height \
                    if (future_comp_geo.height()-i.height()) > 0 else 0

        pt = self.mapToGlobal(rect.bottomRight()) + QPoint(10-x, -y)
        self._completer.move(pt)

    def move_selected(self, inc):
        """
        Moves selected script editor text
        :param inc: int
        """

        cursor = self.textCursor()
        if cursor.hasSelection():
            self.document().documentLayout().blockSignals(True)
            try:
                self.select_blocks()
                start, end = cursor.selectionStart(), cursor.selectionEnd()
                text = cursor.selection().toPlainText()
                cursor.removeSelectedText()
                if inc:
                    new_text = self.addTabs(text)
                else:
                    new_text = self.removeTabs(text)
                cursor.beginEditBlock()
                cursor.insertText(new_text)
                cursor.endEditBlock()
                new_end = cursor.position()
                cursor.setPosition(start)
                cursor.setPosition(new_end, QTextCursor.KeepAnchor)
                self.document().documentLayout().blockSignals(False)
            except Exception:
                logger.error('{}'.format(traceback.format_exc()))
                self.document().documentLayout().blockSignals(False)

            self.setTextCursor(cursor)
            self.update()

    def comment_selected(self):
        """
        Comments script editor text
        """

        cursor = self.textCursor()
        self.document().documentLayout().blockSignals(True)
        try:
            self.select_blocks()
            pos = cursor.position()
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)
            text = cursor.selection().toPlainText()
            self.document().documentLayout().blockSignals(False)
            text, offset = self._add_remove_comments(text)
            cursor.insertText(text)
            cursor.setPosition(min(pos + offset, len(self.toPlainText())))
            self.setTextCursor(cursor)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.document().documentLayout().blockSignals(False)

        self.update()

    def apply_highlighter(self, theme=None):
        """
        Applies highlighter with the settings of the given theme
        :param theme: str
        """

        self.blockSignals(True)
        try:
            colors = None
            if theme or not theme == 'default':
                colors = python.get_colors(theme=theme, settings=self._settings)
                if self._completer:
                    self._completer.update_style(colors)

            self._syntax_highlighter = python.PythonHiglighter(document=self, colors=colors)
            editor_style = python.editor_style(theme)
            self.setStyleSheet(editor_style)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))
        finally:
            self.blockSignals(False)

    def select_word(self, pattern, number, replace=None):
        """
        Selects script editor specific word
        :param pattern: str
        :param number: int
        :param replace: str or None
        :return:
        """

        text = self.toPlainText()
        if pattern not in text:
            return number

        cursor = self.textCursor()
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(self._fix_regex_symbols(pattern), text)]
        if number > len(indexes) - 1:
            number = 0
        cursor.setPosition(indexes[number][0])
        cursor.setPosition(indexes[number][1], QTextCursor.KeepAnchor)

        if replace:
            cursor.removeSelectedText()
            cursor.insertText(replace)
        self.setTextCursor(cursor)
        self.setFocus()

        return number

    def duplicate(self):
        """
        Duplicates selected code
        """

        self.document().documentLayout().blockSignals(True)
        try:
            cursor = self.textCursor()
            if cursor.hasSelection():
                # duplicate selected
                sel = cursor.selectedText()
                end = cursor.selectionEnd()
                cursor.setPosition(end)
                cursor.insertText(sel)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
            else:
                # duplicate line
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)
                line = cursor.selectedText()
                cursor.clearSelection()
                cursor.insertText('\n' + line)
                self.setTextCursor(cursor)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.document().documentLayout().blockSignals(False)

    def parse_text(self):
        """
        Parses all the texts in the script editor
        """

        use_jedi = True

        if self._completer:
            text = self.toPlainText()
            self.move_completer()
            if text:
                context_completer = False
                text_cursor = self.textCursor()
                pos = text_cursor.position()
                line = text[:pos].split('\n')[-1]
                if not hasattr(self._parent, 'namespace'):
                    namespace = dict()
                else:
                    namespace = self._parent.namespace
                comp, extra = completer.completer(line, namespace)
                if comp or extra:
                    context_completer = True
                    self._completer.update_complete_list(comp, extra)
                if not context_completer:
                    if re.match('[a-zA-Z0-9_.]', text[pos - 1]):
                        offset = 0
                        auto_import = completer.Completer.get_auto_import()
                        if auto_import:
                            text = auto_import + text
                            offset = len(auto_import.split('\n')) - 1
                        block_number = text_cursor.blockNumber() + 1 + offset
                        column_number = text_cursor.columnNumber()

                        if self._use_jedi:
                            try:
                                script = jedi.Script(text, block_number, column_number, '')
                                if self._use_jedi:
                                    try:
                                        self._completer.update_complete_list(script.complete())
                                    except Exception:
                                        self._completer.update_complete_list()
                            except Exception as exc:
                                self._use_jedi = False
                        else:
                            self._completer.update_complete_list()
                else:
                    self._completer.update_complete_list()
            else:
                self._completer.update_complete_list()

    def add_tabs(self, text):
        """
        Add new tabs to given text
        :param text: str
        :return: str
        """
        lines = [(' ' * consts.INDENT_LENGTH) + x for x in text.split('\n')]
        return '\n'.join(lines)

    def remove_tabs(self, text):
        """
        Removes tabs from given text
        :param text: str
        :return: str
        """

        lines = text.split('\n')
        new = []
        pat = re.compile("^ .*")
        for line in lines:
            line = line.replace('\t', ' ' * consts.INDENT_LENGTH)
            for _ in range(4):
                if pat.match(line):
                    line = line[1:]
            new.append(line)

        return '\n'.join(new)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _char_before_cursor(self, cursor):
        """
        Returns the character located just before the given cursor
        :param cursor:
        :return: str
        """

        pos = cursor.position()
        if pos:
            text = self.toPlainText()
            return text[pos - 1]

    def _set_text_editor_font_size(self, font_size):
        """
        Set the size of the editor
        :param font_size:
        :return:
        """

        editor_style = self.styleSheet() + '''
           QTextEdit
           {
               font-size: %spx;
               font-family: %s;
           }
           ''' % (font_size, consts.FONT_NAME)
        self.setStyleSheet(editor_style)

    def _apply_preview_style(self, colors):
        self.blockSignals(True)
        self.blockSignals(True)

        try:
            self._syntax_highlighter = python.PythonHiglighter(document=self, colors=colors)
            current_style = python.apply_color_to_editor_style(colors=colors)
            self.setStyleSheet(current_style)
            self._completer.setStyleSheet(current_style)
        except Exception:
            logger.error('{}'.format(traceback.format_exc()))

        self.blockSignals(False)

    def _add_remove_comments(self, text):
        result = text
        ofs = 0
        if text.strip():
            lines = text.split('\n')
            ind = 0
            while not lines[ind].strip():
                ind += 1
            if lines[ind].strip()[0] == '#':
                # Remove Comment
                result = '\n'.join([x.replace('#', '', 1) for x in lines])
                ofs = -1
            else:
                # Add Comment
                result = '\n'.join(['#' + x for x in lines])
                ofs = 1

        return result, ofs

    def _fix_line(self, cursor, comp):
        pos = cursor.position()
        line_pos = cursor.positionInBlock()

        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        cursor.removeSelectedText()

        start = line[:line_pos]
        end = line[line_pos:]
        before = start[:-len(comp.name)]
        br = ''
        ofs = 0
        if hasattr(comp, 'end_char'):
            if before and comp.end_char:
                brackets = {'"': '"', "'": "'"}  # , '(':')', '[':']'}
                if before[-1] in brackets:
                    ofs = 1
                    br = brackets[before[-1]]
                    if end and end[0] == brackets[before[-1]]:
                        br = ''

        res = before + comp.name + br + end

        cursor.beginEditBlock()
        cursor.insertText(res)
        cursor.endEditBlock()
        cursor.clearSelection()
        cursor.setPosition(pos + ofs, QTextCursor.MoveAnchor)

        return cursor

    def _insert_from_mime_data(self, source):
        text = source.text()
        self.insertPlainText(text)

    def _fix_regex_symbols(self, pattern):
        for s in ['[', ']', '(', ')', '*', '^', '.', ',', '{', '}', '$']:
            pattern = pattern.replace(s, '\\' + s)

        return pattern


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
