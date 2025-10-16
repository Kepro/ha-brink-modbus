"""BRINK HRU services."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    BYPASS_MODE_MAP,
    POWER_SWITCH_MAP,
    HOLDING_REGISTERS,
)
from .coordinator import BrinkCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_BYPASS_MODE = "set_bypass_mode"
SERVICE_SET_FLOW_SPEED = "set_flow_speed"
SERVICE_SET_POWER_MODE = "set_power_mode"
SERVICE_RESET_DEVICE = "reset_device"
SERVICE_READ_ALL_REGISTERS = "read_all_registers"

SET_BYPASS_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("mode"): vol.In(["automatic", "closed", "open"]),
    }
)

SET_FLOW_SPEED_SCHEMA = vol.Schema(
    {
        vol.Required("speed"): vol.All(int, vol.Range(min=50, max=325)),
    }
)

SET_POWER_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("mode"): vol.In(["absence", "low", "normal", "high"]),
    }
)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up BRINK HRU services."""

    async def async_set_bypass_mode(call: ServiceCall) -> None:
        """Set bypass mode service."""
        mode = call.data["mode"]
        
        # Find numeric value for mode
        mode_value = None
        for value, text in BYPASS_MODE_MAP.items():
            if text.lower() == mode:
                mode_value = value
                break
                
        if mode_value is None:
            raise ServiceValidationError(f"Invalid bypass mode: {mode}")
        
        # Find coordinator from service call target
        entry_id = call.data.get("config_entry_id")
        if not entry_id:
            # Get first available coordinator if no target specified
            coordinators = [
                coordinator for coordinator in hass.data[DOMAIN].values()
                if isinstance(coordinator, BrinkCoordinator)
            ]
            if not coordinators:
                raise ServiceValidationError("No BRINK HRU devices found")
            coordinator = coordinators[0]
        else:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if not coordinator:
                raise ServiceValidationError(f"BRINK HRU device not found: {entry_id}")
        
        success = await coordinator.async_write_register(
            HOLDING_REGISTERS["bypass_mode_setting"]["address"],
            mode_value
        )
        
        if not success:
            raise ServiceValidationError(f"Failed to set bypass mode to {mode}")
            
        _LOGGER.info("BRINK bypass mode set to %s", mode)

    async def async_set_flow_speed(call: ServiceCall) -> None:
        """Set flow speed service."""
        speed = call.data["speed"]
        
        # Find coordinator
        entry_id = call.data.get("config_entry_id")
        if not entry_id:
            coordinators = [
                coordinator for coordinator in hass.data[DOMAIN].values()
                if isinstance(coordinator, BrinkCoordinator)
            ]
            if not coordinators:
                raise ServiceValidationError("No BRINK HRU devices found")
            coordinator = coordinators[0]
        else:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if not coordinator:
                raise ServiceValidationError(f"BRINK HRU device not found: {entry_id}")
        
        success = await coordinator.async_write_register(
            HOLDING_REGISTERS["flow_setpoint"]["address"],
            speed
        )
        
        if not success:
            raise ServiceValidationError(f"Failed to set flow speed to {speed}")
            
        _LOGGER.info("BRINK flow speed set to %s m³/h", speed)

    async def async_set_power_mode(call: ServiceCall) -> None:
        """Set power mode service."""
        mode = call.data["mode"]
        
        # Find numeric value for mode
        mode_value = None
        for value, text in POWER_SWITCH_MAP.items():
            if text.lower() == mode:
                mode_value = value
                break
                
        if mode_value is None:
            raise ServiceValidationError(f"Invalid power mode: {mode}")
        
        # Find coordinator
        entry_id = call.data.get("config_entry_id")
        if not entry_id:
            coordinators = [
                coordinator for coordinator in hass.data[DOMAIN].values()
                if isinstance(coordinator, BrinkCoordinator)
            ]
            if not coordinators:
                raise ServiceValidationError("No BRINK HRU devices found")
            coordinator = coordinators[0]
        else:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if not coordinator:
                raise ServiceValidationError(f"BRINK HRU device not found: {entry_id}")
        
        success = await coordinator.async_write_register(
            HOLDING_REGISTERS["power_switch_position"]["address"],
            mode_value
        )
        
        if not success:
            raise ServiceValidationError(f"Failed to set power mode to {mode}")
            
        _LOGGER.info("BRINK power mode set to %s", mode)

    async def async_reset_device(call: ServiceCall) -> None:
        """Reset device service."""
        # Find coordinator
        entry_id = call.data.get("config_entry_id")
        if not entry_id:
            coordinators = [
                coordinator for coordinator in hass.data[DOMAIN].values()
                if isinstance(coordinator, BrinkCoordinator)
            ]
            if not coordinators:
                raise ServiceValidationError("No BRINK HRU devices found")
            coordinator = coordinators[0]
        else:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if not coordinator:
                raise ServiceValidationError(f"BRINK HRU device not found: {entry_id}")
        
        _LOGGER.warning("Triggering BRINK device reset")
        
        success = await coordinator.async_write_register(
            HOLDING_REGISTERS["device_reset"]["address"],
            1
        )
        
        if not success:
            raise ServiceValidationError("Failed to trigger device reset")
            
        _LOGGER.info("BRINK device reset triggered successfully")

    async def async_read_all_registers(call: ServiceCall) -> None:
        """Read all registers for diagnostics."""
        # Find coordinator
        entry_id = call.data.get("config_entry_id")
        if not entry_id:
            coordinators = [
                coordinator for coordinator in hass.data[DOMAIN].values()
                if isinstance(coordinator, BrinkCoordinator)
            ]
            if not coordinators:
                raise ServiceValidationError("No BRINK HRU devices found")
            coordinator = coordinators[0]
        else:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if not coordinator:
                raise ServiceValidationError(f"BRINK HRU device not found: {entry_id}")
        
        data = await coordinator.async_read_all_registers()
        
        # Fire event with register data
        hass.bus.async_fire(
            f"{DOMAIN}_diagnostics",
            {
                "device_id": entry_id,
                "registers": data,
            }
        )
        
        _LOGGER.info("BRINK register diagnostics data fired as event")

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_SET_BYPASS_MODE, async_set_bypass_mode, schema=SET_BYPASS_MODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_FLOW_SPEED, async_set_flow_speed, schema=SET_FLOW_SPEED_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_POWER_MODE, async_set_power_mode, schema=SET_POWER_MODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_DEVICE, async_reset_device
    )
    hass.services.async_register(
        DOMAIN, SERVICE_READ_ALL_REGISTERS, async_read_all_registers
    )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload BRINK HRU services."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_BYPASS_MODE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_FLOW_SPEED)
    hass.services.async_remove(DOMAIN, SERVICE_SET_POWER_MODE)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_DEVICE)
    hass.services.async_remove(DOMAIN, SERVICE_READ_ALL_REGISTERS)
