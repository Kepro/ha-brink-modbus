"""Data update coordinator for BRINK HRU."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ConnectionException, ModbusException

from .const import (
    DOMAIN,
    SCAN_INTERVAL_FAST,
    DEFAULT_SLAVE_ID,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    INPUT_REGISTERS,
    HOLDING_REGISTERS,
)

_LOGGER = logging.getLogger(__name__)

class BrinkCoordinator(DataUpdateCoordinator):
    """BRINK HRU data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.hass = hass
        
        # Get configuration
        self.port = entry.data[CONF_PORT]
        self.slave_id = int(entry.data.get("slave_id", DEFAULT_SLAVE_ID))
        self.baudrate = int(entry.data.get("baudrate", DEFAULT_BAUDRATE))
        
        _LOGGER.info(
            "Initializing BRINK coordinator with port=%s, slave_id=%s, baudrate=%s",
            self.port, self.slave_id, self.baudrate
        )
        
        # Initialize async modbus client
        # AsyncModbusSerialClient defaults to FramerType.RTU
        # NOTE: slave_id must be passed as parameter in each read/write call!
        self.client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=DEFAULT_BYTESIZE,
            parity=DEFAULT_PARITY,
            stopbits=DEFAULT_STOPBITS,
            timeout=5,
            retries=3,
            # framer=FramerType.RTU is default, no need to specify
        )
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_FAST),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from BRINK HRU."""
        try:
            # Connect if not connected (native async)
            if not self.client.connected:
                await self.client.connect()
                
            data = {}
            
            # Read ALL input registers (complete device data)
            for sensor_name, config in INPUT_REGISTERS.items():
                try:
                    # Native async read - CRITICAL: device_id parameter required (pymodbus 3.10.0+)!
                    result = await self.client.read_input_registers(
                        config["address"], count=1, device_id=self.slave_id
                    )
                    
                    if result.isError():
                        _LOGGER.warning(
                            "Failed to read register %s (address %d): %s",
                            sensor_name, config["address"], result
                        )
                        continue
                        
                    # Apply scaling if configured
                    value = result.registers[0]
                    if "scale" in config:
                        value = value * config["scale"]
                        
                    data[sensor_name] = value
                    
                except Exception as err:
                    _LOGGER.warning(
                        "Error reading register %s: %s", sensor_name, err
                    )
                    
            # Read holding registers for all control entities (select + number entities)
            setting_registers = {
                k: v for k, v in HOLDING_REGISTERS.items()
                if k in [
                    # Select entities
                    "bypass_mode_setting", "power_switch_position", "modbus_control",
                    # Number entities
                    "flow_level_0_absence", "flow_level_1_low", "flow_level_2_normal", "flow_level_3_high",
                    "supply_imbalance_offset", "exhaust_imbalance_offset",
                    "geo_min_temperature", "geo_max_temperature",
                    # Sensor entity
                    "flow_setpoint"
                ]
            }
            
            for sensor_name, config in setting_registers.items():
                try:
                    # Native async read - CRITICAL: device_id parameter required (pymodbus 3.10.0+)!
                    result = await self.client.read_holding_registers(
                        config["address"], count=1, device_id=self.slave_id
                    )
                    
                    if result.isError():
                        _LOGGER.warning(
                            "Failed to read holding register %s (address %d): %s",
                            sensor_name, config["address"], result
                        )
                        continue
                        
                    value = result.registers[0]
                    data[sensor_name] = value
                    
                    # Debug logging for power_switch_position
                    if sensor_name == "power_switch_position":
                        _LOGGER.info(
                            "Read power_switch_position: raw_value=%s (address 8001)",
                            value
                        )
                    
                except Exception as err:
                    _LOGGER.warning(
                        "Error reading holding register %s: %s", sensor_name, err
                    )
            
            return data
            
        except ConnectionException as err:
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err
        except ModbusException as err:
            _LOGGER.error("Modbus error: %s", err)
            raise UpdateFailed(f"Modbus error: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
    
    async def async_write_register(self, address: int, value: int) -> bool:
        """Write to holding register."""
        try:
            if not self.client.connected:
                await self.client.connect()
                
            # Native async write - CRITICAL: device_id parameter required (pymodbus 3.10.0+)!
            result = await self.client.write_register(address, value=value, device_id=self.slave_id)
            
            if result.isError():
                _LOGGER.error(
                    "Failed to write register %d with value %d: %s",
                    address, value, result
                )
                return False
                
            # Trigger immediate update after write
            await self.async_request_refresh()
            return True
            
        except Exception as err:
            _LOGGER.error("Error writing register %d: %s", address, err)
            return False
    
    async def async_read_all_registers(self) -> dict[str, Any]:
        """Read all registers for diagnostics."""
        try:
            if not self.client.connected:
                await self.client.connect()
                
            data = {}
            
            # Read all input registers
            for sensor_name, config in INPUT_REGISTERS.items():
                try:
                    # Native async read - CRITICAL: device_id parameter required (pymodbus 3.10.0+)!
                    result = await self.client.read_input_registers(
                        config["address"], count=1, device_id=self.slave_id
                    )
                    
                    if not result.isError():
                        value = result.registers[0]
                        if "scale" in config:
                            value = value * config["scale"]
                        data[f"input_{sensor_name}"] = value
                        
                except Exception as err:
                    _LOGGER.debug("Error reading input register %s: %s", sensor_name, err)
            
            # Read all holding registers  
            for sensor_name, config in HOLDING_REGISTERS.items():
                try:
                    # Native async read - CRITICAL: device_id parameter required (pymodbus 3.10.0+)!
                    result = await self.client.read_holding_registers(
                        config["address"], count=1, device_id=self.slave_id
                    )
                    
                    if not result.isError():
                        data[f"holding_{sensor_name}"] = result.registers[0]
                        
                except Exception as err:
                    _LOGGER.debug("Error reading holding register %s: %s", sensor_name, err)
                    
            return data
            
        except Exception as err:
            _LOGGER.error("Error reading all registers: %s", err)
            return {}
    
    async def disconnect(self) -> None:
        """Disconnect from modbus (async)."""
        try:
            if self.client and hasattr(self.client, 'close'):
                import asyncio
                import inspect
                # Check if close is a coroutine function
                if inspect.iscoroutinefunction(self.client.close):
                    await self.client.close()
                else:
                    # Call synchronous close
                    self.client.close()
                _LOGGER.debug("Closed Modbus connection for port %s", self.port)
        except Exception as err:
            _LOGGER.warning("Error closing Modbus connection: %s", err)
