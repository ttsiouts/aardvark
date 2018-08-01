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


from aardvark import exception
from aardvark import utils
import aardvark.conf

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

    def post_job(self, details):
        # Make sure that the forwarded requests are for watched
        # aggregates.
        if not self._is_aggregate_watched(details.aggregates):
            # Skip this check if we have only one worker.
            if self.watched_aggregates != [[]]:
                LOG.error('Request for not watched aggregate %s ',
                          details.aggregates)
                raise exception.UnwatchedAggregate()

        backend_conf = {
            'board': CONF.reaper.job_backend,
            'path': "/var/lib/%s" % CONF.reaper.job_backend,
        }

        with backends.backend(self.board_name, backend_conf.copy()) as board:
            job = board.post("ReaperJob", book=None, details=details.to_dict())

    def _is_aggregate_watched(self, aggregates):
        l1 = [agg for agg in self.watched_aggregates if agg in aggregates]
        l2 = [agg for agg in aggregates if agg in self.watched_aggregates]
        return l1 == l2
