"""Entra lab identifiers for the Case API observe stub.

IDs only. This module does not store client secrets, certificates, or tokens.

Entra directory ids are filled from the Integrations / New Bot handoff.
``lab_ids_configured()`` treats the sensor and executor client ids as the
Entra identity fields. The legacy ``ENTRA_LAB_CLIENT_ID`` stays blank and
is not required. JSM site and project are still unknown, so those hooks
stay unset.
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
# app registration. lab_ids_configured() does not read this field.
# Use SENSOR_APP_CLIENT_ID and EXECUTOR_APP_CLIENT_ID.
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


# String fields lab_ids_configured() requires. Entra identity is the tenant
# plus the two app client ids. The legacy blank ENTRA_LAB_CLIENT_ID is not
# in this list.
LAB_IDS_REQUIRED = (
    "ENTRA_LAB_TENANT_ID",
    "SENSOR_APP_CLIENT_ID",
    "EXECUTOR_APP_CLIENT_ID",
    "JSM_LAB_CLOUD_ID",
    "JSM_LAB_PROJECT_KEY",
    "JSM_LAB_ISSUE_KEY",
)


def lab_ids_configured() -> bool:
    """True only when Entra identity and the JSM lab ids are filled.

    Entra identity is the tenant id plus ``SENSOR_APP_CLIENT_ID`` and
    ``EXECUTOR_APP_CLIENT_ID``. The legacy blank ``ENTRA_LAB_CLIENT_ID``
    is not a configured signal, so a later JSM handoff can unskip the lab
    case without collapsing the two app registrations. JSM site, project,
    webhook, and transition flags still gate this check. It does not arm
    ``real_gate``.
    """
    if JSM_SITE is None or JSM_PROJECT_KEY is None:
        return False
    if not WEBHOOK_REGISTERED or not TRANSITION_IDS_FILLED:
        return False
    required = tuple(globals()[name] for name in LAB_IDS_REQUIRED)
    return all(isinstance(value, str) and bool(value.strip()) for value in required)


assert_sensor_executor_client_ids_differ()
