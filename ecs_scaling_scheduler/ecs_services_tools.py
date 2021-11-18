#    -*- coding: utf-8 -*-
#    -*- coding: utf-8 -*-
#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

from copy import deepcopy

from boto3.session import Session
from compose_x_common.compose_x_common import keyisset

from ecs_scaling_scheduler.common import chunked_iterable


def list_all_services(
    cluster_name=None, services=None, next_token=None, session=None, **kwargs
):
    """

    :param cluster_name:
    :param services:
    :param next_token:
    :param session:
    :return:
    """
    if services is None:
        services = []
    if session is None:
        session = Session()
    client = session.client("ecs")
    args = deepcopy(kwargs)
    if cluster_name:
        args["cluster"] = cluster_name
    if next_token:
        args["nextToken"] = next_token
    services_r = client.list_services(**args)
    if keyisset("nextToken", services_r):
        return list_all_services(
            cluster_name, services, services_r["nextToken"], session, **args
        )
    services += services_r["serviceArns"]
    return services


def describe_all_services(
    services_list: list, cluster_name=None, session=None, as_map=False, **kwargs
):
    """

    :param list[str] services_list:
    :param str cluster_name:
    :param session:
    :param as_map:
    :return:
    """
    if session is None:
        session = Session()
    client = session.client("ecs")
    chunks = chunked_iterable(services_list, size=10)
    services = []
    if as_map:
        services = {}
    for services_chunk in chunks:
        args = deepcopy(kwargs)
        if cluster_name:
            args["cluster"] = cluster_name
        args["services"] = services_chunk
        args["include"] = ["TAGS"]
        services_r = client.describe_services(**args)
        for service in services_r["services"]:
            if as_map:
                services[service["serviceName"]] = service
            else:
                services.append(service)
    return services
