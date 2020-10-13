#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains syntax definition for Python language
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import re

from Qt.QtCore import *
from Qt.QtGui import *

EditorStyle = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'styles', 'completer.css')
if not os.path.exists(EditorStyle):
    EditorStyle = None

DefaultColors = dict(
    background=(40, 40, 40),
    keywords=(65, 255, 130),
    digits=(250, 255, 62),
    definition=(255, 160, 250),
    operator=(230, 220, 110),
    extra=(110, 180, 230),
    methods=(120, 190, 205),
    comment=(110, 100, 100),
    string=(245, 165, 18),
    docstring=(130, 160, 75),
    boolean=(160, 220, 120),
    brace=(235, 235, 195),
    completer_text=(200, 200, 200),
    completer_selected_text=(105, 105, 105),
    completer_hover_text=(255, 255, 255),
    completer_background=(59, 59, 59),
    completer_alt_background=(65, 65, 65),
    completer_hover_background=(85, 85, 85),
    completer_selected_background=(123, 123, 123),
    default=(210, 210, 210)
)

Syntax = {"extension": [
    "py", "pyw"],

    "comment": ["#"],

    "string": ["\"", "'"],

    "operators": ["=",
                  # Comparison
                  "!=", "<", ">",
                  # Arithmetic
                  "+", "\-", "*", "/", "%", "*",
                  # Bitwise
                  "^", "|", "&"],
    "keywords": ["and",
                 "assert",
                 "break",
                 "continue",
                 "del",
                 "elif",
                 "else",
                 "except",
                 "exec",
                 "finally",
                 "for",
                 "from",
                 "global",
                 "if",
                 "import",
                 "in",
                 "is",
                 "not",
                 "or",
                 "pass",
                 "print",
                 "raise",
                 "return",
                 "try",
                 "while",
                 "yield",
                 "None",
                 "with"
                 ],
    "definition": ["class",
                   "def",
                   "lambda"],
    "boolean": ["True",
                "False"],
    "extras": [
        "abs",
        "all",
        "any",
        "basestring",
        "bin",
        "bool",
        "bytearray",
        "callable",
        "chr",
        "classmethod",
        "cmp",
        "compile",
        "complex",
        "delattr",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "execfile",
        "file",
        "filter",
        "float",
        "format",
        "frozenset",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "locals",
        "long",
        "map",
        "max",
        "memoryview",
        "min",
        "next",
        "object",
        "oct",
        "open",
        "ord",
        "pow",
        "property",
        "range",
        "raw_input",
        "reduce",
        "reload",
        "repr",
        "reversed",
        "round",
        "set",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "str",
        "sum",
        "tuple",
        "type",
        "unichr",
        "unicode",
        "vars",
        "xrange",
        "zip",
        "apply",
        "buffer",
        "coerce",
        "intern"
    ],
    "braces": ['\{', '\}', '\(', '\)', '\[', '\]']
}


def get_colors(theme=False, settings=None):
    if not theme:
        theme = settings.get('theme') if settings else 'default'

    result = {k: v for k, v in DefaultColors.items()}
    if theme:
        current_colors = settings.get('colors') if settings else dict()
        if current_colors:
            colors = current_colors.get(theme)
            for k, v in colors.items():
                result[k] = v

    return result


def editor_style(theme=None):
    colors = get_colors(theme)
    colors = {k: tuple(v) if isinstance(v, list) else v for k, v in colors.items()}
    if EditorStyle:
        text = open(EditorStyle).read()
        proxys = re.findall('\[.*\]', text)
        for p in proxys:
            name = p[1:-1]
            if name in colors:
                text = text.replace(p, str(colors[name]))

        return text

    return None


def apply_color_to_editor_style(colors=None):
    if EditorStyle:
        text = open(EditorStyle).read()
        proxys = re.findall('\[.*\]', text)
        for p in proxys:
            name = p[1:-1]
            if name in colors:
                c = colors[name]
                if isinstance(c, list):
                    c = tuple(c)
                text = text.replace(p, str(c))
        return text
    return ''


class PythonHiglighter(QSyntaxHighlighter):
    def __init__(self, document, colors=None):
        super(PythonHiglighter, self).__init__(document)

        if colors:
            self._colors = colors
        else:
            self._colors = get_colors()

        self._tri_single = (QRegExp("'''"), 1, self.get_style(self._colors['docstring']))
        self._tri_double = (QRegExp('"""'), 2, self.get_style(self._colors['docstring']))

        rules = list()

        # rules += [(r".*", 0, self.get_style(self._colors['default'], False))] # Defaults
        rules += [('\\b%s\\b' % w, 0, self.get_style(self._colors['keywords'], True)) for w in
                  Syntax['keywords']]  # Keywords
        rules += [("\\b[A-Za-z0-9_]+(?=\\()", 0, self.get_style(self._colors['methods'], False))]  # Methods
        rules += [(r'[~!@$%^&*()-+=]', 0, self.get_style(
            self._colors['operator']))]  # for o in pythonSyntax.syntax['operators']]      # Operators
        rules += [(r'%s' % b, 0, self.get_style(self._colors['brace'])) for b in Syntax['braces']]  # Braces
        rules += [("\\b%s\\b" % b, 0, self.get_style(self._colors['definition'], True)) for b in
                  Syntax['definition']]  # Definition
        rules += [("\\b%s\\b" % b, 0, self.get_style(self._colors['extra'])) for b in
                  Syntax['extras']]  # Extra
        # rules += [(r'#([.*]+|[^#]*)', 0, self.get_style(design.comment))] # Comment
        rules += [(r"\b[\d]+\b", 0, self.get_style(self._colors['digits']))]  # Digits
        # ("(?:^|[^A-Za-z])([\d|\.]*\d+)", 0, self.get_style(design.digits)),
        rules += [(r'[ru]?"[^"\\]*(\\.[^"\\]*)*"', 0, self.get_style(self._colors['string']))]  # Double-quoted string
        rules += [(r"[ru]?'[^'\\]*(\\.[^'\\]*)*'", 0, self.get_style(self._colors['string']))]  # Single-quoted string

        self.rules = [(QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """
        Applies syntax higlighting to the given block of text
        :param text: str
        """

        def_format = self.get_style(self._colors['default'])
        self.setFormat(0, len(text), def_format)

        for expr, nth, fmt in self.rules:
            index = expr.indexIn(text, 0)
            while index > 0:
                index = expr.pos(nth)
                length = len(expr.cap(nth))
                self.setFormat(index, length, fmt)
                index = expr.indexIn(text, index + length)

        strings = re.findall(r'(".*?")|(\'.*?\')', text)
        if '#' in text:
            copy_text = text
            if strings:
                pat = list()
                for s in strings:
                    for match in s:
                        if match:
                            pat.append(match)
                for s in pat:
                    copy_text = copy_text.replace(s, '_' * len(s))
            if '#' in copy_text:
                index = copy_text.index('#')
                length = len(copy_text) - index
                self.setFormat(index, length, self.get_style(self._colors['comment']))

        self.setCurrentBlockState(0)

        in_multiline = self.match_multiline(text, *self._tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self._tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """
        Do highlighting of multi-line strings
        :param text: str
        :param delimiter: QRegExp, delimiter for triple-sinqle or triple-double quotes
        :param in_state: int, unique integer to represent the corresponding state changes when inside delimiter strings
        :param style: str
        :return: bool, True if we're still in a multi-line string or False otherwise
        """

        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
            # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:

            # Look for the ending delimiter and check if the delimiter ends in this line or not
            end = delimiter.indexIn(text, start + add)
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add

            # Apply formatting and look for next match
            self.setFormat(start, length, style)
            start = delimiter.indexIn(text, start + length)

        if self.currentBlockState() == in_state:
            return True
        else:
            return False

    def get_style(self, color, bold=False):
        brush = QBrush(QColor(*color))
        f = QTextCharFormat()
        if bold:
            f.setFontWeight(QFont.Bold)
        f.setForeground(brush)

        return f
