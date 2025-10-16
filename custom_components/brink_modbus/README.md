# 🌬️ BRINK Heat Recovery Unit Integration

A comprehensive Home Assistant integration for BRINK Heat Recovery Ventilation units via Modbus RTU communication.

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

**Supported Models:**
- BRINK FLAIR 325
- BRINK FLAIR 325 Plus
- BRINK FLAIR 350
- BRINK FLAIR 400

## Features

### 🔍 **Comprehensive Monitoring**
- **Temperature Sensors**: Supply air, exhaust air, outside temperature
- **Pressure Sensors**: Supply and exhaust pressure monitoring
- **Flow Monitoring**: Real-time air volume measurements and fan RPM
- **Air Quality**: CO2 sensors (if equipped)
- **System Status**: Bypass state, filter condition, preheater status
- **Heat Recovery Efficiency**: Calculated in real-time

### ⚙️ **Full Control**
- **Bypass Control**: Automatic, open, or closed modes
- **Flow Control**: Precise air volume setpoints (50-325 m³/h)
- **Power Modes**: Absence, low, normal, high
- **Advanced Settings**: Imbalance correction, geo heat exchanger
- **Flow Levels**: Configure speed for each power mode

### 🎛️ **User-Friendly Interface**
- **Select Entities**: Easy dropdown controls for modes
- **Number Entities**: Slider/input controls for flow rates
- **Binary Sensors**: Clear status indicators
- **Switches**: Toggle advanced features
- **Template Sensors**: Text descriptions for all states

### 🔧 **Professional Features**
- **Device Reset**: Remote restart capability
- **Diagnostics**: Complete register readout
- **Services**: Advanced automation support
- **Error Handling**: Robust Modbus communication
- **Device Discovery**: Automatic model detection
- **Multi-language Support**: English, Slovak, Czech, Polish translations

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL
6. Select "Integration" as category
7. Click "Add"
8. Find "BRINK Heat Recovery Unit" and install

### Manual Installation

1. Download the `brink_modbus` folder from the latest release
2. Copy to your `custom_components` directory
3. Restart Home Assistant

## Hardware Setup

### Required Hardware
- BRINK HRU unit (FLAIR series)
- USB to RS485 converter
- Modbus RTU cable connection to BRINK unit

### Modbus Configuration
- **Baudrate**: 19200 bps
- **Data bits**: 8
- **Parity**: Even
- **Stop bits**: 1
- **Slave ID**: 20 (default)

### ⚠️ Important Notes
- Disconnect the 4-position wall controller before activating Modbus control
- Both cannot operate simultaneously
- Boost functionality remains available

## Configuration

### Basic Setup
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "BRINK Heat Recovery Unit"
4. Configure your connection:
   - **Port**: `/dev/ttyUSB0` or `/dev/serial/by-id/...` (stable device path recommended)
   - **Slave ID**: `20` (default, valid range: 1-247)
   - **Baudrate**: `19200` (default)
   - **Model**: Select your BRINK model

**💡 Tip**: Use `/dev/serial/by-id/` paths for stable device identification across reboots instead of `/dev/ttyUSB0` which may change.

### Supported Languages

The integration provides full translations for:
- 🇺🇸 **English** (en)
- 🇸🇰 **Slovak** (sk) 
- 🇨🇿 **Czech** (cs)
- 🇵🇱 **Polish** (pl)

All entity names, service descriptions, and configuration dialogs are localized.

### Entities Created

| Entity Type | Entity ID | Description | Unit | Values |
|-------------|-----------|-------------|------|---------|
| **Temperature Sensors** |  |  |  |  |
| Sensor | `sensor.brink_supply_air_temperature` | Supply air temperature | °C | Temperature reading |
| Sensor | `sensor.brink_exhaust_air_temperature` | Exhaust air temperature | °C | Temperature reading |
| Sensor | `sensor.brink_outside_temperature` | Outside temperature | °C | Temperature reading |
| **Pressure Sensors** |  |  |  |  |
| Sensor | `sensor.brink_supply_pressure` | Supply air pressure | Pa | Pressure reading |
| Sensor | `sensor.brink_exhaust_pressure` | Exhaust air pressure | Pa | Pressure reading |
| **Flow Sensors** |  |  |  |  |
| Sensor | `sensor.brink_supply_volume_actual` | Actual supply volume | m³/h | 0-325 |
| Sensor | `sensor.brink_exhaust_volume_actual` | Actual exhaust volume | m³/h | 0-325 |
| Sensor | `sensor.brink_supply_fan_rpm` | Supply fan RPM | RPM | 0-3000 |
| Sensor | `sensor.brink_exhaust_fan_rpm` | Exhaust fan RPM | RPM | 0-3000 |
| **System Sensors** |  |  |  |  |
| Sensor | `sensor.brink_heat_recovery_efficiency` | Heat recovery efficiency | % | 0-100 |
| Sensor | `sensor.brink_filter_usage_hours` | Filter usage hours | h | Hours count |
| Sensor | `sensor.brink_device_type` | Device type identifier | - | Device code |
| Sensor | `sensor.brink_software_version` | Software version | - | Version number |
| **CO2 Sensors** |  |  |  |  |
| Sensor | `sensor.brink_co2_sensor_1` | CO2 sensor 1 | ppm | 0-5000 |
| Sensor | `sensor.brink_co2_sensor_2` | CO2 sensor 2 | ppm | 0-5000 |
| Sensor | `sensor.brink_co2_sensor_3` | CO2 sensor 3 | ppm | 0-5000 |
| Sensor | `sensor.brink_co2_sensor_4` | CO2 sensor 4 | ppm | 0-5000 |
| **Status Text Sensors** |  |  |  |  |
| Sensor | `sensor.brink_bypass_state` | Bypass state text | - | Open/Closed/Error |
| Sensor | `sensor.brink_filter_state` | Filter state text | - | Clean/Dirty |
| Sensor | `sensor.brink_preheater_state` | Preheater state text | - | Off/Starting/Active |
| Sensor | `sensor.brink_bypass_mode` | Bypass mode text | - | Automatic/Closed/Open |
| Sensor | `sensor.brink_power_switch_position` | Power switch text | - | Absence/Low/Normal/High |
| **Binary Sensors** |  |  |  |  |
| Binary Sensor | `binary_sensor.brink_filter_dirty` | Filter dirty indicator | - | on/off |
| Binary Sensor | `binary_sensor.brink_preheater_active` | Preheater active | - | on/off |
| Binary Sensor | `binary_sensor.brink_modbus_control_active` | Modbus control active | - | on/off |
| Binary Sensor | `binary_sensor.brink_imbalance_allowed` | Imbalance allowed | - | on/off |
| Binary Sensor | `binary_sensor.brink_geo_heat_exchanger` | Geo heat exchanger | - | on/off |
| Binary Sensor | `binary_sensor.brink_co2_sensor_active` | CO2 sensor mode | - | on/off |
| **Select Controls** |  |  |  |  |
| Select | `select.brink_flair_325_plus_bypass_mode` | Bypass mode control | - | Automatic/Closed/Open |
| Select | `select.brink_flair_325_plus_power_switch_position` | Power switch control | - | Absence/Low/Normal/High |
| Select | `select.brink_flair_325_plus_modbus_control_mode` | Modbus control mode | - | Disabled/Switch/Flow |
| **Number Controls** |  |  |  |  |
| Number | `number.brink_flow_setpoint` | Target flow speed | m³/h | 50-325 |
| Number | `number.brink_flow_level_0_absence` | Flow level 0 (absence) | m³/h | 0-325 |
| Number | `number.brink_flow_level_1_low` | Flow level 1 (low) | m³/h | 0-325 |
| Number | `number.brink_flow_level_2_normal` | Flow level 2 (normal) | m³/h | 0-325 |
| Number | `number.brink_flow_level_3_high` | Flow level 3 (high) | m³/h | 0-325 |
| Number | `number.brink_supply_imbalance_offset` | Supply imbalance offset | % | -15 to +15 |
| Number | `number.brink_exhaust_imbalance_offset` | Exhaust imbalance offset | % | -15 to +15 |
| Number | `number.brink_geo_min_temperature` | Geo min temperature | °C | 0-100 |
| Number | `number.brink_geo_max_temperature` | Geo max temperature | °C | 150-400 |
| **Switch Controls** |  |  |  |  |
| Switch | `switch.brink_imbalance_allowed` | Allow imbalance | - | on/off |
| Switch | `switch.brink_co2_sensor_mode` | CO2 sensor mode | - | on/off |
| Switch | `switch.brink_geo_heat_exchanger` | Geo heat exchanger | - | on/off |
| Switch | `switch.brink_device_reset` | Device reset trigger | - | Momentary action |

## Services

### `brink_modbus.set_bypass_mode`
Set the bypass mode for optimal temperature control.

```yaml
service: brink_modbus.set_bypass_mode
target:
  device_id: <device_id>
data:
  mode: "automatic"  # automatic, closed, open
```

### `brink_modbus.set_flow_speed`
Set precise flow speed for ventilation control.

```yaml
service: brink_modbus.set_flow_speed
target:
  device_id: <device_id>
data:
  speed: 120  # 50-325 m³/h
```

### `brink_modbus.set_power_mode`
Set the power mode for different occupancy scenarios.

```yaml
service: brink_modbus.set_power_mode
target:
  device_id: <device_id>
data:
  mode: "normal"  # absence, low, normal, high
```

## Automation Examples

### Smart Temperature Control
```yaml
automation:
  - alias: "Summer Night Cooling"
    trigger:
      - platform: numeric_state
        entity_id: sensor.brink_outside_temperature
        below: 22
    condition:
      - condition: time
        after: "20:00"
        before: "08:00"
    action:
      - service: brink_modbus.set_bypass_mode
        data:
          mode: "open"
      - service: brink_modbus.set_flow_speed
        data:
          speed: 150
```

### Filter Maintenance Alert
```yaml
automation:
  - alias: "BRINK Filter Maintenance"
    trigger:
      - platform: state
        entity_id: binary_sensor.brink_filter_dirty
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "🔧 BRINK Maintenance Required"
          message: "Filter needs replacement after {{ states('sensor.brink_filter_usage_hours') }} hours"
```

### Heat Recovery Optimization
```yaml
automation:
  - alias: "Heat Recovery Efficiency Monitor"
    trigger:
      - platform: numeric_state
        entity_id: sensor.brink_heat_recovery_efficiency
        below: 80
    action:
      - service: brink_modbus.set_bypass_mode
        data:
          mode: "automatic"
      - service: notify.homeassistant
        data:
          message: "Heat recovery efficiency low: {{ states('sensor.brink_heat_recovery_efficiency') }}%"
```

## Dashboard Cards

### Entity Card
```yaml
type: entity
entity: sensor.brink_heat_recovery_efficiency
name: "Heat Recovery Efficiency"
icon: mdi:heat-pump
```

### Controls Card
```yaml
type: entities
title: "BRINK HRU Controls"
entities:
  - select.brink_flair_325_plus_bypass_mode
  - select.brink_flair_325_plus_power_switch_position
  - number.brink_flair_325_plus_flow_setpoint
  - binary_sensor.brink_flair_325_plus_filter_dirty
```

### Gauge Card
```yaml
type: gauge
entity: number.brink_flow_setpoint
name: "Flow Speed"
min: 50
max: 325
severity:
  green: 50
  yellow: 200
  red: 280
```

## Troubleshooting

### Connection Issues
1. Check USB to RS485 converter connection
2. Verify serial port path exists:
   ```bash
   ls -l /dev/serial/by-id/
   # or
   ls -l /dev/ttyUSB*
   ```
3. Check Home Assistant logs for detailed error messages
4. Ensure wall controller is disconnected
5. Verify Modbus settings match BRINK configuration (slave ID, baudrate)

### Port Lock Errors
If you see `[Errno 11] Could not exclusively lock port` errors:
1. The integration now properly releases the serial port on reload
2. Restart Home Assistant if changing port configuration
3. Ensure no other process is using the serial port

### Entity Not Updating
1. Check logs for Modbus errors
2. Verify slave ID matches BRINK setting
3. Restart integration if needed

### Register Access Errors
Some holding registers may be read-only depending on BRINK firmware version.

## Technical Details

### Modbus Register Map
Complete register documentation available in [MODBUS_BRINK.md](MODBUS_BRINK.md)

### Update Intervals
- **Fast sensors** (temperatures, flows): 10 seconds
- **Slow sensors** (settings, diagnostics): 60 seconds

### Error Handling
- Automatic reconnection on communication errors
- Graceful degradation when registers are unavailable
- Comprehensive logging for diagnostics

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create an [issue](https://github.com/peterkasarda/ha-brink-hru/issues) for bug reports
- Join the [Home Assistant Community](https://community.home-assistant.io/) for discussions
- Check the [documentation](https://github.com/peterkasarda/ha-brink-hru/wiki) for detailed guides

## Acknowledgments

- BRINK for excellent ventilation hardware
- Home Assistant community for integration framework
- pymodbus library for reliable Modbus communication

---

**Made with ❤️ for the Home Assistant community**

[releases-shield]: https://img.shields.io/github/release/peterkasarda/ha-brink-hru.svg?style=for-the-badge
[releases]: https://github.com/peterkasarda/ha-brink-hru/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/peterkasarda/ha-brink-hru.svg?style=for-the-badge
[commits]: https://github.com/peterkasarda/ha-brink-hru/commits/main
[license-shield]: https://img.shields.io/github/license/peterkasarda/ha-brink-hru.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
