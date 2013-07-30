# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013  Christophe Benz, Julien Hebert
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import subprocess
if sys.platform == 'win32':
    import WConio

try:
    from termcolor import colored
except ImportError:
    def colored(s, color=None, on_color=None, attrs=None):
        if attrs is not None and 'bold' in attrs:
            return '%s%s%s' % (IFormatter.BOLD, s, IFormatter.NC)
        else:
            return s

try:
    import tty
    import termios
except ImportError:
    PROMPT = '--Press return to continue--'

    def readch():
        return sys.stdin.readline()
else:
    PROMPT = '--Press a key to continue--'

    def readch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(fd)
        try:
            c = sys.stdin.read(1)
            # XXX do not read magic number
            if c == '\x03':
                raise KeyboardInterrupt()
            return c
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

from weboob.capabilities.base import CapBaseObject
from weboob.tools.application.console import ConsoleApplication
from weboob.tools.ordereddict import OrderedDict


__all__ = ['IFormatter', 'MandatoryFieldsNotFound']


class MandatoryFieldsNotFound(Exception):
    def __init__(self, missing_fields):
        Exception.__init__(self, u'Mandatory fields not found: %s.' % ', '.join(missing_fields))


class IFormatter(object):
    MANDATORY_FIELDS = None

    BOLD = ConsoleApplication.BOLD
    NC = ConsoleApplication.NC

    def colored(self, string, color, attrs=None, on_color=None):
        if self.outfile != sys.stdout or not (os.isatty(self.outfile.fileno())):
            return string

        if isinstance(attrs, basestring):
            attrs = [attrs]
        return colored(string, color, on_color=on_color, attrs=attrs)

    def __init__(self, display_keys=True, display_header=True, outfile=sys.stdout):
        self.display_keys = display_keys
        self.display_header = display_header
        self.interactive = False
        self.print_lines = 0
        self.termrows = 0
        self.outfile = outfile
        # XXX if stdin is not a tty, it seems that the command fails.

        if os.isatty(sys.stdout.fileno()) and os.isatty(sys.stdin.fileno()):
            if sys.platform == 'win32':
                self.termrows = WConio.gettextinfo()[8]
            else:
                self.termrows = int(
                    subprocess.Popen('stty size', shell=True, stdout=subprocess.PIPE).communicate()[0].split()[0]
                )

    def output(self, formatted):
        if self.outfile != sys.stdout:
            with open(self.outfile, "a+") as outfile:
                outfile.write(formatted.encode('utf-8'))

        else:
            for line in formatted.split('\n'):
                if self.termrows and (self.print_lines + 1) >= self.termrows:
                    self.outfile.write(PROMPT)
                    self.outfile.flush()
                    readch()
                    self.outfile.write('\b \b' * len(PROMPT))
                    self.print_lines = 0

                if isinstance(line, unicode):
                    line = line.encode('utf-8')
                print line
                self.print_lines += 1

    def start_format(self, **kwargs):
        pass

    def flush(self):
        pass

    def format(self, obj, selected_fields=None, alias=None):
        """
        Format an object to be human-readable.
        An object has fields which can be selected.

        :param obj: object to format
        :type obj: CapBaseObject or dict
        :param selected_fields: fields to display. If None, all fields are selected
        :type selected_fields: tuple
        :param alias: an alias to use instead of the object's ID
        :type alias: unicode
        """
        if isinstance(obj, CapBaseObject):
            if selected_fields is not None and not '*' in selected_fields:
                obj = obj.copy()
                for name, value in obj.iter_fields():
                    if not name in selected_fields:
                        delattr(obj, name)

            if self.MANDATORY_FIELDS:
                missing_fields = set(self.MANDATORY_FIELDS) - set([name for name, value in obj.iter_fields()])
                if missing_fields:
                    raise MandatoryFieldsNotFound(missing_fields)

            formatted = self.format_obj(obj, alias)
        else:
            try:
                obj = OrderedDict(obj)
            except ValueError:
                raise TypeError('Please give a CapBaseObject or a dict')

            if selected_fields is not None and not '*' in selected_fields:
                obj = obj.copy()
                for name, value in obj.iteritems():
                    if not name in selected_fields:
                        obj.pop(name)

            if self.MANDATORY_FIELDS:
                missing_fields = set(self.MANDATORY_FIELDS) - set(obj.iterkeys())
                if missing_fields:
                    raise MandatoryFieldsNotFound(missing_fields)

            formatted = self.format_dict(obj)

        if formatted:
            self.output(formatted)
        return formatted

    def format_obj(self, obj, alias=None):
        """
        Format an object to be human-readable.
        Called by format().
        This method has to be overridden in child classes.

        :param obj: object to format
        :type obj: CapBaseObject
        :rtype: str
        """
        return self.format_dict(obj.to_dict())

    def format_dict(self, obj):
        """
        Format a dict to be human-readable.

        :param obj: dict to format
        :type obj: dict
        :rtype: str
        """
        return NotImplementedError()


class PrettyFormatter(IFormatter):
    def format_obj(self, obj, alias):
        title = self.get_title(obj)
        desc = self.get_description(obj)

        if alias is not None:
            result = u'%s %s %s (%s)' % (self.colored('%2s' % alias, 'red', 'bold'),
                                         self.colored(u'—', 'cyan', 'bold'),
                                         self.colored(title, 'yellow', 'bold'),
                                         self.colored(obj.backend, 'blue', 'bold'))
        else:
            result = u'%s %s %s' % (self.colored(obj.fullid, 'red', 'bold'),
                                    self.colored(u'—', 'cyan', 'bold'),
                                    self.colored(title, 'yellow', 'bold'))

        if desc is not None:
            result += u'\n\t%s' % self.colored(desc, 'white')

        return result

    def get_title(self, obj):
        raise NotImplementedError()

    def get_description(self, obj):
        return None
