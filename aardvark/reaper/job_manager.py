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

import aardvark.conf
from aardvark import exception
from aardvark.reaper import reaper
from aardvark import utils

from oslo_log import log as logging
from taskflow.jobs import backends


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class JobManager(object):

    board_name = "ReaperBoard"

    def __init__(self):
        self.watched_aggregates = []

        for aggregates in utils.map_aggregate_names():
            if not isinstance(aggregates, list):
                aggregates = [aggregates]
            self.watched_aggregates += aggregates

        # HACK: if a request is received without excplicitly defined
        # aggregates, then any of the workers can pick it up. For this
        # reason, we make sure, that [] is always included in the list of
        # watched aggregates.
        if [] not in self.watched_aggregates:
            self.watched_aggregates.append([])

        # A reaper instance will be created if we are not in the multithreaded
        # mode.
        if not CONF.reaper.is_multithreaded:
            self.reaper_instance = reaper.Reaper(self.watched_aggregates)

        LOG.info("Reaper watching aggregates: %s", self.watched_aggregates)

    @utils.timeit
    def post_job(self, request):
        # Make sure that the forwarded requests are for watched
        # aggregates.
        if hasattr(request, 'aggregates'):
            self._is_aggregate_watched(request.aggregates)
        if CONF.reaper.is_multithreaded:
            self.multithreaded_handling(request)
        else:
            self.single_threaded_handling(request)

    def single_threaded_handling(self, request):
        self.reaper_instance.handle_request(request)

    def multithreaded_handling(self, request):
        backend_conf = {
            'board': CONF.reaper.job_backend,
            'path': "/var/lib/%s" % CONF.reaper.job_backend,
            'host': CONF.reaper.backend_host
        }

        with backends.backend(self.board_name, backend_conf.copy()) as board:
            board.post("ReaperJob", book=None, details=request.to_dict())

    def _is_aggregate_watched(self, aggregates):
        if self.watched_aggregates == [[]]:
            return
        for aggregate in aggregates:
            if aggregate not in self.watched_aggregates:
                LOG.error('Request for not watched aggregate %s', aggregate)
                raise exception.UnwatchedAggregate()
        return
