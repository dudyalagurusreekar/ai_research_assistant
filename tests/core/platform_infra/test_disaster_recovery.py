"""Unit test for DisasterRecoveryManager."""

import pytest

from core.platform_infra.components.disaster_recovery import DisasterRecoveryManager


def test_disaster_recovery_snapshot_and_restore(tmp_path):
    dr = DisasterRecoveryManager(backup_dir=str(tmp_path))

    state_data = {"graph_nodes": 100, "active_workflows": 2}
    snapshot = dr.create_snapshot(tenant_id="tenant_beta", state_data=state_data)

    assert snapshot.snapshot_id is not None
    assert snapshot.size_bytes > 0

    restored = dr.restore_snapshot(snapshot.snapshot_id)
    assert restored["graph_nodes"] == 100
    assert restored["active_workflows"] == 2
