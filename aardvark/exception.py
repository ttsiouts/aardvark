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

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class AardvarkException(Exception):
    """Base Reaper Exception"""

    message = "Unknown error occurred during Reaper's execution"

    def __init__(self, message=None):
        if message:
            self.message = message
        super(AardvarkException, self).__init__(self.message)


class RetryException(AardvarkException):
    """Generic Exception for the retries mechanism"""
    message = ''


class ReaperException(AardvarkException):
    """Base Reaper Exception"""
    message = "Unknown error occurred during Reaper's execution"


class NotEnoughResources(ReaperException):
    message = "Unknown error occurred while trying to make space"


class PreemptibleRequest(ReaperException):
    message = "Making space only for non-preemptible reqs."


class UnwatchedAggregate(ReaperException):
    message = "Received request for unwatched aggregate."


class UnknownRequestType(ReaperException):
    message = "Received request of unknown type."
