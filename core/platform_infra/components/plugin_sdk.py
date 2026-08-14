"""Plugin SDK Manager — Extension discovery, lifecycle management, and event hook dispatching."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.platform_infra.models.plugin import PluginHookType, PluginManifest, PluginStatus
from utils.logger import get_logger

logger = get_logger("PluginSDKManager")


class PluginSDKManager:
    """Manages plugin manifests, state transitions, and event hook dispatches across execution stages."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginManifest] = {}
        self._hooks: Dict[PluginHookType, List[Callable[[Dict[str, Any]], None]]] = {
            h: [] for h in PluginHookType
        }

    def register_plugin(self, manifest: PluginManifest) -> None:
        """Register a plugin manifest."""
        self._plugins[manifest.plugin_id] = manifest
        logger.info(f"PluginSDKManager registered plugin '{manifest.name}' v{manifest.version} [{manifest.plugin_id}]")

    def enable_plugin(self, plugin_id: str) -> None:
        """Enable an installed plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found.")
        plugin.status = PluginStatus.ENABLED
        logger.info(f"PluginSDKManager enabled plugin '{plugin.name}'")

    def disable_plugin(self, plugin_id: str) -> None:
        """Disable an active plugin."""
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found.")
        plugin.status = PluginStatus.DISABLED
        logger.info(f"PluginSDKManager disabled plugin '{plugin.name}'")

    def register_hook(self, hook_type: PluginHookType, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for event hook."""
        self._hooks[hook_type].append(callback)
        logger.info(f"PluginSDKManager registered callback for hook '{hook_type.value}'")

    def dispatch_hook(self, hook_type: PluginHookType, event_payload: Dict[str, Any]) -> None:
        """Dispatch event hook to all registered callbacks."""
        callbacks = self._hooks.get(hook_type, [])
        for cb in callbacks:
            try:
                cb(event_payload)
            except Exception as exc:
                logger.error(f"Plugin hook dispatch exception [{hook_type.value}]: {exc}")

    def list_plugins(self) -> List[PluginManifest]:
        """List registered plugin manifests."""
        return list(self._plugins.values())
