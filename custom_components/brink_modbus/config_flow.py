"""Config flow for BRINK Heat Recovery Unit integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ConnectionException, ModbusException

from .const import (
    DOMAIN,
    DEFAULT_SLAVE_ID,
    DEFAULT_BAUDRATE,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, default="/dev/ttyUSB0"): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required("slave_id", default=DEFAULT_SLAVE_ID): NumberSelector(
            NumberSelectorConfig(min=1, max=247, mode=NumberSelectorMode.BOX)
        ),
        vol.Required("baudrate", default=str(DEFAULT_BAUDRATE)): SelectSelector(
            SelectSelectorConfig(
                options=["9600", "19200", "38400", "57600", "115200"],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required("model", default="flair_325_plus"): SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": k, "label": v} for k, v in SUPPORTED_MODELS.items()
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    port = data[CONF_PORT]
    slave_id = int(data["slave_id"])
    baudrate = int(data["baudrate"])
    
    _LOGGER.info(
        "Validating connection to BRINK HRU: port=%s, slave_id=%s, baudrate=%s",
        port, slave_id, baudrate
    )
    
    # Check if port exists (for Unix-like systems)
    import os
    if not os.path.exists(port):
        error_msg = f"Serial port does not exist: {port}"
        _LOGGER.error(error_msg)
        raise CannotConnect(error_msg)
    
    # Initialize async client
    # AsyncModbusSerialClient defaults to FramerType.RTU
    # NOTE: slave_id must be passed as parameter in each read/write call!
    client = AsyncModbusSerialClient(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        parity="E",
        stopbits=1,
        timeout=5,
        retries=3,
        # framer=FramerType.RTU is default, no need to specify
    )
    
    _LOGGER.info(
        "Modbus RTU client configuration: port=%s, baudrate=%s, parity=E, stopbits=1, slave_id=%s, timeout=5s, retries=3, framer=RTU",
        port, baudrate, slave_id
    )
    
    try:
        # Try to connect (native async, no executor needed)
        _LOGGER.info("Attempting to connect to serial port %s...", port)
        await client.connect()
        
        if not client.connected:
            error_msg = f"Failed to connect to serial port {port}"
            _LOGGER.error(error_msg)
            raise CannotConnect(error_msg)
        
        _LOGGER.info("Serial port connected successfully!")
        _LOGGER.info("Reading device type register (address 4004, slave_id=%s)...", slave_id)
        
        # Try to read device type register
        # AsyncModbusSerialClient is native async - no executor needed
        # CRITICAL: device_id parameter must be passed in each call (pymodbus 3.10.0+)!
        try:
            result = await client.read_input_registers(4004, count=1, device_id=slave_id)
        except Exception as read_err:
            error_msg = (
                f"Modbus read exception (slave_id={slave_id}, address=4004): {type(read_err).__name__}: {read_err}\n\n"
                f"Possible causes:\n"
                f"1. Slave ID mismatch - device may be configured with different ID\n"
                f"2. Wall controller still connected - MUST be disconnected for Modbus\n"
                f"3. RS485 wiring issue - check A/B connections\n"
                f"4. Wrong baudrate - verify device is set to {baudrate}"
            )
            _LOGGER.error(error_msg)
            raise CannotConnect(error_msg) from read_err
        
        if result.isError():
            error_msg = (
                f"Modbus error response (slave_id={slave_id}, address=4004): {result}\n\n"
                f"Common issues:\n"
                f"• Slave ID {slave_id} not responding - try checking device Modbus settings\n"
                f"• Wall controller interference - ensure it is UNPLUGGED\n"
                f"• Device not in Modbus mode - may need activation\n"
                f"• Timeout - device may be slow to respond"
            )
            _LOGGER.error(error_msg)
            raise CannotConnect(error_msg)
        
        device_type = result.registers[0]
        _LOGGER.info("✓ Device type register read successfully: %s (0x%04X)", device_type, device_type)
            
        # Try to read serial number
        _LOGGER.info("Reading serial number register (address 4010)...")
        result = await client.read_input_registers(4010, count=1, device_id=slave_id)
        
        serial_number = result.registers[0] if not result.isError() else "Unknown"
        if not result.isError():
            _LOGGER.info("✓ Serial number: %s", serial_number)
        else:
            _LOGGER.warning("Could not read serial number: %s", result)
        
        device_info = {
            "title": f"BRINK {SUPPORTED_MODELS[data['model']]}",
            "serial_number": serial_number,
        }
        
        _LOGGER.info("=" * 60)
        _LOGGER.info("✓✓✓ Successfully validated connection to BRINK HRU!")
        _LOGGER.info("Device: %s", device_info["title"])
        _LOGGER.info("Serial: %s", serial_number)
        _LOGGER.info("Port: %s", port)
        _LOGGER.info("Slave ID: %s", slave_id)
        _LOGGER.info("=" * 60)
        return device_info
        
    except ConnectionException as err:
        error_msg = (
            f"Modbus connection error on {port}: {err}\n\n"
            f"Check:\n"
            f"• USB to RS485 converter is connected\n"
            f"• Port permissions (may need: sudo chmod 666 {port})\n"
            f"• No other application is using the port"
        )
        _LOGGER.error(error_msg)
        raise CannotConnect(error_msg) from err
    except ModbusException as err:
        error_msg = (
            f"Modbus protocol error (slave_id={slave_id}): {err}\n\n"
            f"⚠️ CRITICAL CHECKLIST:\n"
            f"1. Wall controller MUST be disconnected (unplug it!)\n"
            f"2. Slave ID on device must match (check BRINK settings)\n"
            f"3. RS485 wiring: A to A, B to B\n"
            f"4. Baudrate must be {baudrate} on device\n"
            f"5. Device must be powered on"
        )
        _LOGGER.error(error_msg)
        raise CannotConnect(error_msg) from err
    except CannotConnect:
        raise
    except Exception as err:
        error_msg = f"Unexpected error during validation: {type(err).__name__}: {err}"
        _LOGGER.exception(error_msg)
        raise CannotConnect(error_msg) from err
    finally:
        try:
            client.close()
            _LOGGER.debug("Closed validation connection")
        except Exception as err:
            _LOGGER.warning("Error closing validation connection: %s", err)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BRINK HRU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect as err:
                _LOGGER.error("Connection validation failed: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during setup: %s", err)
                errors["base"] = "unknown"
            else:
                # Create unique ID based on port and slave ID
                unique_id = f"{user_input[CONF_PORT]}_{user_input['slave_id']}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        # Build schema with suggested values from user_input if available
        data_schema = STEP_USER_DATA_SCHEMA
        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(
                data_schema, user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "supported_models": ", ".join(SUPPORTED_MODELS.values())
            },
        )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
