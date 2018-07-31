# Copyright (c) 2018 European Organization for Nuclear Research.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import six

from aardvark import exception
from aardvark.reaper import reaper
import aardvark.conf

from oslo_log import log as logging
from taskflow.jobs import backends
from taskflow.utils import threading_utils
import time


LOG = logging.getLogger(__name__)


CONF = aardvark.conf.CONF


SHARED_CONF = {
    'path': "/var/lib/zookeeper",
    'board': 'zookeeper',
}


class JobManager(object):

    board_name = "ReaperBoard"

    def __init__(self):
        if six.PY3:
            # TODO(ttsiouts): Hack to make eventlet work right, remove when the
            # following is fixed: https://github.com/eventlet/eventlet/issues/230
            from taskflow.utils import eventlet_utils as _eu  # noqa
            try:
                import eventlet as _eventlet  # noqa
            except ImportError:
                pass
        self.watched_aggregates = []
        self.reaper_instances = []
        self._setup_workers(CONF.reaper.watched_aggregates)
        # HACK: if a request is received without excplicitly defined
        # aggregates, then any of the workers can pick it up. For this
        # reason, we make sure, that [] is always included in the list of
        # watched aggregates.
        if [] not in self.watched_aggregates:
            self.watched_aggregates.append([])

    def _setup_workers(self, watched_aggregates):
        if len(watched_aggregates) == 0:
            LOG.debug('One worker for all infrastructure will be started')
            watched_aggregates = [watched_aggregates]

        for aggregates in watched_aggregates:
            if not isinstance(aggregates, list):
                aggregates = [aggregates]
            instance = reaper.Reaper(aggregates)
            instance.worker = threading_utils.daemon_thread(instance.job_handler)
            self.reaper_instances.append(instance)
            self.watched_aggregates.append(aggregates)

    def start_workers(self):
        LOG.info('Starting workers')
        for instance in self.reaper_instances:
            instance.worker.start()

    def stop_workers(self):
        LOG.info('Stoping workers')
        for instance in self.reaper_instances:
            instance.stop_handling()
            instance.worker.join()

    def post_job(self, details):
        # Make sure that the forwarded requests are for watched
        # aggregates
        if details.aggregates not in self.watched_aggregates:
            raise exception.UnwatchedAggregate()

        with backends.backend(self.board_name, SHARED_CONF.copy()) as board:
            job = board.post("ReaperJob", book=None, details=details.to_dict())
            print "posted: %s" % job
