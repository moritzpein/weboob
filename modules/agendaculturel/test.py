# -*- coding: utf-8 -*-

# Copyright(C) 2015      Bezleputh
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


from weboob.tools.test import BackendTest
from weboob.tools.value import Value
from datetime import datetime


class AgendaculturelTest(BackendTest):
    MODULE = 'agendaculturel'

    def setUp(self):
        if not self.is_backend_configured():
            self.backend.config['place'] = Value(value='paris')

    def test_agendaculturel(self):
        l = list(self.backend.list_events(datetime.now()))
        assert len(l)
        event = self.backend.get_event(l[0].id)
        self.assertTrue(event.url, 'URL for event "%s" not found: %s' % (event.id, event.url))
