# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Meta Inc
# Author: Nikolay Yurin <yurinnick@meta.com>

from datetime import datetime
from typing import List

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Field, FileUrl


class PatchworkPatch(BaseModel):
    id: int = Field(
        description="Patch id",
    )
    hash: str = Field(
        description="Patch hash",
    )
    web_url: AnyHttpUrl = Field(
        description="Patch web url",
    )
    date: datetime = Field(
        description="Patch datetime",
    )
    mbox: AnyHttpUrl = Field(
        description="Patch mbox url",
    )

    _TIMESTAMP_FIELDS = ["date"]


class PatchworkSubmitter(BaseModel):
    id: int = Field(
        description="Patchwork submitter id",
    )
    url: AnyHttpUrl = Field(
        description="Patchwork submitter url",
    )
    name: str = Field(
        description="Patchwork submitter name",
    )
    email: str = Field(
        description="Patchwork submitter email",
    )


class Revision(BaseModel):
    tree: str = Field(description="Kernel revision tree")
    url: AnyUrl | FileUrl = Field(description="Kernel revision git URL")
    branch: str = Field(description="Kernel revision git branch")


class WebhookPatchwork(BaseModel):
    event: str = Field(
        description="Patchwork event type",
    )
    revision: Revision = Field(description="Kernel git revision")
    submitter: PatchworkSubmitter = Field(
        description="Patchwork submitter",
    )
    patches: List[PatchworkPatch] = Field(description="Ordered list of patches")
