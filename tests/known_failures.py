"""Quarantine list for pre-existing backend test failures.

Each entry maps a pytest node id to a defect in ``Docs/stage-5/defect-log.md``.
``tests/conftest.py`` marks these tests as *strict* xfails, so:

- CI stays green while the defect is open, and still fails on any *new*
  failure.
- When a fix makes a quarantined test pass, the run fails (XPASS strict) until
  the entry is deleted here. The list can only shrink.

Do not add entries without a matching defect-log row.
"""

KNOWN_FAILURES: dict[str, str] = {
    # D8: alert serialization fails (UUID coercion of non-string values;
    # AlertResponse expects updated_at, which alerts no longer have).
    "tests/test_endpoint_serialization_regressions.py::"
    "test_list_alerts_serializes_cleanly": "D8",
    "tests/test_response_model_serialization_regressions.py::"
    "test_alert_response_model_validate_coerces_optional_uuid"
    "_and_normalizes_datetimes": "D8",
    # D9: work-order suite targets the pre-reconciliation contract
    # (POST /v1/alerts/{id}/work-orders, alert_id link, enum CHECK
    # constraints) removed by migration 0006.
    "tests/test_work_orders.py::test_create_work_order_success": "D9",
    "tests/test_work_orders.py::test_create_duplicate_work_order_conflict": "D9",
    "tests/test_work_orders.py::test_create_work_order_alert_not_found": "D9",
    "tests/test_work_orders.py::test_update_closed_work_order_success": "D9",
    "tests/test_work_orders.py::test_update_empty_body_rejected": "D9",
    "tests/test_work_orders.py::test_update_work_order_success": "D9",
    "tests/test_work_orders.py::test_get_work_order_success": "D9",
    "tests/test_work_orders.py::test_create_invalid_priority_rejected": "D9",
    "tests/test_work_orders.py::test_list_work_orders_pagination": "D9",
    "tests/test_work_orders.py::"
    "test_detail_normalizes_persisted_enum_casing": "D9",
    "tests/test_work_orders.py::test_list_normalizes_persisted_enum_casing": "D9",
    "tests/test_work_orders.py::"
    "test_invalid_work_order_enum_is_rejected_by_database": "D9",
    "tests/test_work_orders.py::"
    "test_invalid_response_enum_returns_data_integrity_problem": "D9",
}
