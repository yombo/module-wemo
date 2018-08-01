#This file was created by Yombo for use with Yombo Gateway automation
#software. Details can be found at https://yombo.net
"""
Wemo
==============

Provides support for Wemo devices. Due to the device discovery, the Wemo devices must
be on the same network as the local gateway. If multiple Wemo devices are spread
across multiple networks, simply install a gateway instance on each network to create a
cluster of controllable Wemo devices.

License
=======

See LICENSE.md for full license and attribution information.

The Yombo team and other contributors hopes that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

.. moduleauthor:: Mitch Schwenk <mitch-gw@yombo.net>
:license: Apache 2.0
"""
# Import python libraries
try:  # Prefer simplejson if installed, otherwise json will work swell.
    import simplejson as json
except ImportError:
    import json
import pywemo

# Import twisted libraries
from twisted.internet.defer import inlineCallbacks
from twisted.internet import threads

from yombo.constants.commands import (COMMAND_ON, COMMAND_OFF, COMMAND_TOGGLE, COMMAND_COMPONENT_CALLED_BY,
    COMMAND_COMPONENT_COMMAND, COMMAND_COMPONENT_COMMAND_ID, COMMAND_COMPONENT_DEVICE,
    COMMAND_COMPONENT_DEVICE_COMMAND, COMMAND_COMPONENT_DEVICE_ID, COMMAND_COMPONENT_INPUTS, COMMAND_COMPONENT_PIN,
    COMMAND_COMPONENT_REQUEST_ID, COMMAND_COMPONENT_REQUESTED_BY, COMMAND_COMPONENT_SOURCE,
    COMMAND_COMPONENT_SOURCE_GATEWAY_ID)
from yombo.constants.platforms import PLATFORM_LIGHT, PLATFORM_BINARY_SENSOR, PLATFORM_SWITCH
from yombo.core.log import get_logger
from yombo.core.module import YomboModule

from . import const as wconst
from .wemo_devices import Wemo_Endpoint_Binary_Sensor, Wemo_Endpoint_Light, Wemo_Endpoint_Switch


logger = get_logger("modules.wemo")

WEMO_PLATFORMS = {
    'Bridge':  PLATFORM_LIGHT,
    'CoffeeMaker': PLATFORM_SWITCH,
    'Dimmer': PLATFORM_LIGHT,
    'Insight': PLATFORM_SWITCH,
    'LightSwitch': PLATFORM_SWITCH,
    'Maker':   PLATFORM_SWITCH,
    'Motion': PLATFORM_BINARY_SENSOR,
    'Sensor':  PLATFORM_BINARY_SENSOR,
    'Socket':  PLATFORM_SWITCH
}


class Wemo(YomboModule):
    """
    Adds support for Wemo networked devices.
    """
    def _init_(self, **kwargs):
        """
        Setup a few basic items needed by this module.

        :param kwargs:
        :return:
        """
        self._module_starting()
        self.scan_running = False
        self.yombo_devices = self._module_devices_cached
        self.wemo_devices = {}
        self.subscription_registry = None

    @inlineCallbacks
    def _load_(self, **kwargs):
        """
        Scan
        :param kwargs:
        :return:
        """
        self.subscription_registry = pywemo.SubscriptionRegistry()
        yield self.discover_devices()
        self._module_started()
        self.subscription_registry.start()

    def _stop_(self, **kwargs):
        self.subscription_registry.stop()

    @inlineCallbacks
    def discover_devices(self):
        """
        Search the network for wemo devices.

        This is a blocking function.
        :return:
        """
        if self.scan_running:
            return
        self.scan_running = True

        devices = yield threads.deferToThread(self._do_discover_devices)
        for device in devices:
            if device.serialnumber not in self.wemo_devices:
                platform = WEMO_PLATFORMS[device.model_name]
                if platform == PLATFORM_BINARY_SENSOR:
                    self.wemo_devices[device.serialnumber] = Wemo_Endpoint_Binary_Sensor(self, device)
                elif platform == PLATFORM_LIGHT:
                    self.wemo_devices[device.serialnumber] = Wemo_Endpoint_Light(self, device)
                elif platform == PLATFORM_SWITCH:
                    self.wemo_devices[device.serialnumber] = Wemo_Endpoint_Switch(self, device)

                try:
                    yombo_device = self.find_yombo_device(device.serialnumber)
                except KeyError as e:
                    yombo_device = None

                if yombo_device is not None:
                    self.subscription_registry.register(self.wemo_devices[device.serialnumber].endpoint)
                    self.subscription_registry.on(self.wemo_devices[device.serialnumber].endpoint, None, self.update_callback)
                    self.wemo_devices[device.serialnumber].attach_yombo_device(yombo_device)

                self._Discovery.new(
                    discover_id="wemo:%s" % device.serialnumber,
                    device_data={
                        'source': wconst.DISCOVERY_SOURCE,
                        'discover_id': "wemo:%s" % device.serialnumber,
                        'description': 'Wemo %s' % device.model_name,
                        'mfr': "wemo",
                        'model': device.model_name,
                        'serial': device.serialnumber,
                        'label': '',
                        'machine_label': '',
                        'device_type': self.wemo_devices[device.serialnumber].device_type,
                        'variables': {
                            'serialnumber': str(device.serialnumber),
                        },
                    'yombo_device': yombo_device
                    }, **{
                        'notification_title': 'New Wemo device found',
                        'notification_message': 'The Wemo module found a new Wemo device. <p>Type: %s<br>' %
                            device.model_name,
                    }
                )

        self.scan_running = False

    def _do_discover_devices(self):
        """
        Search the network for wemo devices.
        This is a blocking function.
        :return:
        """
        devices = pywemo.discover_devices()
        return devices

    def update_callback(self, device, device_type, value):
        """
        Called by pywemo when a device gets an update.

        :param device:
        :param device_type:
        :param value:
        :return:
        """
        if device.serialnumber in self.wemo_devices:
            self.wemo_devices[device.serialnumber].update_value(value)

    def _device_command_(self, **kwargs):
        """
        Control a wemo devicve.

        :param kwags: Contains all the details.
        :return: None
        """
        device = kwargs[COMMAND_COMPONENT_DEVICE]
        if self._is_my_device(device) is False:
            return  # not meant for us.
        request_id = kwargs[COMMAND_COMPONENT_REQUEST_ID]

        if hasattr(device, 'wemo_device') is False:
            logger.warn("Unable to control device: {label}, wemo is missing from device.", label=device.full_label)
            return

        device.device_command_accepted(request_id)
        command = kwargs[COMMAND_COMPONENT_COMMAND]
        command_label = command.machine_label
        if command_label == COMMAND_ON:
            device.device_command_received(request_id)
            device.wemo_device.turn_on(**kwargs)
        elif command_label == COMMAND_OFF:
            device.device_command_received(request_id)
            device.wemo_device.turn_off(**kwargs)
        elif command_label == COMMAND_TOGGLE:
            device.device_command_received(request_id)
            device.wemo_device.toggle(**kwargs)
        else:
            device.device_command_failed(request_id, message="Command for device not available.")

    def find_yombo_device(self, serialnumber):
        """
        Looks for an wemo device given the provided serial number.

        :param serialnumber:
        :return: the device pointer
        """
        devices = self._module_devices_cached
        for device_id, device in devices.items():
            if wconst.DEVICE_VARIABlE_SERIAL_NUMBER not in device.device_variables_cached:
                continue
            device_serial_number = device.device_variables_cached[wconst.DEVICE_VARIABlE_SERIAL_NUMBER]['values'][0]
            if device_serial_number != serialnumber:
                continue
            return device
        return None
