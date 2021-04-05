"""Thermostat to Climate class"""

import logging

from .device_thermostat import Thermostat, WorkMode, TEMP_MIN, TEMP_MAX
from .api_interface import ApiInterface

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    PRESET_COMFORT,
    PRESET_ECO
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)

from .device_base import State

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

PRESET_CALENDAR = "calendar"
PRESET_MANUAL = "manual"
PRESET_FORSAGE = "forsage"
PRESET_VACATION = "vacation"

HA_PRESET_TO_DEVICE = {
    PRESET_CALENDAR: WorkMode.CALENDAR,
    PRESET_MANUAL: WorkMode.MANUAL,
    PRESET_COMFORT: WorkMode.COMFORT,
    PRESET_ECO: WorkMode.ECO,
    PRESET_FORSAGE: WorkMode.FORSAGE,
    PRESET_VACATION: WorkMode.VACATION,
}
DEVICE_PRESET_TO_HA = {v: k for k, v in HA_PRESET_TO_DEVICE.items()}


class Thermostat2Climate(ClimateEntity):
    """Representation of an Climate."""

    def __init__(self, uid: str, api: ApiInterface, data: dict = None):
        """Initialize"""
        _LOGGER.debug("Thermostat2Climate.init")

        self._icon = "mdi:radiator"
        self._device = Thermostat(uid, api, data)
        self._name = "thermostat" + self._device.uid
        self._uid = self._device.uid
        self._min_temp = TEMP_MIN
        self._max_temp = TEMP_MAX
        self._current_temp = None
        self._heating = False
        self._preset = None
        self._target_temp = None
        self._available = False
        self._name = None

        self._update()

    @staticmethod
    def device_type() -> str:
        return "floor"

    def _update(self):
        _LOGGER.debug("Thermostat2Climate.update")

        self._current_temp = self._device.floor_temp
        self._heating = self._device.state
        self._preset = DEVICE_PRESET_TO_HA.get(self._device.mode)
        self._available = self._device.online
        self._target_temp = self._device.floor_temp
        self._name = self._device.room

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def hvac_mode(self):
        """Return hvac operation """
        if self._heating:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes. Need to be a subset of HVAC_MODES. """
        return [HVAC_MODE_HEAT]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        await self._device.set_state(not self._heating)
        self._update()

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.  Need to be one of CURRENT_HVAC_*.  """
        if self._heating:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def unique_id(self):
        """Return the unique ID of the binary sensor."""
        return self._uid

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temp

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._min_temp:
            return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._max_temp:
            return self._max_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        return self._preset

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return [
            PRESET_CALENDAR,
            PRESET_MANUAL,
            PRESET_COMFORT,
            PRESET_ECO,
            PRESET_FORSAGE,
            PRESET_VACATION,
        ]

    async def async_set_preset_mode(self, preset_mode):
        """Set a new preset mode. If preset_mode is None, then revert to auto."""

        if self._preset == preset_mode:
            return

        await self._device.set_mode(HA_PRESET_TO_DEVICE.get(preset_mode, PRESET_COMFORT))
        self._update()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""

        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        await self._device.set_temp(target_temp * 10)
        self._update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    async def async_update(self):
        await self._device.update()
        self._update()
