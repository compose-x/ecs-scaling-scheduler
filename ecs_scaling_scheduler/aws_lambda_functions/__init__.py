#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

"""
AWS Lambda Handlers to use in AWS Lambda Functions.

This package uses the library directly and is aimed to be a self-contained suite of helper functions that can be used
directly into AWS accounts.

"""

from __future__ import annotations

import json
import logging
from os import environ

from boto3.session import Session
from compose_x_common.aws.ecs.services import SERVICE_ARN_RE, get_ecs_services_from_tags
from compose_x_common.compose_x_common import set_else_none

from ecs_scaling_scheduler.aws_lambda_functions.common import get_tag_value_for_key
from ecs_scaling_scheduler.common import import_tag_filters
from ecs_scaling_scheduler.ecs_scaling_scheduler import (
    set_service_schedule_scaling_for_period,
)

LOG = logging.getLogger(__name__)
try:
    logging.getLogger().setLevel(environ.get("LOG_LEVEL", "ERROR").upper())
except Exception as error:
    print(error)
    print("Falling back to INFO logging")
    logging.getLogger().setLevel(logging.INFO)


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


def services_event_warmup(event: dict, context: dict) -> None:
    """
    Function that will discover services based on a pre-defined tags (not in the events payload).
    Based on the tags of the services, these will be scaled with a one-time action rule
    """

    cluster_name = environ.get("ECS_CLUSTER_NAME")
    if not cluster_name:
        raise EnvironmentError(f"Missing value for {cluster_name}")
    services_tags = import_tag_filters("WARMUP_ECS_SERVICES_TAGS")
    dimension_tag = environ.get("WARMUP_DIMENSION_TAG", "warmup-dimension")
    warmup_duration_tag = environ.get("WARMUP_DURATION_TAG", "warmup-duration")
    message = set_else_none("Message", event)
    name = set_else_none("AlarmName", event, "warmup")
    if message:
        try:
            content = json.loads(message)
            name = set_else_none("AlarmName", content, "warmup")
        except json.JSONDecodeError:
            LOG.info("No message body found in event")
    session = Session()
    services = get_ecs_services_from_tags(services_tags, session=session)
    for service in services:
        service_parts = SERVICE_ARN_RE.match(service["ResourceARN"])
        service_cluster = service_parts.group("cluster")
        service_name = service_parts.group("id")
        if service_cluster != cluster_name:
            LOG.info(
                "Service %s is not in cluster %s: %s",
                service_name,
                cluster_name,
                service_cluster,
            )
            continue
        dimension_tag_value = get_tag_value_for_key(dimension_tag, service["Tags"])
        if not dimension_tag_value:
            LOG.info(f"Service does not have {dimension_tag} tag: {service_name}")
            continue
        dimension_value = dimension_tag_value.split(r":")
        warmup_delay = get_tag_value_for_key(warmup_duration_tag, service["Tags"])
        if not warmup_delay:
            LOG.info(
                f"Service does not have {warmup_duration_tag} tag set: %s", service_name
            )
            continue

        LOG.info(
            "Service & Cluster:  %s %s | %s %s",
            service_name,
            service_cluster,
            dimension_value,
            warmup_delay,
        )
        count = int(dimension_value)
        set_service_schedule_scaling_for_period(
            service_name=service_name,
            cluster_name=service_cluster,
            min_count=count,
            max_count=count,
            duration=warmup_delay,
            action_name=name,
            session=session,
        )
