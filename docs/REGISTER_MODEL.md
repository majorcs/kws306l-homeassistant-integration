# KWS306L register model

This is a local working document. It is intentionally kept out of Git content.

## Source summary

- workbook rows: 44
- readable rows: 42
- write-only rows: 2
- multi-register values are encoded high word first, then low word

## Initial grouped polling plan

| Block | Start | Count | Coverage |
| --- | ---: | ---: | --- |
| A | 12 | 1 | Communication settings |
| B | 14 | 61 | Voltages through over-electricity limit |

## Entity mapping

| Entity key | Addr | Count | Access | Native type | Unit | State class | Notes |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| baud_rate_code | 12 | 1 | RW | sensor | - | - | high byte of register 12 |
| slave_address | 12 | 1 | RW | sensor | - | - | low byte of register 12 |
| phase_a_voltage | 14 | 1 | R | sensor | V | measurement | divisor 100 |
| phase_b_voltage | 15 | 1 | R | sensor | V | measurement | divisor 100 |
| phase_c_voltage | 16 | 1 | R | sensor | V | measurement | divisor 100 |
| phase_a_current | 17 | 2 | R | sensor | A | measurement | divisor 1000 |
| phase_b_current | 19 | 2 | R | sensor | A | measurement | divisor 1000 |
| phase_c_current | 21 | 2 | R | sensor | A | measurement | divisor 1000 |
| total_active_power | 23 | 2 | R | sensor | W | measurement | divisor 10 |
| phase_a_active_power | 25 | 2 | R | sensor | W | measurement | divisor 10 |
| phase_b_active_power | 27 | 2 | R | sensor | W | measurement | divisor 10 |
| phase_c_active_power | 29 | 2 | R | sensor | W | measurement | divisor 10 |
| total_reactive_power | 31 | 2 | R | sensor | var | measurement | divisor 10, signed int32 on hardware |
| phase_a_reactive_power | 33 | 2 | R | sensor | var | measurement | divisor 10, signed int32 on hardware |
| phase_b_reactive_power | 35 | 2 | R | sensor | var | measurement | divisor 10, signed int32 on hardware |
| phase_c_reactive_power | 37 | 2 | R | sensor | var | measurement | divisor 10, signed int32 on hardware |
| total_apparent_power | 39 | 2 | R | sensor | VA | measurement | divisor 10 |
| phase_a_apparent_power | 41 | 2 | R | sensor | VA | measurement | divisor 10 |
| phase_b_apparent_power | 43 | 2 | R | sensor | VA | measurement | divisor 10 |
| phase_c_apparent_power | 45 | 2 | R | sensor | VA | measurement | divisor 10 |
| total_power_factor | 47 | 1 | R | sensor | - | measurement | divisor 1000 |
| phase_a_power_factor | 48 | 1 | R | sensor | - | measurement | divisor 1000 |
| phase_b_power_factor | 49 | 1 | R | sensor | - | measurement | divisor 1000 |
| phase_c_power_factor | 50 | 1 | R | sensor | - | measurement | divisor 1000 |
| frequency | 51 | 1 | R | sensor | Hz | measurement | divisor 100 |
| total_energy | 52 | 2 | R | sensor | kWh | total_increasing | divisor 100 |
| phase_a_energy | 54 | 2 | R | sensor | kWh | total_increasing | divisor 100 |
| phase_b_energy | 56 | 2 | R | sensor | kWh | total_increasing | divisor 100 |
| phase_c_energy | 58 | 2 | R | sensor | kWh | total_increasing | divisor 100 |
| temperature | 60 | 1 | R | sensor | °C | measurement | divisor 1 |
| runtime_minutes | 61 | 1 | R | sensor | min | total | raw minutes |
| alarm_mask | 62 | 1 | R | sensor | - | - | bitmask sensor |
| meter_status | 63 | 1 | RW | sensor | - | - | enum: off/on |
| overvoltage_limit | 64 | 1 | RW | sensor | V | - | divisor 10 |
| undervoltage_limit | 65 | 1 | RW | sensor | V | - | divisor 10 |
| overcurrent_limit | 66 | 1 | RW | sensor | A | - | divisor 100 |
| overpower_limit | 67 | 1 | RW | sensor | kW | - | divisor 100 |
| voltage_imbalance_limit | 68 | 1 | RW | sensor | V | - | divisor 10 |
| current_imbalance_limit | 69 | 1 | RW | sensor | A | - | divisor 10 |
| countdown_minutes | 70 | 1 | RW | sensor | min | - | raw minutes |
| screensaver_minutes | 71 | 1 | RW | sensor | min | - | raw minutes |
| overtemperature_limit | 72 | 1 | RW | sensor | °C | - | raw integer |
| overelectricity_limit | 73 | 2 | RW | sensor | kWh | - | raw integer scale from workbook |

## Write-only registers

| Addr | Meaning | Planned first-iteration support |
| ---: | --- | --- |
| 75 | Clear electricity usage | not exposed |
| 76 | Meter cleared | not exposed |

## Notes to validate on hardware

- reactive power registers `31..38` behave as signed 32-bit values on live hardware even though the workbook only documents register count and decimal scaling, not signedness
- confirm `runtime` should use the Home Assistant `total` state class in minutes
- confirm `overelectricity_limit` scaling, because the workbook shows `1` decimal metadata but the note is `kWh`
- confirm whether threshold/config sensors should remain enabled by default or move to diagnostic-only defaults
