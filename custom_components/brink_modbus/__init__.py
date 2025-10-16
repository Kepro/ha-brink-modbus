"""BRINK Heat Recovery Unit integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    PLATFORMS,
    SCAN_INTERVAL_FAST,
)
from .coordinator import BrinkCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BRINK HRU from a config entry."""
    _LOGGER.info("Setting up BRINK HRU integration")
    
    # Create coordinator
    coordinator = BrinkCoordinator(hass, entry)
    
    # Test connection
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to connect to BRINK HRU: %s", err)
        raise ConfigEntryNotReady from err
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Setup services (only once)
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading BRINK HRU integration")
    
    # Get coordinator before unloading
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Disconnect async modbus client to release serial port
        if coordinator:
            await coordinator.disconnect()
            _LOGGER.debug("Disconnected Modbus client for port %s", coordinator.port)
        
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unload services if this is the last device
        if not hass.data[DOMAIN]:
            await async_unload_services(hass)
        
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
