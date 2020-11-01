#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains definition for tpScriptEditor sessions
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json
import codecs

import tpDcc
from tpDcc.libs.python import fileio, decorators


class Session(object):
    def __init__(self, session_path):
        self._path = session_path
        if not os.path.isfile(session_path):
            fileio.create_file(os.path.basename(session_path), os.path.dirname(session_path))
            with open(session_path, 'w') as fh:
                fh.write('{}')

    def read(self):
        """
        Reads the current session status
        :return: list
        """

        if not os.path.exists(self._path):
            return list()

        with codecs.open(self._path, 'r', 'utf-16') as stream:
            try:
                return json.load(stream)
            except Exception as exc:
                tpDcc.logger.error('Error while reading Script Editor session file: {} | {}'.format(self._path, exc))
                return list()

    def write(self, data):
        """
        Writes session into disk
        :param data: dict
        :return:
        """

        with codecs.open(self._path, 'w', 'utf-16') as stream:
            json.dump(data, stream, indent=4)

        return self._path


@decorators.add_metaclass(decorators.Singleton)
class SessionManager(object):
    def __init__(self):
        super(SessionManager, self).__init__()

        self._current_session = None

    @property
    def current_session(self):
        return self._current_session

    @current_session.setter
    def current_session(self, session):
        self._current_session = session
