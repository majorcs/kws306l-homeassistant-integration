"""Config flow for KWS306L."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BAUDRATE,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERIAL_BAUDRATE,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    PROTOCOL_SERIAL,
    PROTOCOL_TCP,
    SERIAL_BAUD_RATES,
    SUPPORTED_PROTOCOLS,
    build_entry_title,
    build_unique_id,
)
from .modbus import KwsConnectionParams, KwsModbusClient, KwsModbusError


def _protocol_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=PROTOCOL_TCP, label="Modbus TCP"),
                selector.SelectOptionDict(value=PROTOCOL_SERIAL, label="Modbus RTU (Serial)"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _baud_rate_selector() -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=str(rate), label=f"{rate} bps")
                for rate in SERIAL_BAUD_RATES
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _tcp_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=65535, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_SLAVE_ID,
                default=user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=247, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=3600, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "")): str,
        }
    )


def _serial_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_SERIAL_PORT, default=user_input.get(CONF_SERIAL_PORT, "/dev/ttyUSB0")): str,
            vol.Required(
                CONF_BAUDRATE,
                default=str(user_input.get(CONF_BAUDRATE, DEFAULT_SERIAL_BAUDRATE)),
            ): _baud_rate_selector(),
            vol.Required(
                CONF_SLAVE_ID,
                default=user_input.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=247, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=3600, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, "")): str,
        }
    )


class Kws306lConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KWS306L."""

    VERSION = 1

    def __init__(self) -> None:
        self._protocol = PROTOCOL_TCP

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the first step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PROTOCOL, default=self._protocol): _protocol_selector(),
                    }
                ),
            )

        protocol = str(user_input[CONF_PROTOCOL])
        if protocol not in SUPPORTED_PROTOCOLS:
            return self.async_show_form(step_id="user", errors={CONF_PROTOCOL: "invalid_protocol"})

        self._protocol = protocol
        if protocol == PROTOCOL_TCP:
            return await self.async_step_tcp()
        return await self.async_step_serial()

    async def async_step_tcp(self, user_input: dict[str, Any] | None = None):
        """Handle Modbus TCP configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            payload = {CONF_PROTOCOL: PROTOCOL_TCP, **user_input}
            try:
                await self._async_validate_payload(payload)
            except KwsModbusError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=build_entry_title(payload), data=payload)

        return self.async_show_form(step_id="tcp", data_schema=_tcp_schema(user_input), errors=errors)

    async def async_step_serial(self, user_input: dict[str, Any] | None = None):
        """Handle serial Modbus configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            payload = {CONF_PROTOCOL: PROTOCOL_SERIAL, **user_input}
            payload[CONF_BAUDRATE] = int(payload[CONF_BAUDRATE])
            try:
                await self._async_validate_payload(payload)
            except KwsModbusError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=build_entry_title(payload), data=payload)

        return self.async_show_form(step_id="serial", data_schema=_serial_schema(user_input), errors=errors)

    async def _async_validate_payload(self, payload: dict[str, Any]) -> None:
        unique_id = build_unique_id(payload)
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        client = KwsModbusClient(self.hass, KwsConnectionParams.from_mapping(payload))
        try:
            await client.async_validate_connection()
        finally:
            await client.async_close()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return Kws306lOptionsFlow(config_entry)


class Kws306lOptionsFlow(config_entries.OptionsFlow):
    """Handle options for KWS306L, including full connection reconfiguration."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Let the user edit connection settings and scan interval in place."""
        entry = self._config_entry
        protocol = entry.data[CONF_PROTOCOL]
        errors: dict[str, str] = {}
        payload: dict[str, Any] = {}

        if user_input is not None:
            payload = dict(user_input)
            if protocol == PROTOCOL_SERIAL:
                payload[CONF_BAUDRATE] = int(payload[CONF_BAUDRATE])

            updated_data = {**entry.data, **payload, CONF_PROTOCOL: protocol}
            new_unique_id = build_unique_id(updated_data)

            if any(
                other.entry_id != entry.entry_id and other.unique_id == new_unique_id
                for other in self.hass.config_entries.async_entries(DOMAIN)
            ):
                errors["base"] = "already_configured"
            else:
                client = KwsModbusClient(self.hass, KwsConnectionParams.from_mapping(updated_data))
                try:
                    await client.async_validate_connection()
                except KwsModbusError:
                    errors["base"] = "cannot_connect"
                finally:
                    await client.async_close()

            if not errors:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=updated_data,
                    title=build_entry_title(updated_data),
                    unique_id=new_unique_id,
                )
                return self.async_create_entry(
                    title="", data={CONF_SCAN_INTERVAL: updated_data[CONF_SCAN_INTERVAL]}
                )

        current = dict(entry.data)
        current[CONF_SCAN_INTERVAL] = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        current.update(payload)

        schema = _tcp_schema(current) if protocol == PROTOCOL_TCP else _serial_schema(current)
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
