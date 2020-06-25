
#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core implementation for Script Editor widget
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from tpDcc.libs.qt.core import base


class ScriptEditorWidget(base.BaseWidget, object):
    def __init__(self, parent=None):
        super(ScriptEditorWidget, self).__init__(parent=parent)
