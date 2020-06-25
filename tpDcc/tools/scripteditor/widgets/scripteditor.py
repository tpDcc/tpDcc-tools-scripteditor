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

import os
import appdirs

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpDcc.libs.python import path as path_utils
from tpDcc.libs.qt.core import base, settings

from tpDcc.tools.scripteditor.core import session, consts
from tpDcc.tools.scripteditor.widgets import console, script


class ScriptEditorWidget(base.BaseWidget, object):
    def __init__(self, settings=None, parent=None):
        self._settings = settings
        super(ScriptEditorWidget, self).__init__(parent=parent)

        session_path = self._get_session_path()
        session.SessionManager().current_session = session.Session(session_path)

        self._namespace = __import__('__main__').__dict__
        self._dial = None

        self._update_namespace({
            'self_main': self,
            'self_output': None
        })

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ScriptEditorWidget, self).ui()

        main_splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(main_splitter)

        self._output_console = console.OutputConsole()

        # NOTE: Scripts Tab MUST pass ScriptEditor as parent because internally some ScriptEditor functions
        # NOTE: are connected to some signals. If we don't do this Maya will crash when opening new Script Editors :)
        self._scrips_tab = script.ScriptsTab(parent=self)

        main_splitter.addWidget(self._output_console)
        main_splitter.addWidget(self._scrips_tab)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_session_path(self):
        """
        Internal function that returns path where script session will be stored
        :return: str
        """

        if self._settings:
            return os.path.join(
                os.path.normpath(os.path.dirname(self._settings.fileName())), consts.DEFAULT_SESSION_NAME)
        else:
            return os.path.join(appdirs.user_data_dir(), 'tpDcc-tools-scripteditor', consts.DEFAULT_SESSION_NAME)

    def _update_namespace(self, namespace_dict):
        """
        Internal function that updates script editor namespaces
        :param namespace_dict: dict
        """

        self._namespace.update(namespace_dict)