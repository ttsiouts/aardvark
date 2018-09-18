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

from collections import Iterable
import eventlet.queue
import eventlet.timeout
from functools import wraps
from oslo_concurrency import lockutils
from oslo_log import log
import time

from aardvark.api.rest import nova
import aardvark.conf
from aardvark import exception


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


def is_multithreaded(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if CONF.reaper.is_multithreaded:
            return fn(*args, **kwargs)
        return None
    return wrapper


def notifications_enabled(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if CONF.aardvark.enable_notification_handling:
            return fn(*args, **kwargs)
        return None
    return wrapper


def watermark_enabled(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if CONF.aardvark.enable_watermark_mode:
            return fn(*args, **kwargs)
        return None
    return wrapper


def retries(side_effect=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < 3:
                try:
                    return fn(*args, **kwargs)
                except exception.RetryException:
                    retries += 1
            message = 'Execution of %s failed: Retries exceeded!' % fn.__name__
            if side_effect is not None:
                raise side_effect(message)
            LOG.error(message)
        return wrapper
    return decorator


def timeit(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if CONF.aardvark.benchmarking_mode:
            now = time.time()
        result = fn(*args, **kwargs)
        if CONF.aardvark.benchmarking_mode:
            LOG.info("Took %s secs to execute %s",
                     time.time() - now, fn.__name__)
        return result
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
        try:
            aggregates = aggregates.split('|')
            uuids.append([aggregate_map[agg.strip()] for agg in aggregates])
        except KeyError:
            message = "One of the configured aggregates was not found"
            raise exception.BadConfigException(message)
    return uuids


def parallelize(max_results=-1, num_workers=10, timeout=10):
    """Helper function to parallelize a workload

    This decorator can be used to parallelize a method.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            greenthreads = []
            responded = []
            results = []
            queue = eventlet.queue.LightQueue()

            @wraps(func)
            def parallel_task(i, *ars, **kwars):
                try:
                    result = func(*ars, **kwars)
                    if not isinstance(result, Iterable):
                        result = [result]
                    queue.put((i, result))
                except Exception:
                    pass

            workload = args[0]
            for i, load in enumerate(split_workload(num_workers, workload)):
                ar = [load]
                ar += args[1:]
                greenthreads.append(
                    (i, eventlet.spawn(parallel_task, i, *ar, **kwargs))
                )

            with eventlet.timeout.Timeout(timeout, exception.ParallelTimeout):
                try:
                    while len(responded) < len(greenthreads):
                        if max_results != -1 and max_results <= len(results):
                            LOG.info("Max results %s, gathered for %s",
                                     max_results, func.__name__)
                            break
                        i, result = queue.get()
                        responded.append(i)
                        results += result
                except exception.ParallelTimeout:
                    LOG.error("Timeout for parallel task exceeded")
                    pass

            for id_, greenthread in greenthreads:
                if id_ not in responded:
                    greenthread.kill()
                else:
                    greenthread.wait()
            return results
        return wrapper
    return decorator


def split_workload(num_workers, workload):
    jobs = []

    length = len(workload)
    ratio = length / float(num_workers)
    ratio = int(ratio) + 1 if ratio > int(ratio) else int(ratio)

    for i in range(0, num_workers):
        if i == num_workers - 1:
            jobs.append(l for l in workload[i * ratio:])
        else:
            jobs.append(l for l in workload[i * ratio: (i + 1) * ratio])
        if (i + 1) * ratio >= length:
            break
    return jobs
