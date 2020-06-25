#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains core implementation for Script Editor Tool
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

from tpDcc.core import tool
from tpDcc.libs.qt.widgets import toolset

# Defines ID of the tool
TOOL_ID = 'tpDcc-tools-scripteditor'


class ScriptEditorTool(tool.DccTool, object):
    def __init__(self, *args, **kwargs):
        super(ScriptEditorTool, self).__init__(*args, **kwargs)

    @classmethod
    def config_dict(cls, file_name=None):
        base_tool_config = tool.DccTool.config_dict(file_name=file_name)
        tool_config = {
            'name': 'Script Editor',
            'id': 'tpDcc-tools-scripteditor',
            'icon': 'scripteditor',
            'tooltip': 'Renamer Tool to easily rename DCC objects in a visual way',
            'tags': ['tpDcc', 'dcc', 'tool', 'script', 'editor'],
            'is_checkable': False,
            'is_checked': False,
            'menu_ui': {'label': 'Script Editor', 'load_on_startup': False, 'color': '', 'background_color': ''},
            'menu': [{'type': 'menu', 'children': [{'id': 'tpDcc-tools-scripteditor', 'type': 'tool'}]}],
            'shelf': [
                {'name': 'tpDcc', 'children': [{'id': 'tpDcc-tools-scripteditor', 'display_label': False, 'type': 'tool'}]}
            ]
        }
        base_tool_config.update(tool_config)

        return base_tool_config

    def launch(self, *args, **kwargs):
        return self.launch_frameless(*args, **kwargs)


class ScriptEditorWidget(toolset.ToolsetWidget, object):
    ID = TOOL_ID

    def __init__(self, *args, **kwargs):
        super(ScriptEditorWidget, self).__init__(*args, **kwargs)

    def contents(self):

        from tpDcc.tools.scripteditor.widgets import scripteditor

        return [scripteditor.ScriptEditorWidget()]
