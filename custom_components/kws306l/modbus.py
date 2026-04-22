"""Modbus transport support for KWS306L."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus.client import ModbusSerialClient, ModbusTcpClient

from .const import (
    CONF_PROTOCOL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SERIAL_BAUDRATE,
    DEFAULT_TIMEOUT,
    PROTOCOL_SERIAL,
    PROTOCOL_TCP,
)
from .register_map import RegisterBlock

_LOGGER = logging.getLogger(__name__)


class KwsModbusError(Exception):
    """Raised when Modbus communication fails."""


@dataclass(frozen=True, slots=True)
class KwsConnectionParams:
    """Connection parameters for the KWS306L transport."""

    protocol: str
    slave_id: int
    host: str | None = None
    port: int = DEFAULT_PORT
    serial_port: str | None = None
    baudrate: int = DEFAULT_SERIAL_BAUDRATE
    timeout: float = DEFAULT_TIMEOUT

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "KwsConnectionParams":
        """Build params from config entry or flow data."""
        return cls(
            protocol=str(data[CONF_PROTOCOL]),
            slave_id=int(data[CONF_SLAVE_ID]),
            host=str(data[CONF_HOST]) if data.get(CONF_HOST) else None,
            port=int(data.get(CONF_PORT, DEFAULT_PORT)),
            serial_port=str(data[CONF_SERIAL_PORT]) if data.get(CONF_SERIAL_PORT) else None,
        )


class KwsModbusClient:
    """Thin wrapper around pymodbus clients."""

    def __init__(self, hass: HomeAssistant, params: KwsConnectionParams) -> None:
        self._hass = hass
        self._params = params
        self._client: ModbusTcpClient | ModbusSerialClient | None = None

    async def async_validate_connection(self) -> None:
        """Validate connectivity by reading the first measurement register."""
        await self.async_read_blocks((RegisterBlock(start=14, count=1),))

    async def async_read_blocks(self, blocks: tuple[RegisterBlock, ...]) -> dict[int, int]:
        """Read one or more register blocks."""
        return await self._hass.async_add_executor_job(self._read_blocks_sync, blocks)

    async def async_close(self) -> None:
        """Close the client connection."""
        await self._hass.async_add_executor_job(self._close_sync)

    def _get_client(self) -> ModbusTcpClient | ModbusSerialClient:
        if self._client is not None:
            return self._client

        if self._params.protocol == PROTOCOL_TCP:
            self._client = ModbusTcpClient(
                host=self._params.host,
                port=self._params.port,
                timeout=self._params.timeout,
            )
            return self._client

        if self._params.protocol == PROTOCOL_SERIAL:
            self._client = ModbusSerialClient(
                port=self._params.serial_port,
                baudrate=self._params.baudrate,
                timeout=self._params.timeout,
                parity="N",
                stopbits=1,
                bytesize=8,
            )
            return self._client

        raise KwsModbusError(f"Unsupported protocol: {self._params.protocol}")

    def _ensure_connected(self) -> ModbusTcpClient | ModbusSerialClient:
        client = self._get_client()
        connected = client.connect()
        if connected is False:
            self._close_sync()
            raise KwsModbusError("Unable to connect to the KWS306L device")
        return client

    def _read_blocks_sync(self, blocks: tuple[RegisterBlock, ...]) -> dict[int, int]:
        client = self._ensure_connected()
        values: dict[int, int] = {}

        try:
            for block in blocks:
                result = self._read_registers(client, block.start, block.count)
                if result.isError():
                    raise KwsModbusError(
                        f"Read failed for address {block.start} count {block.count}: {result!s}"
                    )
                for index, register in enumerate(result.registers):
                    values[block.start + index] = int(register)
        except Exception as err:
            self._close_sync()
            if isinstance(err, KwsModbusError):
                raise
            raise KwsModbusError(str(err)) from err

        return values

    def _read_registers(
        self,
        client: ModbusTcpClient | ModbusSerialClient,
        address: int,
        count: int,
    ):
        try:
            return client.read_holding_registers(
                address=address,
                count=count,
                device_id=self._params.slave_id,
            )
        except TypeError:
            try:
                return client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self._params.slave_id,
                )
            except TypeError:
                return client.read_holding_registers(
                    address=address,
                    count=count,
                    unit=self._params.slave_id,
                )

    def _close_sync(self) -> None:
        if self._client is None:
            return
        try:
            self._client.close()
        finally:
            self._client = None
            _LOGGER.debug("Closed KWS306L Modbus client")
