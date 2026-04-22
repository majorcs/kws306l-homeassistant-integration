# KWS306L Home Assistant integration

KWS306L is a Home Assistant custom integration for the KWS-306L energy meter family.

## Features

- Native Home Assistant integration with config-entry setup
- Modbus TCP and Modbus RTU support
- Multiple devices supported in parallel
- One Home Assistant device per configured meter
- Native sensor entities for voltages, currents, powers, energy totals, temperature, status, and readable protection limits
- HACS-compatible repository layout

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository:
   - `https://github.com/majorcs/kws306l-homeassistant-integration`
   - Category: `Integration`
3. Install **KWS306L** from HACS.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/kws306l` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Local manual testing

Run `./scripts/run_local_homeassistant.sh` to start a local Home Assistant instance for manual testing with a pre-seeded KWS306L serial config entry for `/dev/ttyUSB0`.

## Configuration

1. Open **Settings** -> **Devices & services**.
2. Click **Add integration**.
3. Search for **KWS306L**.
4. Choose the protocol and enter the device settings:
   - Modbus TCP: host, port, slave ID, scan interval
   - Modbus RTU: serial port, slave ID, scan interval

## Entities

The integration exposes the readable KWS306L meter values as native sensor entities, including:

- per-phase voltage and current
- active, reactive, and apparent power
- per-phase and total energy
- frequency, temperature, and runtime
- device status, alarm mask, and readable threshold values

## Releases

Release tags use the format `YYYY.MM.DD.SEQ`.
