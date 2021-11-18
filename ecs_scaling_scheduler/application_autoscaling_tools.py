#    -*- coding: utf-8 -*-
#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>


from copy import deepcopy

import boto3
from boto3.session import Session
from compose_x_common.compose_x_common import keyisset

from ecs_scaling_scheduler.ecs_cluster_tools import CLUSTER_NAME_FROM_ARN


def list_all_scalable_targets(
    namespace=None, targets=None, next_token=None, session=None, **kwargs
):
    """

    :param str namespace: Required parameter
    :param targets:
    :param next_token:
    :param session:
    :param kwargs:
    :return:
    """
    if targets is None:
        targets = []
    if session is None:
        session = Session()
    client = session.client("application-autoscaling")
    args = deepcopy(kwargs)
    if not namespace and not keyisset("ServiceNamespace", args):
        raise KeyError(
            "ServiceNamespace must be set either via `namespace` or `kwargs['ServiceNamespace']`"
        )
    if not keyisset("ServiceNamespace", args):
        args["ServiceNamespace"] = namespace
    if next_token:
        args["NextToken"] = next_token
    targets_r = client.describe_scalable_targets(**args)
    if keyisset("NextToken", targets_r):
        return list_all_scalable_targets(
            targets, targets_r["NextToken"], session, **args
        )
    targets += targets_r["ScalableTargets"]
    return targets


def map_ecs_services_with_scalable_targets(services_list: list, session=None):
    """
    :param services_list:
    :param session:
    :return:
    """
    if session is None:
        session = Session()
    client = session.client("application-autoscaling")

    for service in services_list:
        cluster = CLUSTER_NAME_FROM_ARN.match(service["ClusterArn"]).group("name")
        service_name = service["serviceName"]
        target = f"service/{cluster}/{service_name}"
