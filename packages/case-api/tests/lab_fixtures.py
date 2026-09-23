"""Placeholders for Integrations lab fixtures.

Lab ID hooks for Integrations — TBD.

These constants stay empty until Integrations attaches Entra and JSM lab
identifiers. They are not production credentials. Filling them does not
arm ``real_gate``: the Case API observe stub never calls Entra or JSM.

Do not store secrets, certificates, or client secrets here.
"""

from __future__ import annotations

# TODO(integrations): lab directory (Entra) tenant id. Not a production tenant.
ENTRA_LAB_TENANT_ID = ""

# TODO(integrations): lab app registration client id, if a future test needs one.
# Leave empty. Do not store a secret or certificate here.
ENTRA_LAB_CLIENT_ID = ""

# TODO(integrations): lab JSM cloud / site id.
JSM_LAB_CLOUD_ID = ""

# TODO(integrations): lab JSM project or service desk key.
JSM_LAB_PROJECT_KEY = ""

# TODO(integrations): lab JSM issue key used only as correlation evidence.
JSM_LAB_ISSUE_KEY = ""


def lab_ids_configured() -> bool:
    """True only when Integrations has filled every lab id placeholder."""
    required = (
        ENTRA_LAB_TENANT_ID,
        ENTRA_LAB_CLIENT_ID,
        JSM_LAB_CLOUD_ID,
        JSM_LAB_PROJECT_KEY,
        JSM_LAB_ISSUE_KEY,
    )
    return all(bool(value.strip()) for value in required)
