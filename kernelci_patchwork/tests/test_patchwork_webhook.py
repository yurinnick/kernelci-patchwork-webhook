# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Meta Inc
# Author: Nikolay Yurin <yurinnick@meta.com>

import unittest

from fastapi.testclient import TestClient

from kernelci_patchwork.main import app


class TestPatchworkWebhook(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = TestClient(app)

    def test_status(self):
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"service": "KernelCI Patchwork Webhook API", "status": "ok"},
        )
