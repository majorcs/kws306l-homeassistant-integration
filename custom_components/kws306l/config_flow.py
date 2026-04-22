"""Config flow for KWS306L."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ID,
    DOMAIN,
    PROTOCOL_SERIAL,
    PROTOCOL_TCP,
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
    """Handle options for KWS306L."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=3600, mode=selector.NumberSelectorMode.BOX)
                    )
                }
            ),
        )
