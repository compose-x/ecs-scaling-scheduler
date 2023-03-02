#    -*- coding: utf-8 -*-
#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

"""
Handles discovery ECS Services based on tags
"""

from __future__ import annotations

import json
import os


def import_tag_filters(env_var_name: str) -> list:
    """
    From environment variable, determines the tags and values to use for services discovery.
    The environment variable can either be a valid JSON string or a comma-separated list of key=value pairs.

    :param env_var_name: The environment variable name
    :return: A tuple of (tags, values)
    """
    tags: list = []
    try:
        tags = json.loads(os.environ[env_var_name])
    except json.JSONDecodeError:
        for kv in os.environ[env_var_name].split(":"):
            k, v = kv.split("=")
            tags.append({"Key": k, "Values": [v]})
    return tags
