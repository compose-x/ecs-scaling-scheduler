#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2021 John Mille <john@compose-x.io>

from __future__ import annotations

from typing import Any, Union
from compose_x_common.compose_x_common import keyisset


def get_tag_value_for_key(key: str, tags: list) -> Union[Any, None]:
    """
    Get the value of a tag with a given key.

    :param str key:
    :param list tags:
    :return:
    """
    for tag in tags:
        if keyisset("Key", tag) and keyisset("Value", tag) and tag["Key"] == key:
            return tag["Value"]
    return None
