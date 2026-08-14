"""Unit test for PluginSDKManager."""

import pytest

from core.platform_infra.components.plugin_sdk import PluginSDKManager
from core.platform_infra.models.plugin import PluginHookType, PluginManifest, PluginStatus


def test_plugin_sdk_lifecycle_and_hooks():
    sdk = PluginSDKManager()
    manifest = PluginManifest(plugin_id="plugin_analytics", name="Analytics Extension")

    sdk.register_plugin(manifest)
    assert len(sdk.list_plugins()) == 1

    sdk.enable_plugin("plugin_analytics")
    assert manifest.status == PluginStatus.ENABLED

    hook_called = []
    sdk.register_hook(PluginHookType.POST_EXECUTION, lambda payload: hook_called.append(payload))
    sdk.dispatch_hook(PluginHookType.POST_EXECUTION, {"event": "task_completed"})

    assert len(hook_called) == 1
    assert hook_called[0]["event"] == "task_completed"
