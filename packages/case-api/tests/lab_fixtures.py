"""Entra lab identifiers for the Case API observe stub.

IDs only. This module does not store client secrets, certificates, or tokens.

Entra directory ids are filled from the Integrations / New Bot handoff.
JSM site and project are still unknown, so those hooks stay unset.
Filling the Entra ids does not arm ``real_gate``: this package never calls
Entra or JSM. ``REAL_GATE`` / ``real_gate`` stay false until the JSM lab
and the R6 foreign Graph close (``REAL_GATE_BLOCKS``).
"""

from __future__ import annotations

# Case API tenant slug for this lab. Not a secret.
LAB_SLUG = "yossefdaargmail"
CASE_TENANT_ID = LAB_SLUG

# Lab directory (Entra) tenant id. Not a production tenant.
ENTRA_TENANT_ID = "20404583-0498-43da-b716-2f320464fbae"
# Name kept from the PR #2 observe-stub hook.
ENTRA_LAB_TENANT_ID = ENTRA_TENANT_ID

# Read sensor and write executor are separate app registrations.
# Public client ids only — do not add a client secret here.
SENSOR_APP_CLIENT_ID = "90162120-9f34-41b8-8095-771e6b88ea28"
EXECUTOR_APP_CLIENT_ID = "3d98bda1-dd2d-4dae-8934-f92ce22182c3"

# Legacy single-client placeholder. Left blank: there is no one shared
# app registration. Use SENSOR_APP_CLIENT_ID and EXECUTOR_APP_CLIENT_ID.
ENTRA_LAB_CLIENT_ID = ""

# JSM lab is not handed off. Do not invent site, project, or issue ids.
JSM_SITE = None
JSM_PROJECT_KEY = None
WEBHOOK_REGISTERED = False
TRANSITION_IDS_FILLED = False

# String hooks from the PR #2 stub. Empty while JSM_SITE / JSM_PROJECT_KEY
# are None. lab_ids_configured() stays false, so the lab case stays skipped.
JSM_LAB_CLOUD_ID = ""
JSM_LAB_PROJECT_KEY = ""
JSM_LAB_ISSUE_KEY = ""

REAL_GATE = False
real_gate = REAL_GATE

# Blocks that keep the gate disarmed. Remove an entry only when that close
# is actually done; do not set REAL_GATE true while any block remains.
REAL_GATE_BLOCKS = (
    "jsm_pending",
    "R6_foreign_graph_must_close",
)


def assert_sensor_executor_client_ids_differ() -> None:
    """Sensor and executor app registrations must not share a client id."""
    if SENSOR_APP_CLIENT_ID == EXECUTOR_APP_CLIENT_ID:
        raise AssertionError(
            "sensor client id must differ from executor client id"
        )
    if REAL_GATE or real_gate:
        raise AssertionError(
            "real_gate must stay false until JSM lab and R6 foreign Graph close"
        )


def lab_ids_configured() -> bool:
    """True only when every lab id placeholder, including JSM, is filled.

    Entra tenant and app client ids are not enough. JSM cloud, project, and
    issue key are still empty, and ``real_gate`` is not armed by this check.
    """
    if JSM_SITE is None or JSM_PROJECT_KEY is None:
        return False
    if not WEBHOOK_REGISTERED or not TRANSITION_IDS_FILLED:
        return False
    required = (
        ENTRA_LAB_TENANT_ID,
        ENTRA_LAB_CLIENT_ID,
        JSM_LAB_CLOUD_ID,
        JSM_LAB_PROJECT_KEY,
        JSM_LAB_ISSUE_KEY,
    )
    return all(isinstance(value, str) and bool(value.strip()) for value in required)


assert_sensor_executor_client_ids_differ()
