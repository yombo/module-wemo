from time import time


from yombo.constants.commands import COMMAND_COMPONENT_INPUTS, COMMAND_COMPONENT_REQUEST_ID
from yombo.constants.features import FEATURE_BRIGHTNESS, FEATURE_PERCENT, FEATURE_NUMBER_OF_STEPS
from yombo.constants.inputs import INPUT_BRIGHTNESS, INPUT_PERCENT
from yombo.constants.status_extra import STATUS_EXTRA_BRIGHTNESS
from yombo.core.log import get_logger

logger = get_logger("modules.wemo.devices")


class Wemo_Endpoint(object):
    """
    This is a skeleton class represents a wemo device (a switch, light, sensor, etc)
    """
    FRIENDLY_LABEL = "Wemo device"

    def __init__(self, parent, endpoint):
        """
        Initialize a new Wemo device object.

        @param parent:
        @param endpoint:
        """
        self._Parent = parent
        self.endpoint = endpoint
        self.device_type = self._Parent._DeviceTypes.get('wemo_switch')
        self.device_commands = parent._Devices.device_commands
        self.yombo_device = None
        self.state = self.endpoint.get_state()
        self.commands = {}
        self.last_request_id = None
        self.device_mfg = "wemo"
        self.FEATURES: dict = {}

    def attach_yombo_device(self, yombo_device):
        """
        Attach a yombo device. This allows status updates and control commands to be used.

        :param yombo_device:
        :return: 
        """
        logger.info("Attach yombo device to me.. {label}", label=yombo_device.full_label)
        self.yombo_device = yombo_device
        self.yombo_device.wemo_device = self
        self.FEATURES = self.yombo_device.FEATURES
        self.update_value(self.state)

    def update_value(self, value):
        """
        Called when the device state changes.

        :param value:
        :return:
        """
        try:
            value = int(value)
        except:
            pass
        logger.debug("Wemo update_value: {value}", value=value)

        if self.yombo_device is None:
            logger.info("Cannot update device state, no attached Yombo device.")
            return

        # We try to guess if the status update was a result of a command request.
        last_device_command = None

        if self.last_request_id is not None and self.last_request_id in self.device_commands:
            last_device_command = self.device_commands[self.last_request_id]
            if time() - last_device_command.broadcast_at > 2:
                self.last_request_id = None

        self.update_status(value, last_device_command)

    def update_status(self, value, last_device_command):
        """
        Update the status. This can overridden by a subclass to modify the value.

        :param value:
        :param last_device_command:
        :return:
        """
        self.endpoint.state = value
        if value >= 1:
            status = 1
        else:
            status = 0

        status_extra = {}

        if FEATURE_BRIGHTNESS in self.FEATURES and self.FEATURES[FEATURE_BRIGHTNESS] is True:
            status_extra[STATUS_EXTRA_BRIGHTNESS] = value
        self.set_status(status, status_extra, last_device_command=last_device_command)

    def set_status(self, status, status_extra, last_command=None, last_device_command=None, delay=None):
        """
        Sets the status of related Yombo device.

        :param status:
        :param status_extra:
        :param last_command:
        :param last_device_command:
        :param delay:
        :return:
        """
        if delay is None:
            delay = 0.100

        if last_device_command is not None:
            command = last_device_command.command
            request_id = last_device_command.request_id
        else:
            command = None
            request_id = None

        if last_command is not None:
            command = last_command

        if status is None:
            self.yombo_device.set_status_delayed(
                delay=delay,
                machine_status_extra=status_extra,
                request_id=request_id,
                reported_by="Wemo node"
            )
        else:
            self.yombo_device.set_status_delayed(
                delay=delay,
                command=command,
                request_id=request_id,
                machine_status=status,
                machine_status_extra=status_extra,
                reported_by="Wemo node"
            )

    def turn_on(self, **kwargs):
        self.last_request_id = kwargs[COMMAND_COMPONENT_REQUEST_ID]
        if FEATURE_BRIGHTNESS in self.FEATURES and self.FEATURES[FEATURE_BRIGHTNESS] is True:
            inputs = kwargs.get(COMMAND_COMPONENT_INPUTS, {})
            brightness = 255
            if INPUT_PERCENT in inputs:
                brightness = inputs[INPUT_PERCENT]
                if brightness <= 0:
                    return self.turn_off()
                if brightness > 100:
                    brightness = 100
            elif INPUT_BRIGHTNESS in inputs:
                brightness = inputs[INPUT_BRIGHTNESS]
                if brightness == 0:
                    return self.turn_off()
                if brightness > 255:
                    brightness = 255
                brightness = int((brightness/250) * 100)

            self.endpoint.on()
            self.endpoint.set_brightness(brightness)
        else:
            self.endpoint.on()

    def turn_off(self, **kwargs):
        self.endpoint.off()

    def toggle(self, **kwargs):
        if self.state is 0:
            self.turn_on()
        else:
            self.turn_off()


class Wemo_Endpoint_Binary_Sensor(Wemo_Endpoint):
    """Representation of a wemo switch."""

    FRIENDLY_LABEL = "Wemo switch"

    def __init__(self, parent, endpoint):
        """Initialize the wemo binary sensor device."""
        Wemo_Endpoint.__init__(self, parent, endpoint)
        self.device_type = self._Parent._DeviceTypes.get('wemo_binary_sensor')
        self.FEATURES.update({
            FEATURE_BRIGHTNESS: False,
            FEATURE_PERCENT: False,
            FEATURE_NUMBER_OF_STEPS: False
        })

    def turn_on(self, **kwargs):
        pass

    def turn_off(self, **kwargs):
        pass

    def turn_toggle(self, **kwargs):
        pass


class Wemo_Endpoint_Light(Wemo_Endpoint):
    """Representation of a wemo light."""

    FRIENDLY_LABEL = "Wemo light"

    def __init__(self, parent, endpoint):
        """Initialize the wemo switch device."""
        Wemo_Endpoint.__init__(self, parent, endpoint)
        self.device_type = self._Parent._DeviceTypes.get('wemo_light')
        self.FEATURES.update({
            FEATURE_BRIGHTNESS: True,
            FEATURE_PERCENT: True,
            FEATURE_NUMBER_OF_STEPS: 100
        })

    @property
    def brightness(self):
        return self.state

    @property
    def percent(self):
        return self.state


class Wemo_Endpoint_Switch(Wemo_Endpoint):
    """Representation of a wemo switch."""

    FRIENDLY_LABEL = "Wemo switch"

    def __init__(self, parent, endpoint):
        """Initialize the wemo switch device."""
        Wemo_Endpoint.__init__(self, parent, endpoint)
        self.device_type = self._Parent._DeviceTypes.get('wemo_switch')
        self.FEATURES.update({
            FEATURE_BRIGHTNESS: False,
            FEATURE_PERCENT: False,
            FEATURE_NUMBER_OF_STEPS: False
        })
