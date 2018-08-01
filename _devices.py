"""
This file is used by the Yombo core to create a device object for the specific wemo devices.
"""
from yombo.lib.devices.light import Light
from yombo.lib.devices.sensor import Binary_Sensor
from yombo.lib.devices.switch import Switch
from yombo.constants.features import FEATURE_BRIGHTNESS, FEATURE_SEND_UPDATES, FEATURE_NUMBER_OF_STEPS
from yombo.constants.status_extra import STATUS_EXTRA_BRIGHTNESS

from . import const as wconst


class Wemo_Device(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SUB_PLATFORM = wconst.PLATFORM_WEMO
        self.device_mfg = wconst.DEFAULT_MANUFACTURER
        self.wemo_device = None  # A pointer to the Wemo_device instance, which holds a pointer to the final device.

    @property
    def brightness(self):
        """
        Return the brightness as a percent for this light. Returns a range between 0 and 100, converts based on the
        'number_of_steps'.
        """
        if self.wemo_device is None:
            return 0

        return self.wemo_device.brightness

    @property
    def percent(self):
        """
        Return the brightness as a percent for this light. Returns a range between 0 and 100, converts based on the
        'number_of_steps'.
        """
        if self.wemo_device is None:
            return 0

        return self.wemo_device.percent

    @property
    def debug_data(self):
        """
        Provide zwave node values to the debug display.

        :return:
        """
        debug_data = super().debug_data
        if self.has_wemo_device:
            debug_data[wconst.PLATFORM_WEMO] = {
                'title': _("module::wemo::ui::debug_header", "Wemo device details"),
                'description': _("module::wemo::ui::debug_description", "Data as reported by the wemo device."),
                'fields': [
                    _("module::wemo::ui::debug_column1", "Value name"),
                    _("module::wemo::ui::debug_column2", "Value data")
                ],
                'data': {
                    _("module::wemo::ui::debug::%s" % wconst.WEMO_MODEL, wconst.WEMO_MODEL): self.wemo_device.endpoint.model,
                    _("module::wemo::ui::debug::%s" % wconst.WEMO_MODEL_NAME, wconst.WEMO_MODEL): self.wemo_device.endpoint.model_name,
                    _("module::wemo::ui::debug::%s" % wconst.WEMO_NAME, wconst.WEMO_NAME): self.wemo_device.endpoint.name,
                    _("module::wemo::ui::debug::%s" % wconst.WEMO_SERIAL_NUMBER, wconst.WEMO_SERIAL_NUMBER): self.wemo_device.endpoint.serialnumber,
                }
            }
        else:
            debug_data[wconst.PLATFORM_WEMO] = {
                'title': _("module::wemo::ui::debug_header", "Wemo device details"),
                'description': _("module::wemo::ui::debug_description", "Data as reported by the wemo device."),
                'fields': [
                    _("module::wemo::ui::debug_column1", "Value name"),
                    _("module::wemo::ui::debug_column2", "Value data")
                ],
                'data': {
                    _("module::wemo::ui::debug_loading_column1", "Wemo is still loading"): _("module::wemo::ui::debug_loading_column2", "Try later."),
                }
            }
        return debug_data

    @property
    def has_wemo_device(self):
        if self.wemo_device is None:
            return False
        return True

    @property
    def is_on(self):
        """Return true if device is on."""
        if self.has_wemo_device is False:
            return False

        state = self.wemo_device.state
        if state >= 1:
            return True
        return False

    @property
    def is_off(self):
        """Return true if device is on."""
        if self.has_wemo_device is False:
            return True

        return not self.is_on


class Wemo_Light(Wemo_Device, Light):
    """
    Simple wemo light device, non-colorized.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.FEATURES.update({
            FEATURE_BRIGHTNESS: True,
            FEATURE_NUMBER_OF_STEPS: 100,
            FEATURE_SEND_UPDATES: True,
            }
        )
        self.MACHINE_STATUS_EXTRA_FIELDS[STATUS_EXTRA_BRIGHTNESS] = True


class Wemo_binary_sensor(Wemo_Device, Binary_Sensor):
    """
    Simple wemo lock device
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.FEATURES.update({
            FEATURE_NUMBER_OF_STEPS: False,
            FEATURE_SEND_UPDATES: True,
            }
        )


class Wemo_Switch(Wemo_Device, Switch):
    """
    Simple wemo Switch device
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.FEATURES.update({
            FEATURE_NUMBER_OF_STEPS: False,
            FEATURE_SEND_UPDATES: True,
            }
        )
