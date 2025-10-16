"""BRINK HRU sensor platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    REVOLUTIONS_PER_MINUTE,
    CONCENTRATION_PARTS_PER_MILLION,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    INPUT_REGISTERS,
    HOLDING_REGISTERS,
    BYPASS_STATE_MAP,
    FILTER_STATE_MAP,
    PREHEATER_STATE_MAP,
    BYPASS_MODE_MAP,
    POWER_SWITCH_MAP,
    SENSOR_ICONS,
)
from .coordinator import BrinkCoordinator
from .entity import BrinkEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BRINK HRU sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Sensors that have dedicated text versions (skip numeric entity)
    text_only_sensors = ["bypass_state", "filter_state", "preheater_state"]
    
    # Add input register sensors
    for sensor_key, config in INPUT_REGISTERS.items():
        # Skip numeric entities if text version exists (data still loaded by coordinator)
        if sensor_key in text_only_sensors:
            continue
        entities.append(BrinkSensor(coordinator, entry, sensor_key, config, "input"))
    
    # Add selected holding register sensors (read-only view)
    # Note: bypass_mode_setting and power_switch_position have text versions, so skip numeric
    readonly_holdings = [
        "flow_setpoint"  # Only numeric sensor without text version
    ]
    for sensor_key in readonly_holdings:
        if sensor_key in HOLDING_REGISTERS:
            config = HOLDING_REGISTERS[sensor_key]
            entities.append(BrinkSensor(coordinator, entry, sensor_key, config, "holding"))
    
    # Add text state sensors (calculated efficiency in templates.yaml for better accuracy)
    entities.extend([
        BrinkBypassStateTextSensor(coordinator, entry),
        BrinkFilterStateTextSensor(coordinator, entry),
        BrinkPreheaterStateTextSensor(coordinator, entry),
        BrinkBypassModeTextSensor(coordinator, entry),
        BrinkPowerSwitchTextSensor(coordinator, entry),
    ])
    
    async_add_entities(entities)

class BrinkSensor(BrinkEntity, SensorEntity):
    """Base BRINK sensor."""

    def __init__(
        self,
        coordinator: BrinkCoordinator,
        entry: ConfigEntry,
        sensor_key: str,
        config: dict[str, Any],
        register_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._sensor_key = sensor_key
        self._config = config
        self._register_type = register_type
        
        # Set basic attributes with has_entity_name pattern
        self._attr_name = sensor_key.replace('_', ' ').title()
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"
        
        # Set units and device class
        if config.get("unit"):
            if config["unit"] == "°C":
                self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
                self._attr_device_class = SensorDeviceClass.TEMPERATURE
            elif config["unit"] == "Pa":
                self._attr_native_unit_of_measurement = UnitOfPressure.PA
                self._attr_device_class = SensorDeviceClass.PRESSURE
            elif config["unit"] == "ppm":
                self._attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
                self._attr_device_class = SensorDeviceClass.CO2
            elif config["unit"] == "RPM":
                self._attr_native_unit_of_measurement = REVOLUTIONS_PER_MINUTE
            elif config["unit"] == "m³/h":
                self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
            elif config["unit"] == "h":
                self._attr_native_unit_of_measurement = UnitOfTime.HOURS
            elif config["unit"] == "%":
                self._attr_native_unit_of_measurement = PERCENTAGE
            else:
                self._attr_native_unit_of_measurement = config["unit"]
        
        # Set device class from config
        if config.get("device_class") and not hasattr(self, "_attr_device_class"):
            if config["device_class"] == "temperature":
                self._attr_device_class = SensorDeviceClass.TEMPERATURE
            elif config["device_class"] == "pressure":
                self._attr_device_class = SensorDeviceClass.PRESSURE
            elif config["device_class"] == "carbon_dioxide":
                self._attr_device_class = SensorDeviceClass.CO2
            elif config["device_class"] == "humidity":
                self._attr_device_class = SensorDeviceClass.HUMIDITY
        
        # Set state class for numeric sensors
        if hasattr(self, "_attr_native_unit_of_measurement") and self._attr_native_unit_of_measurement:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Set icon
        self._attr_icon = self._get_icon()
        
        # Add software version to device info
        if coordinator.data:
            self._attr_device_info["sw_version"] = coordinator.data.get("software_version")

    def _get_icon(self) -> str:
        """Get icon for sensor."""
        if "temperature" in self._sensor_key:
            return SENSOR_ICONS["temperature"]
        elif "pressure" in self._sensor_key:
            return SENSOR_ICONS["pressure"]
        elif "volume" in self._sensor_key or "flow" in self._sensor_key:
            return SENSOR_ICONS["volume"]
        elif "rpm" in self._sensor_key or "fan" in self._sensor_key:
            return SENSOR_ICONS["rpm"]
        elif "co2" in self._sensor_key:
            return SENSOR_ICONS["co2"]
        elif "filter" in self._sensor_key:
            return SENSOR_ICONS["filter"]
        elif "bypass" in self._sensor_key:
            return SENSOR_ICONS["bypass"]
        elif "preheater" in self._sensor_key:
            return SENSOR_ICONS["preheater"]
        else:
            return "mdi:gauge"

    @property
    def native_value(self) -> float | int | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get(self._sensor_key)

class BrinkBypassStateTextSensor(BrinkEntity, SensorEntity):
    """Bypass state text sensor."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._attr_name = "Bypass State"
        self._attr_unique_id = f"{entry.entry_id}_bypass_state"
        self._attr_icon = "mdi:valve"

    @property
    def native_value(self) -> str | None:
        """Return bypass state as text."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("bypass_state")
        if state is None:
            return None
            
        return BYPASS_STATE_MAP.get(state, "Unknown")

class BrinkFilterStateTextSensor(BrinkEntity, SensorEntity):
    """Filter state text sensor."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._attr_name = "Filter State"
        self._attr_unique_id = f"{entry.entry_id}_filter_state"
        self._attr_icon = "mdi:air-filter"

    @property
    def native_value(self) -> str | None:
        """Return filter state as text."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("filter_state")
        if state is None:
            return None
            
        return FILTER_STATE_MAP.get(state, "Unknown")

class BrinkPreheaterStateTextSensor(BrinkEntity, SensorEntity):
    """Preheater state text sensor."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._attr_name = "Preheater State"
        self._attr_unique_id = f"{entry.entry_id}_preheater_state"
        self._attr_icon = "mdi:heating-coil"

    @property
    def native_value(self) -> str | None:
        """Return preheater state as text."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("preheater_state")
        if state is None:
            return None
            
        return PREHEATER_STATE_MAP.get(state, "Unknown")

class BrinkBypassModeTextSensor(BrinkEntity, SensorEntity):
    """Bypass mode text sensor."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._attr_name = "Bypass Mode"
        self._attr_unique_id = f"{entry.entry_id}_bypass_mode_setting"
        self._attr_icon = "mdi:valve-closed"

    @property
    def native_value(self) -> str | None:
        """Return bypass mode as text."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("bypass_mode_setting")
        if state is None:
            return None
            
        return BYPASS_MODE_MAP.get(state, "Unknown")

class BrinkPowerSwitchTextSensor(BrinkEntity, SensorEntity):
    """Power switch position text sensor."""

    def __init__(self, coordinator: BrinkCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        
        self._attr_name = "Power Switch Position"
        self._attr_unique_id = f"{entry.entry_id}_power_switch_position"
        self._attr_icon = "mdi:toggle-switch"

    @property
    def native_value(self) -> str | None:
        """Return power switch position as text."""
        if self.coordinator.data is None:
            return None
            
        state = self.coordinator.data.get("power_switch_position")
        if state is None:
            return None
            
        return POWER_SWITCH_MAP.get(state, "Unknown")
