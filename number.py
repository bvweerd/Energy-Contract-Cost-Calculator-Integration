"""Provide a custom implementation of NumberEntity for Home Assistant.

This module represents adjustable input numbers for energy contract cost calculations.

Classes:
    CustomNumberEntity: Represents an adjustable input_number entity.

Functions:
    async_setup_entry: Sets up the input_numbers as adjustable entities.
"""

import logging

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up de input_numbers als instelbare getallen."""
    input_numbers = {
        "electricity_tax_per_kwh": ("€", 0, 1, 0.001),
        "electricity_fixed_fee_day": ("€", 0, 5, 0.01),
        "electricity_fixed_return_day": ("€", 0, 5, 0.01),
        "electricity_cost_tariff_1": ("€", 0, 1, 0.001),
        "electricity_cost_tariff_2": ("€", 0, 1, 0.001),
        "electricity_profit": ("€", 0, 1, 0.001),
        "gas_fixed_fee_day": ("€", 0, 5, 0.01),
        "gas_tax": ("€", 0, 1, 0.001),
        "gas_cost": ("€", 0, 5, 0.01),
    }

    entities = [
        CustomNumberEntity(hass, key, unit, min_value, max_value, step)
        for key, (unit, min_value, max_value, step) in input_numbers.items()
    ]

    async_add_entities(entities, True)


class CustomNumberEntity(RestoreNumber):
    """Representeert een instelbare input_number als entiteit."""

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str,
        unit: str,
        min_value: float,
        max_value: float,
        step: float,
    ) -> None:
        """Initialize the input_number."""
        self.hass = hass
        self._attr_name = (
            entity_id.replace("number.", "").replace("_", " ").capitalize()
        )
        self._attr_unique_id = entity_id
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = None
        self._attr_mode = "box"

    async def async_added_to_hass(self) -> None:
        """Restore de laatst bekende waarde."""
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            None,
            "unknown",
            "unavailable",
        ):
            self._attr_native_value = float(last_state.state)
        else:
            self._attr_native_value = (
                self._attr_native_min_value
            )  # Standaardwaarde instellen

    async def async_set_native_value(self, value: float) -> None:
        """Stel de nieuwe waarde in."""
        self._attr_native_value = value
        self.hass.states.async_set(self.entity_id, value)
