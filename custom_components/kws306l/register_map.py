"""Register catalog for the KWS306L integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription, SensorStateClass
from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory


@dataclass(frozen=True, slots=True)
class RegisterBlock:
    """Contiguous Modbus register block."""

    start: int
    count: int


RegisterData = dict[int, int]
RegisterDecoder = Callable[[RegisterData], int | float | str | None]


@dataclass(frozen=True, kw_only=True)
class KwsSensorDescription(SensorEntityDescription):
    """Extended description for KWS306L registers."""

    register: int
    register_count: int
    access: str
    decoder: RegisterDecoder
    entity_registry_enabled_default: bool = True


ALARM_BITS: dict[int, str] = {
    0: "overvoltage",
    1: "undervoltage",
    2: "overcurrent",
    3: "overpower",
    4: "overelectricity",
    5: "overtemperature",
    6: "voltage_imbalance",
    7: "current_imbalance",
}

READ_BLOCKS: tuple[RegisterBlock, ...] = (
    RegisterBlock(start=12, count=1),
    RegisterBlock(start=14, count=61),
)


def _u16(data: RegisterData, address: int) -> int:
    return data[address]


def _u32(data: RegisterData, address: int) -> int:
    return (data[address] << 16) | data[address + 1]


def _s32(data: RegisterData, address: int) -> int:
    value = _u32(data, address)
    if value & 0x8000_0000:
        return value - 0x1_0000_0000
    return value


def _scaled(value: int, divisor: int, precision: int) -> int | float:
    if divisor == 1:
        return value
    return round(value / divisor, precision)


def decode_u16_scaled(address: int, divisor: int, precision: int) -> RegisterDecoder:
    """Decode a scaled 16-bit register."""

    def decoder(data: RegisterData) -> int | float:
        return _scaled(_u16(data, address), divisor, precision)

    return decoder


def decode_u32_scaled(address: int, divisor: int, precision: int) -> RegisterDecoder:
    """Decode a scaled 32-bit register."""

    def decoder(data: RegisterData) -> int | float:
        return _scaled(_u32(data, address), divisor, precision)

    return decoder


def decode_s32_scaled(address: int, divisor: int, precision: int) -> RegisterDecoder:
    """Decode a signed scaled 32-bit register."""

    def decoder(data: RegisterData) -> int | float:
        return _scaled(_s32(data, address), divisor, precision)

    return decoder


def decode_baud_rate_code(data: RegisterData) -> int:
    """Decode the high byte from the combined communication register."""
    return (_u16(data, 12) >> 8) & 0xFF


def decode_slave_address(data: RegisterData) -> int:
    """Decode the low byte from the combined communication register."""
    return _u16(data, 12) & 0xFF


SENSOR_DESCRIPTIONS: tuple[KwsSensorDescription, ...] = (
    KwsSensorDescription(
        key="baud_rate_code",
        name="Baud rate code",
        register=12,
        register_count=1,
        access="RW",
        decoder=decode_baud_rate_code,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:serial-port",
    ),
    KwsSensorDescription(
        key="slave_address",
        name="Slave address",
        register=12,
        register_count=1,
        access="RW",
        decoder=decode_slave_address,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    KwsSensorDescription(
        key="phase_a_voltage",
        name="Phase A voltage",
        register=14,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        decoder=decode_u16_scaled(14, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_b_voltage",
        name="Phase B voltage",
        register=15,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        decoder=decode_u16_scaled(15, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_c_voltage",
        name="Phase C voltage",
        register=16,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        decoder=decode_u16_scaled(16, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_a_current",
        name="Phase A current",
        register=17,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u32_scaled(17, 1000, 3),
    ),
    KwsSensorDescription(
        key="phase_b_current",
        name="Phase B current",
        register=19,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u32_scaled(19, 1000, 3),
    ),
    KwsSensorDescription(
        key="phase_c_current",
        name="Phase C current",
        register=21,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u32_scaled(21, 1000, 3),
    ),
    KwsSensorDescription(
        key="total_active_power",
        name="Total active power",
        register=23,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(23, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_a_active_power",
        name="Phase A active power",
        register=25,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(25, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_b_active_power",
        name="Phase B active power",
        register=27,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(27, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_c_active_power",
        name="Phase C active power",
        register=29,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(29, 10, 1),
    ),
    KwsSensorDescription(
        key="total_reactive_power",
        name="Total reactive power",
        register=31,
        register_count=2,
        access="R",
        native_unit_of_measurement="var",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_s32_scaled(31, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_a_reactive_power",
        name="Phase A reactive power",
        register=33,
        register_count=2,
        access="R",
        native_unit_of_measurement="var",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_s32_scaled(33, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_b_reactive_power",
        name="Phase B reactive power",
        register=35,
        register_count=2,
        access="R",
        native_unit_of_measurement="var",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_s32_scaled(35, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_c_reactive_power",
        name="Phase C reactive power",
        register=37,
        register_count=2,
        access="R",
        native_unit_of_measurement="var",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_s32_scaled(37, 10, 1),
    ),
    KwsSensorDescription(
        key="total_apparent_power",
        name="Total apparent power",
        register=39,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(39, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_a_apparent_power",
        name="Phase A apparent power",
        register=41,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(41, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_b_apparent_power",
        name="Phase B apparent power",
        register=43,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(43, 10, 1),
    ),
    KwsSensorDescription(
        key="phase_c_apparent_power",
        name="Phase C apparent power",
        register=45,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        decoder=decode_u32_scaled(45, 10, 1),
    ),
    KwsSensorDescription(
        key="total_power_factor",
        name="Total power factor",
        register=47,
        register_count=1,
        access="R",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u16_scaled(47, 1000, 3),
    ),
    KwsSensorDescription(
        key="phase_a_power_factor",
        name="Phase A power factor",
        register=48,
        register_count=1,
        access="R",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u16_scaled(48, 1000, 3),
    ),
    KwsSensorDescription(
        key="phase_b_power_factor",
        name="Phase B power factor",
        register=49,
        register_count=1,
        access="R",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u16_scaled(49, 1000, 3),
    ),
    KwsSensorDescription(
        key="phase_c_power_factor",
        name="Phase C power factor",
        register=50,
        register_count=1,
        access="R",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        decoder=decode_u16_scaled(50, 1000, 3),
    ),
    KwsSensorDescription(
        key="frequency",
        name="Frequency",
        register=51,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        decoder=decode_u16_scaled(51, 100, 2),
    ),
    KwsSensorDescription(
        key="total_energy",
        name="Total energy",
        register=52,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        decoder=decode_u32_scaled(52, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_a_energy",
        name="Phase A energy",
        register=54,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        decoder=decode_u32_scaled(54, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_b_energy",
        name="Phase B energy",
        register=56,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        decoder=decode_u32_scaled(56, 100, 2),
    ),
    KwsSensorDescription(
        key="phase_c_energy",
        name="Phase C energy",
        register=58,
        register_count=2,
        access="R",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        decoder=decode_u32_scaled(58, 100, 2),
    ),
    KwsSensorDescription(
        key="temperature",
        name="Temperature",
        register=60,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        decoder=decode_u16_scaled(60, 1, 0),
    ),
    KwsSensorDescription(
        key="runtime_minutes",
        name="Runtime",
        register=61,
        register_count=1,
        access="R",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL,
        decoder=decode_u16_scaled(61, 1, 0),
    ),
    KwsSensorDescription(
        key="alarm_mask",
        name="Alarm mask",
        register=62,
        register_count=1,
        access="R",
        decoder=decode_u16_scaled(62, 1, 0),
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-outline",
    ),
)
