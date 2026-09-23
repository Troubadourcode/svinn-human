"""Contract tests for the Case API observe stub.

How to run, from ``packages/case-api``::

    make test

From the repo root::

    PYTHONPATH=packages/case-api/src python3 -m unittest discover \\
        -s packages/case-api/tests -v

The suite starts ``case_api.server.Handler`` in-process on 127.0.0.1 and
an ephemeral port (it does not call ``server.main``, which binds :8787
until killed). Stdlib only.

**real_gate is false.** These tests do not import ``sandbox.*``, do not
call Entra or JSM, and do not arm an Action plane.

Entra lab ids live in ``lab_fixtures.py`` (no secrets). JSM site and
project are still unset, so ``test_lab_ids_do_not_arm_real_gate`` stays
skipped. CI does not wait on a lab and does not claim ``real_gate``.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from http.server import ThreadingHTTPServer

import lab_fixtures
from case_api.case_sm import STATES
from case_api.server import Handler

# Platform CaseStatus literals (case_sm.STATES / OpenAPI). Not CTO shorthand.
HOLD_PENDING = "HOLD_PENDING"
ACTION_PENDING = "ACTION_PENDING"
RECEIVED = "RECEIVED"

_CREATE_BODY = {
    "protected_action": "mfa_reset",
    "mode": "hold",
    "subject": {"upn": "contract-user@example.com"},
    # Synthetic correlation only. Real lab issue keys belong in lab_fixtures.
    "jsm_ticket_ref": {"key": "CONTRACT-OBSERVE"},
}

_RELEASE_BODY = {
    "approver_id": "recovery_owner",
    "action_ceiling_use": ["mfa_methods_reset"],
}


def request_json(base_url, method, path, body=None, idempotency_key=None, timeout=5):
    """HTTP helper. Returns ``(status, parsed_json)`` for error responses too."""
    headers = {}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            parsed = json.loads(raw.decode()) if raw else None
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        parsed = json.loads(raw.decode()) if raw else None
        return exc.code, parsed


class CaseApiContractTest(unittest.TestCase):
    """HTTP contract for one in-process observe stub (real_gate false)."""

    tenant = "contract-observe"

    @classmethod
    def setUpClass(cls):
        # Ephemeral port so a developer stub on :8787 is left alone.
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.httpd.daemon_threads = True
        host, port = cls.httpd.server_address
        cls.base_url = f"http://{host}:{port}"
        cls._thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls._thread.start()
        status, body = request_json(cls.base_url, "GET", "/healthz")
        if status != 200 or not body or body.get("real_gate") is not False:
            raise RuntimeError(f"observe stub did not become ready: {status} {body}")

    @classmethod
    def tearDownClass(cls):
        httpd = getattr(cls, "httpd", None)
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()
        thread = getattr(cls, "_thread", None)
        if thread is not None:
            thread.join(timeout=5)

    def _request(self, method, path, body=None, idempotency_key=None):
        return request_json(self.base_url, method, path, body, idempotency_key)

    def _create_path(self):
        return f"/v1/tenants/{self.tenant}/action-requests"

    def _case_path(self, case_id):
        return f"{self._create_path()}/{case_id}"

    def _release_path(self, case_id):
        return f"{self._case_path(case_id)}/release"

    def test_healthz_real_gate_is_false(self):
        status, body = self._request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertIs(body["real_gate"], False)
        self.assertEqual(body["service"], "case-api")
        self.assertIs(body["ok"], True)

    def test_create_get_and_release_intent_only(self):
        idem = uuid.uuid4().hex
        with self.subTest("create"):
            status, created = self._request(
                "POST",
                self._create_path(),
                _CREATE_BODY,
                idempotency_key=idem,
            )
            self.assertEqual(status, 201)
            self.assertIn(HOLD_PENDING, STATES)
            self.assertEqual(created["state"], HOLD_PENDING)
            self.assertEqual(created["tenant_id"], self.tenant)
            self.assertTrue(created["case_id"])
            self.assertTrue(created["action_request_id"])
            self.assertIs(created["real_gate"], False)
            self.assertIs(created["executed"], False)
            self.assertNotIn(created["state"], {"HOLD", "RELEASED", "EXECUTING"})

        case_id = created["case_id"]

        with self.subTest("get"):
            status, fetched = self._request("GET", self._case_path(case_id))
            self.assertEqual(status, 200)
            self.assertEqual(fetched["case_id"], case_id)
            self.assertEqual(fetched["state"], HOLD_PENDING)
            self.assertEqual(fetched["tenant_id"], self.tenant)
            self.assertIs(fetched["real_gate"], False)

        release_idem = uuid.uuid4().hex
        with self.subTest("release"):
            status, released = self._request(
                "POST",
                self._release_path(case_id),
                _RELEASE_BODY,
                idempotency_key=release_idem,
            )
            self.assertEqual(status, 200)
            self.assertIn(ACTION_PENDING, STATES)
            self.assertEqual(released["state"], ACTION_PENDING)
            self.assertEqual(released["case_id"], case_id)
            self.assertIs(released["executed"], False)
            self.assertIs(released["intent_only"], True)
            self.assertIs(released["real_gate"], False)
            self.assertNotEqual(released["state"], "RELEASED")

        with self.subTest("release replay"):
            status, replay = self._request(
                "POST",
                self._release_path(case_id),
                _RELEASE_BODY,
                idempotency_key=release_idem,
            )
            self.assertEqual(status, 200)
            self.assertEqual(replay["case_id"], case_id)
            self.assertEqual(replay["state"], ACTION_PENDING)
            self.assertIs(replay["executed"], False)
            self.assertIs(replay["intent_only"], True)

    def test_create_idempotency_key_replay_returns_same_case_id(self):
        idem = uuid.uuid4().hex
        status, first = self._request(
            "POST",
            self._create_path(),
            _CREATE_BODY,
            idempotency_key=idem,
        )
        self.assertEqual(status, 201)
        self.assertEqual(first["state"], HOLD_PENDING)

        # Same key, different body: stored success, not a second case.
        replay_body = dict(_CREATE_BODY)
        replay_body["subject"] = {"upn": "other@example.com"}
        status, second = self._request(
            "POST",
            self._create_path(),
            replay_body,
            idempotency_key=idem,
        )
        self.assertEqual(status, 201)
        self.assertEqual(second["case_id"], first["case_id"])
        self.assertEqual(second["action_request_id"], first["action_request_id"])
        self.assertEqual(second["state"], HOLD_PENDING)
        self.assertIs(second["real_gate"], False)
        self.assertIs(second["executed"], False)

    def test_missing_idempotency_key_is_422(self):
        with self.subTest("create"):
            status, body = self._request("POST", self._create_path(), _CREATE_BODY)
            self.assertEqual(status, 422)
            self.assertEqual(body["error"], "Idempotency-Key required")
            self.assertIs(body["real_gate"], False)

        status, created = self._request(
            "POST",
            self._create_path(),
            _CREATE_BODY,
            idempotency_key=uuid.uuid4().hex,
        )
        self.assertEqual(status, 201)
        case_id = created["case_id"]

        with self.subTest("release"):
            status, body = self._request(
                "POST",
                self._release_path(case_id),
                _RELEASE_BODY,
            )
            self.assertEqual(status, 422)
            self.assertEqual(body["error"], "Idempotency-Key required")
            self.assertIs(body["real_gate"], False)

        status, fetched = self._request("GET", self._case_path(case_id))
        self.assertEqual(status, 200)
        self.assertEqual(fetched["state"], HOLD_PENDING)

    def test_unknown_case_is_404(self):
        missing = "not-a-case"
        with self.subTest("get"):
            status, body = self._request("GET", self._case_path(missing))
            self.assertEqual(status, 404)
            self.assertEqual(body["error"], "not_found")
            self.assertIs(body["real_gate"], False)

        with self.subTest("release"):
            status, body = self._request(
                "POST",
                self._release_path(missing),
                _RELEASE_BODY,
                idempotency_key=uuid.uuid4().hex,
            )
            self.assertEqual(status, 404)
            self.assertEqual(body["error"], "not_found")
            self.assertIs(body["real_gate"], False)

    def test_observe_mode_release_conflict_is_409(self):
        body = dict(_CREATE_BODY)
        body["mode"] = "observe"
        status, created = self._request(
            "POST",
            self._create_path(),
            body,
            idempotency_key=uuid.uuid4().hex,
        )
        self.assertEqual(status, 201)
        # mode=observe stays at RECEIVED. OBSERVE is a different Platform state.
        self.assertIn(RECEIVED, STATES)
        self.assertEqual(created["state"], RECEIVED)
        self.assertEqual(created["mode"], "observe")
        self.assertIs(created["real_gate"], False)

        status, conflict = self._request(
            "POST",
            self._release_path(created["case_id"]),
            _RELEASE_BODY,
            idempotency_key=uuid.uuid4().hex,
        )
        self.assertEqual(status, 409)
        self.assertEqual(conflict["error"], "mode_observe")
        self.assertEqual(conflict["state"], RECEIVED)
        self.assertIs(conflict["real_gate"], False)

        status, fetched = self._request("GET", self._case_path(created["case_id"]))
        self.assertEqual(status, 200)
        self.assertEqual(fetched["state"], RECEIVED)
        self.assertNotEqual(fetched["state"], ACTION_PENDING)

    def test_sensor_client_id_differs_from_executor(self):
        """Entra app ids are split. Recording them does not arm real_gate."""
        lab_fixtures.assert_sensor_executor_client_ids_differ()
        self.assertNotEqual(
            lab_fixtures.SENSOR_APP_CLIENT_ID,
            lab_fixtures.EXECUTOR_APP_CLIENT_ID,
        )
        self.assertTrue(lab_fixtures.SENSOR_APP_CLIENT_ID.strip())
        self.assertTrue(lab_fixtures.EXECUTOR_APP_CLIENT_ID.strip())
        self.assertIs(lab_fixtures.REAL_GATE, False)
        self.assertIs(lab_fixtures.real_gate, False)
        self.assertIn("jsm_pending", lab_fixtures.REAL_GATE_BLOCKS)
        self.assertIn("R6_foreign_graph_must_close", lab_fixtures.REAL_GATE_BLOCKS)
        self.assertIsNone(lab_fixtures.JSM_SITE)
        self.assertIsNone(lab_fixtures.JSM_PROJECT_KEY)
        self.assertFalse(lab_fixtures.lab_ids_configured())
        status, body = self._request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertIs(body["real_gate"], False)

    @unittest.skipUnless(
        lab_fixtures.lab_ids_configured(),
        "Entra lab ids are recorded; JSM lab ids are still unset; "
        "not real_gate; skipped until lab_fixtures.py is fully filled "
        "(do not fail CI)",
    )
    def test_lab_ids_do_not_arm_real_gate(self):
        """Future Integrations hook. Must not call Entra or JSM.

        Lab marker: skipped unless ``lab_fixtures`` is fully filled,
        including JSM. Same intent as a future ``pytest.mark.lab`` —
        this repo has no pytest. Entra ids alone must not unskip it.
        """
        lab_fixtures.assert_sensor_executor_client_ids_differ()
        self.assertNotEqual(
            lab_fixtures.SENSOR_APP_CLIENT_ID,
            lab_fixtures.EXECUTOR_APP_CLIENT_ID,
        )
        self.assertIs(lab_fixtures.REAL_GATE, False)
        self.assertIs(lab_fixtures.real_gate, False)
        self.assertTrue(lab_fixtures.ENTRA_LAB_TENANT_ID.strip())
        self.assertTrue(lab_fixtures.JSM_LAB_PROJECT_KEY.strip())
        self.assertTrue(lab_fixtures.JSM_LAB_ISSUE_KEY.strip())
        status, body = self._request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertIs(body["real_gate"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
