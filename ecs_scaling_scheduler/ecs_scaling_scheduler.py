#    -*- coding: utf-8 -*-
#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

from copy import deepcopy
from datetime import datetime as dt

from boto3.session import Session
from compose_x_common.aws.application_autoscaling import list_all_scalable_targets
from compose_x_common.aws.ecs import (
    CLUSTER_NAME_FROM_ARN,
    describe_all_services,
    list_all_services,
)
from compose_x_common.compose_x_common import get_duration as get_time_delta_from_str
from compose_x_common.compose_x_common import get_future_time_delta, keyisset


def set_scheduled_action_for_service_scaling_target(
    service, resource_id=None, session=None, **kwargs
):
    """

    :param dict service:
    :param str resource_id:
    :param boto3.session.Session session:
    :return:
    """
    if session is None:
        session = Session()
    client = session.client("application-autoscaling")
    args = deepcopy(kwargs)
    args["ServiceNamespace"] = "ecs"
    args["ScalableDimension"] = "ecs:service:DesiredCount"
    if keyisset("target", service) and keyisset("ResourceId", service["target"]):
        args["ResourceId"] = service["target"]["ResourceId"]
    elif resource_id:
        args["ResourceId"] = resource_id
    else:
        raise KeyError("You must specify either resource_id or kwargs['ResourceId']")
    client.put_scheduled_action(**args)


def set_service_schedule_scaling_for_period(
    service_name: str,
    cluster_name: str,
    min_count: int,
    max_count: int,
    duration: str = None,
    action_name: str = None,
    session=None,
):
    """
    Function to set the scalable schedule for a given period of time (duration) from now
    :param str service_name:
    :param str cluster_name:
    :param int min_count:
    :param int max_count:
    :param str duration:
    :param str action_name:
    :param boto3.session.Session session:
    :return:
    """
    if session is None:
        session = Session()

    services = list_all_services(cluster_name, session=session)
    services_definition = describe_all_services(
        services, cluster_name, session=session, return_as_map=True, include=["TAGS"]
    )
    if service_name not in services_definition.keys():
        raise LookupError(f"Service {service_name} not found in {cluster_name}")
    the_service = services_definition[service_name]
    map_ecs_services_with_scalable_targets([the_service], session=session)
    del the_service["deployments"]
    del the_service["events"]

    now = dt.utcnow()
    if not action_name:
        api_action_name = f"{cluster_name}-{service_name}-onetime-scaling"
    else:
        api_action_name = action_name
    args = {
        "ServiceNamespace": "ecs",
        "ScheduledActionName": action_name
        if action_name
        else f"{api_action_name}__set",
        "ScalableDimension": "ecs:service:DesiredCount",
        "ResourceId": the_service["target"]["ResourceId"],
        "Schedule": f"at({now.strftime('%Y-%m-%dT%H:%M:%S')})",
        "StartTime": now,
        "EndTime": now + get_time_delta_from_str("1m"),
        "ScalableTargetAction": {"MinCapacity": min_count, "MaxCapacity": max_count},
    }
    set_scheduled_action_for_service_scaling_target(
        the_service, session=session, **args
    )
    if not duration:
        return
    restore_time_delta = get_time_delta_from_str(duration)
    restore_time = get_future_time_delta(now, restore_time_delta)
    restore_args = {
        "ServiceNamespace": "ecs",
        "ScheduledActionName": action_name
        if action_name
        else f"{api_action_name}__restore",
        "ScalableDimension": "ecs:service:DesiredCount",
        "ResourceId": the_service["target"]["ResourceId"],
        "Schedule": f"at({restore_time.strftime('%Y-%m-%dT%H:%M:%S')})",
        "StartTime": restore_time,
        "EndTime": restore_time + get_time_delta_from_str("1m"),
        "ScalableTargetAction": {
            "MinCapacity": the_service["target"]["MinCapacity"],
            "MaxCapacity": the_service["target"]["MaxCapacity"],
        },
    }
    set_scheduled_action_for_service_scaling_target(
        the_service, session=session, **restore_args
    )


def map_ecs_services_with_scalable_targets(services_list=None, session=None):
    """
    :param list[dict] services_list:
    :param boto3.session.Session session:
    :return:
    """
    if session is None:
        session = Session()
    ecs_targets = list_all_scalable_targets("ecs", session=session)
    for service in services_list:
        name = service["serviceName"]
        cluster = CLUSTER_NAME_FROM_ARN.match(service["clusterArn"]).group("name")
        target_id = f"service/{cluster}/{name}"
        for target in ecs_targets:
            if target["ResourceId"] == target_id:
                service["target"] = target
                break
        else:
            raise LookupError(f"Failed to find the target scaling for {name}")
