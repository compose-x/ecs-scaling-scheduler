#   -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille <john@compose-x.io>

import re

from boto3.session import Session
from compose_x_common.compose_x_common import keyisset

from ecs_scaling_scheduler.common import chunked_iterable

CLUSTER_NAME_FROM_ARN = re.compile(
    r"arn:aws(?:-[a-z-]+)?:ecs:[\S]+:[\d]{12}:cluster/(?P<name>[a-zA-Z0-9-_]+$)"
)


def list_all_ecs_clusters(clusters=None, next_token=None, session=None):
    """

    :param clusters:
    :param next_token:
    :param session:
    :return:
    """
    if clusters is None:
        clusters = []
    if session is None:
        session = Session()
    client = session.client("ecs")
    if next_token:
        clusters_r = client.list_clusters(nextToken=next_token)
    else:
        clusters_r = client.list_clusters()
    if keyisset("nextToken", clusters_r):
        return list_all_ecs_clusters(clusters, clusters_r["nextToken"], session)
    clusters += clusters_r["clusterArns"]
    return clusters


def describe_all_ecs_clusters(
    clusters_to_list: list, session=None, return_as_map=False
):
    """

    :param clusters_to_list:
    :param session:
    :param return_as_map:
    :return:
    """
    clusters = []
    if return_as_map:
        clusters = {}
    if session is None:
        session = Session()
    client = session.client("ecs")
    cluster_chunks = chunked_iterable(clusters_to_list, size=10)
    for clusters_to_describe in cluster_chunks:
        clusters_r = client.describe_clusters(
            clusters=clusters_to_describe,
            include=[
                "ATTACHMENTS",
                "CONFIGURATIONS",
                "SETTINGS",
                "STATISTICS",
                "TAGS",
            ],
        )
        for cluster in clusters_r["clusters"]:
            if return_as_map:
                clusters[cluster["clusterName"]] = cluster
            else:
                clusters.append(cluster)
            clusters.append(cluster)

    return clusters
