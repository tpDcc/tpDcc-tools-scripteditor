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
import sys
import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpDcc as tp
from tpDcc.libs.python import osplatform, path as path_utils
from tpDcc.libs.qt.core import base

from tpDcc.tools.scripteditor.core import session, consts
from tpDcc.tools.scripteditor.widgets import console, script

logger = tp.LogsMgr().get_logger('tpDcc-tools-scripteditor')


class ScriptEditorWidget(base.BaseWidget, object):

    lastTabClosed = Signal()
    scriptSaved = Signal(str)

    def __init__(self, load_session=True, enable_save_script=True, settings=None, parent=None):
        self._settings = settings
        super(ScriptEditorWidget, self).__init__(parent=parent)

        if load_session:
            session_path = self._get_session_path()
            session.SessionManager().current_session = session.Session(session_path)

        self._namespace = __import__('__main__').__dict__
        self._dial = None
        self._enable_save_script = enable_save_script

        self._update_namespace({
            'self_main': self,
            'self_output': self._output_console,
            'self._context': tp.Dcc.get_name()
        })

        self._load_current_session()
        self._load_settings()
        self._scripts_tab.widget(0).editor.setFocus()
        self._process_args()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    @property
    def namespace(self):
        return self._namespace

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def ui(self):
        super(ScriptEditorWidget, self).ui()

        main_splitter = QSplitter(Qt.Vertical, parent=self)

        self._output_console = console.OutputConsole(parent=self)

        # NOTE: Scripts Tab MUST pass ScriptEditor as parent because internally some ScriptEditor functions
        # NOTE: are connected to some signals. If we don't do this Maya will crash when opening new Script Editors :)
        self._scripts_tab = script.ScriptsTab(parent=self, settings=self._settings)

        main_splitter.addWidget(self._output_console)
        main_splitter.addWidget(self._scripts_tab)

        self._menu_bar = self._setup_menubar()
        self._tool_bar = self._setup_toolbar()

        self.main_layout.addWidget(self._menu_bar)
        self.main_layout.addWidget(self._tool_bar)
        self.main_layout.addWidget(main_splitter)

    def setup_signals(self):
        self._scripts_tab.lastTabClosed.connect(self.lastTabClosed.emit)

    def closeEvent(self, event):
        self.save_current_session()
        self._save_settings()
        super(ScriptEditorWidget, self).closeEvent(event)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def enable_console(self):
        """
        Enables console functionality
        """

        self._output_console.setVisible(True)

    def disable_console(self):
        """
        Disables console functionality
        """

        self._output_console.setVisible(False)

    def enable_save_script(self):
        """
        Enables save script functionality
        """

        self._enable_save_script = True

    def disable_save_script(self):
        """
        Disables save script functionality
        """

        self._enable_save_script = False

    def set_toolbar_visibility(self, flag):
        """
        Sets whether or not toolbar is visible
        :param flag: bool
        """

        self._tool_bar.setVisible(flag)

    def set_menubar_visibility(self, flag):
        """
        Sets whether or not menubar is visible
        :param flag: bool
        """

        self._menu_bar.setVisible(flag)

    def add_new_tab(self, script_name=consts.DEFAULT_SCRIPTS_TAB_NAME, script_file=''):
        """
        Adds a new tab
        :param script_name: str
        :param script_file: str
        :return:
        """

        self._scripts_tab.add_new_tab(script_name, script_file)

    def close_all_tabs(self):
        """
        Closes all current tabs
        """

        self._scripts_tab.close_all_tabs()

    def save_script(self, script_path=''):
        """
        Saves scripts opened in current tab into given file. If not given, a file dialog will allow the user to select
            the path of the file
        :param script_path: str
        """

        script_text = self._scripts_tab.get_current_text()
        script_file = self._scripts_tab.get_current_file()
        home_dir = os.getenv('HOME') or os.path.expanduser('~')

        if self._enable_save_script:
            script_path = script_path or script_file
            if not script_path or not os.path.isfile(script_path):
                script_path = QFileDialog.getSaveFileName(self, 'Save Script', home_dir, 'Python Files (*.py)')
                if not script_path:
                    return
                script_path = script_path[0]

            try:
                with open(script_path, 'w') as f:
                    f.write(script_text)
                self._scripts_tab.set_current_tab_name(os.path.basename(script_path))
                self.scriptSaved.emit(script_path)
            except Exception:
                self._output_console.show_message('Error saving file: {} | {}'.format(script_path, traceback.format_exc))
        else:
            if script_file and os.path.isfile(script_file):
                self.scriptSaved.emit(script_file)

    def load_script(self, script_path=''):
        """
        Loads a script into script editor
        :param script_path: str, Path of script to load. If not given, a file dialog will allow the user to
            select the file to open
        """

        home_dir = os.getenv('HOME')
        if not home_dir:
            home_dir = os.path.expanduser('~')

        if not script_path or not os.path.isfile(script_path):
            script_path = QFileDialog.getOpenFileName(self, 'Open Script', home_dir, 'Python Files (*.py)')
            if not script_path:
                return
            script_path = script_path[0]

        if not os.path.exists(script_path):
            logger.warning('Given script does not exists: {}'.format(script_path))
            return

        self._scripts_tab.add_new_tab(os.path.basename(script_path), script_path, skip_if_exists=True)

    def execute_all(self):
        """
        Execute all code
        """

        all_text = self._scripts_tab.get_current_text()
        if all_text:
            self._execute_command(all_text.strip())

    def execute_selected(self):
        """
        Executes selected code
        """

        text = self._scripts_tab.get_current_selected_text()
        if text:
            self._execute_command(text)

    def clear_history(self):
        """
        Clear console output
        """

        self._output_console.setText('')

    def tabs_to_spaces(self):
        """
        Converts all current opened script tabs to spaces
        """

        script_text = self._scripts_tab.get_current_text()
        script_text = script_text.replace('\t', '    ')
        self._scripts_tab.set_current_text(script_text)

    def save_current_session(self):
        """
        Function that stores current session state
        """

        current_session = session.SessionManager().current_session
        if current_session:
            opened_scripts = list()
            index = self._scripts_tab.currentIndex()
            for item in range(self._scripts_tab.count()):
                name = self._scripts_tab.tabText(item)
                text = self._scripts_tab.get_tab_text(item)
                file_path = self._scripts_tab.get_current_file(item)
                if tp.is_houdini():
                    size = self._scripts_tab.widget(item).editor.font_size
                else:
                    size = self._scripts_tab.widget(item).editor.font().pointSize()

                script = {
                    'name': name,
                    'text': text,
                    'file': file_path,
                    'active': item == index,
                    'size': size
                }
                opened_scripts.append(script)

            session_path = current_session.write(opened_scripts)
            logger.debug('>>> Script Editor Session saved: {}'.format(session_path.replace('\\', '/')))

        self.save_script()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _setup_menubar(self):
        """
        Internal function that setups menu bar for the widget
        :return:
        """

        menubar = QMenuBar(self)

        save_archive_icon = tp.ResourcesMgr().icon('save_archive')
        save_icon = tp.ResourcesMgr().icon('save')
        load_icon = tp.ResourcesMgr().icon('open_folder')
        play_icon = tp.ResourcesMgr().icon('play')
        clear_icon = tp.ResourcesMgr().icon('delete')
        resume_icon = tp.ResourcesMgr().icon('resume')
        undo_icon = tp.ResourcesMgr().icon('undo')
        redo_icon = tp.ResourcesMgr().icon('redo')
        copy_icon = tp.ResourcesMgr().icon('copy')
        cut_icon = tp.ResourcesMgr().icon('cut')
        paste_icon = tp.ResourcesMgr().icon('paste')
        note_icon = tp.ResourcesMgr().icon('note')
        rename_icon = tp.ResourcesMgr().icon('rename')
        theme_icon = tp.ResourcesMgr().icon('palette')
        edit_icon = tp.ResourcesMgr().icon('edit')
        settings_icon = tp.ResourcesMgr().icon('settings')
        manual_icon = tp.ResourcesMgr().icon('manual')
        keyboard_icon = tp.ResourcesMgr().icon('keyboard')
        help_icon = tp.ResourcesMgr().icon('help')
        about_icon = tp.ResourcesMgr().icon('about')

        file_menu = QMenu('File', self)
        menubar.addMenu(file_menu)
        save_session_action = QAction(save_archive_icon, 'Save Session', file_menu)
        load_script_action = QAction(load_icon, 'Load Script', file_menu)
        save_script_action = QAction(save_icon, 'Save Script', file_menu)
        file_menu.addAction(save_session_action)
        file_menu.addAction(load_script_action)
        file_menu.addAction(save_script_action)
        load_script_action.setShortcut('Ctrl+O')
        load_script_action.setShortcutContext(Qt.WidgetShortcut)
        save_script_action.setShortcut('Ctrl+S')
        save_script_action.setShortcutContext(Qt.WidgetShortcut)

        edit_menu = QMenu('Edit', self)
        menubar.addMenu(edit_menu)
        undo_action = QAction(undo_icon, 'Undo', edit_menu)
        redo_action = QAction(redo_icon, 'Redo', edit_menu)
        copy_action = QAction(copy_icon, 'Copy', edit_menu)
        cut_action = QAction(cut_icon, 'Cut', edit_menu)
        paste_action = QAction(paste_icon, 'Paste', edit_menu)
        tab_to_spaces_action = QAction('Tab to Spaces', edit_menu)
        comment_action = QAction(note_icon, 'Comment', edit_menu)
        find_and_replace = QAction(rename_icon, 'Find and Replace', edit_menu)
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(copy_action)
        edit_menu.addAction(cut_action)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(tab_to_spaces_action)
        edit_menu.addAction(comment_action)
        edit_menu.addAction(find_and_replace)

        run_menu = QMenu('Run', self)
        menubar.addMenu(run_menu)
        self._execute_all_action = QAction(play_icon, 'Execute All', run_menu)
        self._execute_all_action.setShortcut('Ctrl+Shift+Return')
        self._execute_all_action.setShortcutContext(Qt.ApplicationShortcut)
        self._execute_selected_action = QAction(resume_icon, 'Execute Selected', run_menu)
        self._execute_selected_action.setShortcut('Ctrl+Return')
        self._execute_selected_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self._clear_output_action = QAction(clear_icon, 'Clear Output', run_menu)

        run_menu.addAction(self._execute_all_action)
        run_menu.addAction(self._execute_selected_action)
        run_menu.addAction(self._clear_output_action)

        options_menu = QMenu('Options', self)
        menubar.addMenu(options_menu)
        self._theme_menu = QMenu('Theme', self)
        self._theme_menu.setIcon(theme_icon)
        edit_theme_action = QAction(edit_icon, 'Edit...', self._theme_menu)
        open_settings_folder_action = QAction(settings_icon, 'Open Settings Folder', options_menu)
        options_menu.addMenu(self._theme_menu)
        self._theme_menu.addAction(edit_theme_action)
        options_menu.addAction(open_settings_folder_action)

        help_menu = QMenu('Help', self)
        menubar.addMenu(help_menu)
        manual_action = QAction(manual_icon, 'Manual', help_menu)
        show_shortcuts_action = QAction(keyboard_icon, 'Show Shortcuts', help_menu)
        print_help_action = QAction(help_icon, 'Print Help', help_menu)
        about_action = QAction(about_icon, 'About', help_menu)
        help_menu.addAction(manual_action)
        help_menu.addAction(show_shortcuts_action)
        help_menu.addSeparator()
        help_menu.addAction(print_help_action)
        help_menu.addAction(about_action)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.setShortcutContext(Qt.WidgetShortcut)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.setShortcutContext(Qt.WidgetShortcut)
        copy_action.setShortcut('Ctrl+C')
        copy_action.setShortcutContext(Qt.WidgetShortcut)
        cut_action.setShortcut('Ctrl+X')
        cut_action.setShortcutContext(Qt.WidgetShortcut)
        paste_action.setShortcut('Ctrl+V')
        paste_action.setShortcutContext(Qt.WidgetShortcut)
        comment_action.setShortcut(QKeySequence(Qt.ALT + Qt.Key_Q))
        comment_action.setShortcutContext(Qt.WidgetShortcut)

        self._execute_all_action.triggered.connect(self.execute_all)
        self._execute_selected_action.triggered.connect(self.execute_selected)
        self._clear_output_action.triggered.connect(self.clear_history)
        open_settings_folder_action.triggered.connect(self._open_settings)
        # manual_action.triggered.connect(self._open_manual)
        # show_shortcuts_action.triggered.connect(self._open_shortcuts)
        # print_help_action.triggered.connect(self.editor_help)
        # about_action.triggered.connect(self._open_about)
        save_session_action.triggered.connect(self.save_current_session)
        save_script_action.triggered.connect(self.save_script)
        load_script_action.triggered.connect(self.load_script)
        undo_action.triggered.connect(self._scripts_tab.undo)
        redo_action.triggered.connect(self._scripts_tab.redo)
        copy_action.triggered.connect(self._scripts_tab.copy)
        cut_action.triggered.connect(self._scripts_tab.cut)
        paste_action.triggered.connect(self._scripts_tab.paste)
        tab_to_spaces_action.triggered.connect(self.tabs_to_spaces)
        find_and_replace.triggered.connect(self._open_find_replace)
        comment_action.triggered.connect(self._scripts_tab.comment)

        return menubar

    def _setup_toolbar(self):
        """
        Internal function that setups script editor toolbar
        """

        toolbar = QToolBar('Script Editor ToolBar')
        toolbar.setIconSize(QSize(16, 16))

        execute_btn = QToolButton()
        execute_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        execute_selected_btn = QToolButton()
        execute_selected_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        clear_output_btn = QToolButton()
        clear_output_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        toolbar.addWidget(execute_btn)
        toolbar.addWidget(execute_selected_btn)
        toolbar.addWidget(clear_output_btn)

        execute_btn.setDefaultAction(self._execute_all_action)
        execute_selected_btn.setDefaultAction(self._execute_selected_action)
        clear_output_btn.setDefaultAction(self._clear_output_action)

        return toolbar

    def _get_session_path(self):
        """
        Internal function that returns path where script session will be stored
        :return: str
        """

        if self._settings:
            return os.path.join(
                os.path.normpath(os.path.dirname(self._settings.fileName())), consts.DEFAULT_SESSION_NAME)
        else:
            return os.path.join(path_utils.get_user_data_dir(), 'tpDcc-tools-scripteditor', consts.DEFAULT_SESSION_NAME)

    def _update_namespace(self, namespace_dict):
        """
        Internal function that updates script editor namespaces
        :param namespace_dict: dict
        """

        self._namespace.update(namespace_dict)

    def _load_current_session(self):
        """
        Internal function that loads current script editor session
        """

        current_session = session.SessionManager().current_session
        if not current_session:
            self._scripts_tab.add_new_tab()
        else:
            sessions = current_session.read()
            self._scripts_tab.clear()
            active = 0
            if sessions:
                for i, s in enumerate(sessions):
                    script_file = s.get('file', None)
                    script_name = s.get('name', '')
                    script_text = s.get('text', '')
                    if script_file and os.path.isfile(script_file):
                        script_editor = self._scripts_tab.add_new_tab(script_name, script_file)
                    else:
                        script_editor = self._scripts_tab.add_new_tab(script_name, script_text)
                    if s.get('active', False):
                        active = i
                    script_editor.set_font_size(s.get('size', None))
            else:
                self._scripts_tab.add_new_tab()
            self._scripts_tab.setCurrentIndex(active)

    def _open_settings(self):
        """
        Internal function that opens folder where script editor settings files are located
        :return:
        """

        settings_path = self._settings.fileName()
        settings_folder_path = (path_utils.clean_path(path_utils.get_dirname(settings_path)))
        self._output_console.show_message('>>> Settings folder: {}'.format(settings_folder_path))
        if path_utils.exists(settings_path):
            osplatform.open_folder(settings_folder_path)
        else:
            self._output_console.show_message('>>> Settings file not created!')

    def _load_settings(self):
        """
        Internal function that laods script editor settings
        :return:
        """

        console_font_size = self._settings.get('console_font_size')
        if not console_font_size:
            console_font_size = 8
            self._settings.set('console_font_size', console_font_size)

        f = self._output_console.font()
        f.setPointSize(int(console_font_size))
        self._output_console.setFont(f)

    def _save_settings(self):
        """
        Internal function that stores current settings
        """

        font_size = max(8, self._output_console.font().pointSize())
        self._settings.set('console_font_size', font_size)

    def _process_args(self):
        """
        Internal function that adds processes given args
        If file path is given in sys.argv, we tyr to open it ...
        :return:
        """

        if sys.argv:
            f = sys.argv[-1]
            if os.path.exists(f):
                if not os.path.basename(f) == os.path.basename(__file__):
                    if os.path.splitext(f)[-1] in ['.txt', '.py']:
                        self._output_console.show_message(os.path.splitext(f)[-1])
                        self._output_console.show_message('Open File: ' + f)
                        self._scripts_tab.add_new_tab(os.path.basename(f), f)
                        if self._scripts_tab.count() == 2:
                            self._scripts_tab.removeTab(0)

    def _execute_command(self, cmd):
        """
        Internal function that executes the given command
        :param cmd: str, command to execute
        """

        if not cmd:
            return

        tmp_std_out = sys.stdout

        class StdOutProxy(object):
            def __init__(self, write_fn):
                self.write_fn = write_fn
                self.skip = False

            def write(self, text):
                if not self.skip:
                    stripped_text = text.rstrip('\n')
                    self.write_fn(stripped_text)
                    QCoreApplication.processEvents()
                self.skip = not self.skip

            def flush(self):
                pass
        sys.stdout = StdOutProxy(self._output_console.show_message)

        try:
            try:
                result = eval(cmd, self._namespace, self._namespace)
                if result is not None:
                    self._output_console.show_message(repr(result))
            except SyntaxError:
                pass
                # exec(cmd in self._namespace)
                # exec cmd in self._namespace
        except SystemExit:
            pass
            # self.close()
        except Exception:
            traceback_lines = traceback.format_exc().split('\n')
            for i in (3, 2, 1, -1):
                traceback_lines.pop(i)
            self._output_console.show_message('\n'.join(traceback_lines))

        sys.stdout = tmp_std_out

    def _open_find_replace(self):
        print('opening ...')
