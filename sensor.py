"""Module providing a custom sensor for calculating energy and gas costs in Home Assistant.

Classes:
    CustomEnergySensor: A sensor entity for calculating energy and gas costs.

Functions:
    async_setup_entry: Set up the custom energy sensors and adjustable numbers from a config entry.
"""

from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the custom energy sensors and adjustable numbers from a config entry."""
    config = hass.data[DOMAIN][entry.entry_id]

    electricity_sensor = config.get("electricity_sensor")
    gas_sensor = config.get("gas_sensor")

    entities = []

    if electricity_sensor:
        entities.append(
            CustomEnergySensor(
                hass, electricity_sensor, "Energie Electriciteitskosten", "€"
            )
        )
    if gas_sensor:
        entities.append(CustomEnergySensor(hass, gas_sensor, "Energie Gaskosten", "€"))

    async_add_entities(entities, True)


class CustomEnergySensor(SensorEntity):
    """Sensor for calculating energy and gas costs."""

    def __init__(
        self, hass: HomeAssistant, source_sensor: str, name: str, unit: str
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._attr_native_value = None
        self._source_sensor = source_sensor
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{source_sensor}_cost"

    async def async_update(self) -> None:
        """Update the sensor value."""
        if "electricity" in self._source_sensor:
            self._attr_native_value = self.calculate_electricity_costs()
        else:
            self._attr_native_value = self.calculate_gas_costs()

    def calculate_electricity_costs(self):
        """Calculate the electricity costs."""
        balance_tariff_1 = self.get_state(
            "sensor.electricity_meter_consumption_tariff_1_since_contract_start"
        ) - self.get_state(
            "sensor.electricity_meter_production_tariff_1_since_contract_start"
        )
        balance_tariff_2 = self.get_state(
            "sensor.electricity_meter_consumption_tariff_2_since_contract_start"
        ) - self.get_state(
            "sensor.electricity_meter_production_tariff_2_since_contract_start"
        )
        total_balance = balance_tariff_1 + balance_tariff_2

        energy_tax = (
            total_balance * self.get_state("number.electricity_tax_per_kwh")
            if total_balance > 0
            else 0
        )
        fixed_fee = self.get_days_since_start() * self.get_state(
            "number.electricity_fixed_fee_day"
        )
        fixed_fee_return = self.get_days_since_start() * self.get_state(
            "number.electricity_fixed_return_day"
        )

        cost_tariff_1 = max(0, balance_tariff_1) * self.get_state(
            "number.electricity_cost_tariff_1"
        )
        cost_tariff_2 = max(0, balance_tariff_2) * self.get_state(
            "number.electricity_cost_tariff_2"
        )

        return fixed_fee + energy_tax + fixed_fee_return + cost_tariff_1 + cost_tariff_2

    def calculate_gas_costs(self):
        """Calculate the gas costs."""
        days_since_start = self.get_days_since_start()
        fixed_fee = days_since_start * self.get_state("number.gas_fixed_fee_day")
        energy_tax = self.get_state(
            "sensor.gas_meter_since_contract_start"
        ) * self.get_state("number.gas_tax")
        energy_cost = self.get_state(
            "sensor.gas_meter_since_contract_start"
        ) * self.get_state("number.gas_cost")

        return fixed_fee + energy_tax + energy_cost

    def get_state(self, entity_id):
        """Help to get the value of an entity."""
        state = self.hass.states.get(entity_id)
        return (
            float(state.state)
            if state and state.state.replace(".", "", 1).isdigit()
            else 0
        )

    def get_days_since_start(self):
        """Calculate the number of days since the contract started."""
        contract_start = self.hass.states.get("input_datetime.energycontract_startdate")
        if not contract_start or not contract_start.state:
            return 0
        start_date = datetime.strptime(contract_start.state, "%Y-%m-%d")
        return (datetime.now() - start_date).days
