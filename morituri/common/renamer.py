# -*- Mode: Python; test-case-name: morituri.test.test_common_renamer -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of morituri.
#
# morituri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# morituri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with morituri.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile

"""
Rename files on file system and inside metafiles in a resumable way.
"""


class Operator(object):

    def __init__(self, statePath, key):
        self._todo = []
        self._done = []
        self._statePath = statePath
        self._key = key
        self._resuming = False

    def addOperation(self, operation):
        """
        Add an operation.
        """
        self._todo.append(operation)

    def load(self):
        """
        Load state from the given state path using the given key.
        Verifies the state.
        """
        todo = os.path.join(self._statePath, self._key + '.todo')
        handle = open(todo, 'r')
        lines = []
        for line in handle.readlines():
            lines.append(line)
            name, data = line.split(' ', 1)
            cls = globals()[name]
            operation = cls.deserialize(data)
            self._todo.append(operation)


        done = os.path.join(self._statePath, self._key + '.done')
        i = 0
        if os.path.exists(done):
            handle = open(done, 'r')
            for i, line in enumerate(handle.readlines()):
                assert line == lines[i], "line %s is different than %s" % (
                    line, lines[i])
                self._done.append(self._todo[i])

        # last task done is i; check if the next one might have gotten done.
        self._resuming = True

    def save(self):
        """
        Saves the state to the given state path using the given key.
        """
        # only save todo first time
        todo = os.path.join(self._statePath, self._key + '.todo')
        if not os.path.exists(todo):
            handle = open(todo, 'w')
            for o in self._todo:
                name = o.__class__.__name__
                data = o.serialize()
                handle.write('%s %s\n' % (name, data))
            handle.close()

        # save done every time
        done = os.path.join(self._statePath, self._key + '.done')
        handle = open(done, 'w')
        for o in self._done:
            name = o.__class__.__name__
            data = o.serialize()
            handle.write('%s %s\n' % (name, data))
        handle.close()

    def start(self):
        """
        Execute the operations
        """

    def next(self):
        operation = self._todo[len(self._done)]
        if self._resuming:
            operation.redo()
            self._resuming = False
        else:
            operation.do()

        self._done.append(operation)
        self.save()


class FileRenamer(Operator):

    def addRename(self, source, destination):
        """
        Add a rename operation.

        @param source:      source filename
        @type  source:      str
        @param destination: destination filename
        @type  destination: str
        """


class Operation(object):

    def verify(self):
        """
        Check if the operation will succeed in the current conditions.
        Consider this a pre-flight check.

        Does not eliminate the need to handle errors as they happen.
        """

    def do(self):
        """
        Perform the operation.
        """
        pass

    def redo(self):
        """
        Perform the operation, without knowing if it already has been
        (partly) performed.
        """
        self.do()

    def serialize(self):
        """
        Serialize the operation.
        The return value should bu usable with L{deserialize}

        @rtype: str
        """

    def deserialize(cls, data):
        """
        Deserialize the operation with the given operation data.

        @type  data: str
        """
        raise NotImplementedError
    deserialize = classmethod(deserialize)


class RenameFile(Operation):

    def __init__(self, source, destination):
        self._source = source
        self._destination = destination

    def verify(self):
        assert os.path.exists(self._source)
        assert not os.path.exists(self._destination)

    def do(self):
        os.rename(self._source, self._destination)

    def serialize(self):
        return '"%s" "%s"' % (self._source, self._destination)

    def deserialize(cls, data):
        _, source, __, destination, ___ = data.split('"')
        return RenameFile(source, destination)
    deserialize = classmethod(deserialize)

    def __eq__(self, other):
        return self._source == other._source \
            and self._destination == other._destination


class RenameInFile(Operation):

    def __init__(self, path, source, destination):
        self._path = path
        self._source = source
        self._destination = destination

    def verify(self):
        assert os.path.exists(self._path)
        # check if the source exists in the given file

    def do(self):
        handle = open(self._path)
        (fd, name) = tempfile.mkstemp(suffix='.morituri')

        for s in handle:
            os.write(fd, s.replace(self._source, self._destination))

        handle.close()
        os.close(fd)
        os.rename(name, self._path)

    def serialize(self):
        return '"%s" "%s" "%s"' % (self._path, self._source, self._destination)

    def deserialize(cls, data):
        _, path, __, source, ___, destination, ____ = data.split('"')
        return RenameInFile(path, source, destination)
    deserialize = classmethod(deserialize)

    def __eq__(self, other):
        return self._source == other._source \
            and self._destination == other._destination \
            and self._path == other._path
