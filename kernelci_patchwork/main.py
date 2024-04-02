# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Meta Inc
# Author: Nikolay Yurin <yurinnick@meta.com>

# pylint: disable=unused-argument disable=global-statement

"""KernelCI Patchwork Webhook main module"""
import logging
import os
from urllib.parse import urljoin

import kernelci.api
import kernelci.config
import requests.exceptions
from fastapi import Depends, FastAPI, HTTPException
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_versioning import VersionedFastAPI

from .models import PatchworkWebhook

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


def get_checkout_node(api, tree, branch):
    raise NotImplementedError()


@app.post("/webhook/patchwork")
async def post_webhook(
    webhook_data: PatchworkWebhook,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    """Patchwork event webhook handler"""

    project_name = webhook_data.event_data["link_name"]
    try:
        project_config = CONFIG["projects"][project_name]
    except KeyError as e:
        err_msg = "No configuration found for {project_name} patchwork project"
        logger.error(err_msg)
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail=err_msg
        ) from e

    api_config = CONFIG["api_configs"][ENVIRONMENT]
    api = kernelci.api.get_api(api_config, credentials.credentials)

    checkout_node = get_checkout_node(
        api=api, tree=project_config["tree"], branch=project_config["branch"]
    )

    patch_metadata = webhook_data.event_data["payload"]["patch"]
    patch_url = urljoin(patch_metadata["web_url"], "raw/?series=*")
    # Remove <> surrounding msgid and append .patch extention
    patch_name = "{}.patch".format(patch_metadata["msgid"][1:-1])

    patchset_node = {
        "name": "patchset",
        "path": ["checkout", "patchset"],
        "parent": checkout_node["id"],
        "artifacts": {patch_name: patch_url},
        "data": {
            "patchwork": {
                "patches": {
                    patch_name: patch_metadata["id"],
                }
            }
        },
    }

    try:
        node = api.create_node(patchset_node)
        logger.info(f"Succesfully scheduled a new node: {node}")
    except requests.exceptions.HTTPError as e:
        logger.error("API request failed: %s", e)
        raise HTTPException(status_code=e.response.status_code) from e
    except requests.exceptions.ConnectionError as e:
        logger.error("API connection failed: %s", e)
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE) from e

    return node
