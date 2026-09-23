"""In-memory case store for the observe stub. Stdlib only."""

from __future__ import annotations

from case_api.case_sm import Case


class CaseStore:
    def __init__(self) -> None:
        self._by_case: dict[str, Case] = {}
        self._by_action: dict[str, str] = {}

    def put(self, case: Case) -> None:
        self._by_case[case.case_id] = case
        self._by_action[case.action_request_id] = case.case_id

    def get(self, case_id: str) -> Case | None:
        case = self._by_case.get(case_id)
        if case is not None:
            return case
        mapped = self._by_action.get(case_id)
        if mapped is None:
            return None
        return self._by_case.get(mapped)

    def get_public(self, action_request_id: str) -> dict | None:
        case = self.get(action_request_id)
        if case is None:
            return None
        return case.to_public()
