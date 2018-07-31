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

from functools import wraps
from oslo_concurrency import lockutils
from oslo_log import log

import aardvark.conf
from aardvark.api.rest import nova


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


def retries(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < 3:
            try:
                return fn(*args, **kwargs)
            except exception.RetryException:
                retries += 1
        LOG.error('Execution of %s failed: Retries exceeded!', fn.__name__)
    return wrapper


class SafeDict(dict):
    """Provides a threadsafe dictionary by locking the methods needed"""

    @lockutils.synchronized('reaper_lock')
    def __setitem__(self, key, item):
        super(SafeDict, self).__setitem__(key, item)

    @lockutils.synchronized('reaper_lock')
    def __getitem__(self, key):
        return super(SafeDict, self).__getitem__(key)

    @lockutils.synchronized('reaper_lock')
    def __delitem__(self, key):
        super(SafeDict, self).__delitem__(key)


def map_aggregate_names():
    """Maps aggregate names to uuids"""
    novaclient = nova.novaclient()
    aggregate_map = {
        agg.name: agg.uuid for agg in novaclient.aggregates.list()
    }
    uuids = []
    for aggregates in CONF.reaper.watched_aggregates:
        aggregates = aggregates.split('|')
        uuids.append([aggregate_map[agg.strip()] for agg in aggregates])
    return uuids
