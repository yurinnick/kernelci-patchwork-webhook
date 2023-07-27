# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Meta Inc
# Author: Nikolay Yurin <yurinnick@meta.com>

# pylint: disable=unused-argument disable=global-statement

"""KernelCI Patchwork Webhook main module"""
import logging
import os

import kernelci.api
import kernelci.config
import requests.exceptions
from fastapi import Depends, FastAPI, HTTPException, status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_versioning import VersionedFastAPI

from .models import WebhookPatchwork

CONFIG = kernelci.config.load("config/patchwork.yaml")
ENVIRONMENT = os.environ.get("API_ENV", "localhost")

logger = logging.getLogger(__name__)

app = FastAPI()
app = VersionedFastAPI(
    app,
    version_format="{major}",
    prefix_format="/v{major}",
    enable_latest=True,
    default_version=(0, 0),
)


@app.get("/status")
async def status():
    return {"service": "KernelCI Patchwork Webhook API", "status": "ok"}


@app.post("/webhook/patchworks")
async def post_webhook(
    webhook_data: WebhookPatchwork,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    """Patchwork webhook handler"""
    if not webhook_data.patches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Patches list is empty"
        )

    head_patch_hash = webhook_data.patches[0].hash
    node_config = {
        "name": "checkout",
        "path": ["checkout"],
        "group": "patchwork-nodes",
        "revision": {
            "tree": webhook_data.revision.tree,
            "url": webhook_data.revision.url,
            "commit": "HEAD",
            "branch": webhook_data.revision.branch,
            "describe": (
                f"{webhook_data.revision.tree} tree"
                f" - {webhook_data.revision.branch} branch"
                f" - {head_patch_hash} patch"
            ),
        },
        "data": {
            "patchwork": {
                "version": 1,
                "payload": jsonable_encoder(webhook_data),
            }
        },
    }

    api_config = CONFIG["api_configs"][ENVIRONMENT]
    api = kernelci.api.get_api(api_config, credentials.credentials)
    try:
        node = api.create_node(node_config)
        logger.info(f"Succesfully scheduled a new node: {node}")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code)
    except requests.exceptions.ConnectionError as e:
        logger.error("bla")
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE)
    return {}
