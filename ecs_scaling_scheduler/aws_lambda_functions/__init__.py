#    -*- coding: utf-8 -*-
#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

"""
AWS Lambda Handlers to use in AWS Lambda Functions.

This package uses the library directly and is aimed to be a self-contained suite of helper functions that can be used
directly into AWS accounts.

"""

from boto3.session import Session
from compose_x_common.compose_x_common import set_else_none

from ecs_scaling_scheduler.ecs_scaling_scheduler import (
    set_service_schedule_scaling_for_period,
)


def one_time_set_ecs_set_desired_count(event: dict, context: dict):
    """
    Function that will create a One-Time AT Scaling policy to change the ecs:DesiredCount dimension of a service.

    :param dict event:
    :param dict context:
    :return:
    """
    cluster_name = set_else_none("ecsClusterName", event)
    service_name = set_else_none("ecsServiceName", event)
    desired_count = int(set_else_none("desiredCount", event))
    scaling_duration = set_else_none("scalingDuration", event)
    action_name = set_else_none("actionName", event)
    session = Session()

    set_service_schedule_scaling_for_period(
        service_name=service_name,
        cluster_name=cluster_name,
        min_count=desired_count,
        max_count=desired_count,
        duration=scaling_duration,
        action_name=action_name,
        session=session,
    )
