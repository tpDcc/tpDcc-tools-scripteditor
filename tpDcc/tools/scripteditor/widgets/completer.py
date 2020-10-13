#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains completer widget for script editor
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import re

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.python import osplatform

from tpDcc.tools.scripteditor.syntax import python

NODE_TYPES_CACHE = list()


class ContextCompleter(object):
    def __init__(self, name, complete, end=None):
        self.name = name
        self.complete = complete
        self.end = end


class ScriptCompleter(QListWidget, object):
    def __init__(self, parent=None, editor=None):
        super(ScriptCompleter, self).__init__(parent)

        if tp.is_maya():
            import pymel.core as pm
            global NODE_TYPES_CACHE
            NODE_TYPES_CACHE = pm.allNodeTypes()

        self.setAlternatingRowColors(True)
        self.line_height = 18
        self.editor = editor
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        if osplatform.is_windows():
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window | Qt.WindowStaysOnTopHint)

        self.itemDoubleClicked.connect(self._on_insert_selected)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_R or event.key() == Qt.Key_Enter:
            self.editor.setFocus()
            self.apply_current_complete()
            return event
        elif event.key() == Qt.Key_Up:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i == 0:
                    super(ScriptCompleter, self).keyPressEvent(event)
                    self.setCurrentRow(self.count()-1)
                    return
        elif event.key() == Qt.Key_Down:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i+1 == self.count():
                    super(ScriptCompleter, self).keyPressEvent(event)
                    self.setCurrentRow(0)
                    return
        elif event.key() == Qt.Key_Backspace:
            self.editor.setFocus()
            self.editor.activateWindow()
        elif event.text():
            self.editor.keyPressEvent(event)
            return

        super(ScriptCompleter, self).keyPressEvent(event)

    def send_text(self, comp):
        self.editor.insert_text(comp)

    def show_me(self):
        self.show()
        self.editor.move_completer()

    def hide_me(self):
        self.hide()

    def activate_completer(self, key=False):
        self.activateWindow()
        if not key == Qt.Key_Up:
            self.setCurrentRow(min(1, self.count() - 1))
        else:
            self.setCurrentRow(self.count()-1)

    def update_style(self, colors=None):
        text = python.editor_style()
        self.setStyleSheet(text)

    def update_complete_list(self, lines=None, extra=None):
        self.clear()
        if lines or extra:
            self.show_me()
            if lines:
                for i in [x for x in lines if not x.name == 'mro']:
                    item = QListWidgetItem(i.name)
                    item.setData(32, i)
                    self.addItem(item)
            if extra:
                font = self.font()
                font.setItalic(True)
                font.setPointSize(font.pointSize()*0.8)
                for e in extra:
                    item = QListWidgetItem(e.name)
                    item.setData(32, e)
                    item.setFont(font)
                    self.addItem(item)

            font = QFont('monospace', self.line_height, False)
            fm = QFontMetrics(font)
            width = fm.width(' ') * max([len(x.name) for x in lines or extra]) + 40

            self.resize(max(250, width), 250)
            self.setCurrentRow(0)
        else:
            self.hide_me()

    def apply_current_complete(self):
        i = self.selectedItems()
        if i:
            comp = i[0].data(32)
            self.send_text(comp)
        self.hide_me()

    def _on_insert_selected(self, item):
        if item:
            comp = item.data(32)
            self.send_text(comp)
            self.hide_me()


def completer(line, ns):

    # create node
    p = r"createNode\(['\"](\w*)$"
    m = re.search(p, line)
    if m:
        name = m.group(1)
        if name:
            auto = [x for x in NODE_TYPES_CACHE if x.lower().startswith(name.lower())]
            l = len(name)
            return [ContextCompleter(x, x[l:], True) for x in auto], None
    # exists nodes
    p = r"PyNode\(['\"](\w*)$"
    m = re.search(p, line)
    if m:
        name = m.group(1)
        exists_nodes = sorted(tp.Dcc.selected_nodes(full_path=False))
        l = len(name)
        if name:
            auto = [x for x in exists_nodes if x.lower().startswith(name.lower())]
            return [ContextCompleter(x, x[l:], True) for x in auto], None
        else:
            return [ContextCompleter(x, x, True) for x in exists_nodes], None

    return None, None
