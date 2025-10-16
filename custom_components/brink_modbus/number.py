"""BRINK HRU number platform."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, HOLDING_REGISTERS
from .coordinator import BrinkCoordinator
from .entity import BrinkEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BRINK HRU number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        # Flow levels
        BrinkFlowLevelNumber(coordinator, entry, "flow_level_0_absence", "Flow Level 0 (Absence)"),
        BrinkFlowLevelNumber(coordinator, entry, "flow_level_1_low", "Flow Level 1 (Low)"),
        BrinkFlowLevelNumber(coordinator, entry, "flow_level_2_normal", "Flow Level 2 (Normal)"),
        BrinkFlowLevelNumber(coordinator, entry, "flow_level_3_high", "Flow Level 3 (High)"),
        
        # Flow setpoint (current target)
        BrinkFlowSetpointNumber(coordinator, entry),
        
        # Imbalance settings
        BrinkImbalanceOffsetNumber(coordinator, entry, "supply_imbalance_offset", "Supply Imbalance Offset"),
        BrinkImbalanceOffsetNumber(coordinator, entry, "exhaust_imbalance_offset", "Exhaust Imbalance Offset"),
        
        # Geo heat exchanger temperatures
        BrinkGeoTemperatureNumber(coordinator, entry, "geo_min_temperature", "Geo Min Temperature"),
        BrinkGeoTemperatureNumber(coordinator, entry, "geo_max_temperature", "Geo Max Temperature"),
    ]
    
    async_add_entities(entities)

class BrinkFlowLevelNumber(BrinkEntity, NumberEntity):
    """BRINK flow level number entity."""

    def __init__(
        self,
        coordinator: BrinkCoordinator,
        entry: ConfigEntry,
        setting_key: str,
        name: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry)
        self._setting_key = setting_key
        self._config = HOLDING_REGISTERS[setting_key]
        
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{setting_key}"
        self._attr_icon = "mdi:fan"
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        self._attr_mode = NumberMode.BOX
        
        # Set limits from config
        self._attr_native_min_value = self._config.get("min", 0)
        self._attr_native_max_value = self._config.get("max", 325)
        self._attr_native_step = 5

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get(self._setting_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        success = await self.coordinator.async_write_register(
            self._config["address"],
            int(value)
        )
        
        if not success:
            _LOGGER.error("Failed to set %s to %s", self._setting_key, value)

class BrinkFlowSetpointNumber(BrinkEntity, NumberEntity):
    """BRINK flow setpoint number entity."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry)
        self._config = HOLDING_REGISTERS["flow_setpoint"]
        
        self._attr_name = "Flow Setpoint"
        self._attr_unique_id = f"{entry.entry_id}_flow_setpoint"
        self._attr_icon = "mdi:fan-speed-3"
        self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        self._attr_mode = NumberMode.SLIDER
        
        # Set limits from config
        self._attr_native_min_value = self._config.get("min", 50)
        self._attr_native_max_value = self._config.get("max", 325)
        self._attr_native_step = 5

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get("flow_setpoint")

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        # Check if modbus control is in Flow Control mode (2)
        current_control_mode = self.coordinator.data.get("modbus_control") if self.coordinator.data else None
        
        if current_control_mode != 2:
            _LOGGER.info(
                "Flow setpoint requires Flow Control mode (2), currently: %s. Enabling Flow Control...",
                current_control_mode
            )
            # Enable Flow Control mode first
            control_success = await self.coordinator.async_write_register(
                HOLDING_REGISTERS["modbus_control"]["address"],
                2  # Flow Control mode
            )
            if not control_success:
                _LOGGER.error("Failed to enable Flow Control mode")
                return
            
            # Wait a moment for mode change
            import asyncio
            await asyncio.sleep(0.5)
        
        success = await self.coordinator.async_write_register(
            self._config["address"],
            int(value)
        )
        
        if not success:
            _LOGGER.error("Failed to set flow setpoint to %s", value)
        else:
            _LOGGER.info("Successfully set flow setpoint to %s m³/h", value)

class BrinkImbalanceOffsetNumber(BrinkEntity, NumberEntity):
    """BRINK imbalance offset number entity."""

    def __init__(
        self,
        coordinator: BrinkCoordinator,
        entry: ConfigEntry,
        setting_key: str,
        name: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry)
        self._setting_key = setting_key
        self._config = HOLDING_REGISTERS[setting_key]
        
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{setting_key}"
        self._attr_icon = "mdi:scale-balance"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.SLIDER
        
        # Set limits from config
        self._attr_native_min_value = self._config.get("min", -15)
        self._attr_native_max_value = self._config.get("max", 15)
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get(self._setting_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        success = await self.coordinator.async_write_register(
            self._config["address"],
            int(value)
        )
        
        if not success:
            _LOGGER.error("Failed to set %s to %s", self._setting_key, value)

class BrinkGeoTemperatureNumber(BrinkEntity, NumberEntity):
    """BRINK geo heat exchanger temperature number entity."""

    def __init__(
        self,
        coordinator: BrinkCoordinator,
        entry: ConfigEntry,
        setting_key: str,
        name: str,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, entry)
        self._setting_key = setting_key
        self._config = HOLDING_REGISTERS[setting_key]
        
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{setting_key}"
        self._attr_icon = "mdi:thermometer"
        self._attr_native_unit_of_measurement = "°C"
        self._attr_mode = NumberMode.BOX
        
        # Set limits from config
        self._attr_native_min_value = self._config.get("min", 0)
        self._attr_native_max_value = self._config.get("max", 400)
        self._attr_native_step = 1

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get(self._setting_key)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        success = await self.coordinator.async_write_register(
            self._config["address"],
            int(value)
        )
        
        if not success:
            _LOGGER.error("Failed to set %s to %s", self._setting_key, value)
