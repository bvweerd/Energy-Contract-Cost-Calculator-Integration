"""Config flow for the Energy Contract Cost Calculator integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_available_sensors(hass: HomeAssistant, unit: str):
    """Haalt alle sensors op die de juiste eenheid en state_class hebben."""
    sensors = []
    for state in hass.states.async_all("sensor"):
        entity_id = state.entity_id
        attributes = state.attributes

        # Controleer of de unit kWh of m³ is en of het type total_increasing is
        if (
            attributes.get("unit_of_measurement") == unit
            and attributes.get("state_class") == "total_increasing"
        ):
            sensors.append(entity_id)

    return sensors


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Energy Contract Cost Calculator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title="Energy Contract Cost Calculator", data=user_input
            )

        # Get the available electricity and gas sensors
        electricity_sensors = get_available_sensors(self.hass, "kWh")
        gas_sensors = get_available_sensors(self.hass, "m³")

        if not electricity_sensors and not gas_sensors:
            errors["base"] = "no_sensors_found"

        STEP_USER_DATA_SCHEMA = vol.Schema(
            {
                vol.Optional("electricity_sensor"): SelectSelector(
                    SelectSelectorConfig(
                        options=electricity_sensors, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional("gas_sensor"): SelectSelector(
                    SelectSelectorConfig(
                        options=gas_sensors, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
