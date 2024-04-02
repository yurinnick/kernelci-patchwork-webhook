# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Meta Inc
# Author: Nikolay Yurin <yurinnick@meta.com>

from typing import Any, Dict

from pydantic import BaseModel, Field


class PatchworkWebhook(BaseModel):
    event_data: Dict[str, Any] = Field(
        description="Patchwork event data",
    )
