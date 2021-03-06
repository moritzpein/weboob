# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon, Laurent Bachelier
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

import sys
from functools import wraps
from unittest import TestCase

from weboob.core import Weboob

# This is what nose does for Python 2.6 and lower compatibility
# We do the same so nose becomes optional
try:
    from unittest.case import SkipTest
except:
    from nose.plugins.skip import SkipTest


__all__ = ['BackendTest', 'SkipTest', 'skip_without_config']


class BackendTest(TestCase):
    MODULE = None

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)

        self.backends = {}
        self.backend_instance = None
        self.backend = None
        self.weboob = Weboob()

        # Skip tests when passwords are missing
        self.weboob.requests.register('login', self.login_cb)

        if self.weboob.load_backends(modules=[self.MODULE]):
            # provide the tests with all available backends
            self.backends = self.weboob.backend_instances

    def login_cb(self, backend_name, value):
        raise SkipTest('missing config \'%s\' is required for this test' % value.label)

    def run(self, result):
        """
        Call the parent run() for each backend instance.
        Skip the test if we have no backends.
        """
        # This is a hack to fix an issue with nosetests running
        # with many tests. The default is 1000.
        sys.setrecursionlimit(10000)
        try:
            if not len(self.backends):
                self.backend = self.weboob.build_backend(self.MODULE, nofail=True)
                TestCase.run(self, result)
            else:
                # Run for all backend
                for backend_instance in self.backends.keys():
                    print(backend_instance)
                    self.backend = self.backends[backend_instance]
                    TestCase.run(self, result)
        finally:
            self.weboob.deinit()

    def shortDescription(self):
        """
        Generate a description with the backend instance name.
        """
        # do not use TestCase.shortDescription as it returns None
        return '%s [%s]' % (str(self), self.backend_instance)

    def is_backend_configured(self):
        """
        Check if the backend is in the user configuration file
        """
        return self.weboob.backends_config.backend_exists(self.backend.config.instname)


def skip_without_config(*keys):
    """Decorator to skip a test if backend config is missing

    :param keys: if any of these keys is missing in backend config, skip test. Can be empty.
    """

    for key in keys:
        if callable(key):
            raise TypeError('skip_without_config() must be called with arguments')

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            config = self.backend.config
            if not self.is_backend_configured():
                raise SkipTest('a backend must be declared in configuration for this test')
            for key in keys:
                if not config[key].get():
                    raise SkipTest('config key %r is required for this test' %
                                   key)

            return func(self, *args, **kwargs)
        return wrapper
    return decorator
