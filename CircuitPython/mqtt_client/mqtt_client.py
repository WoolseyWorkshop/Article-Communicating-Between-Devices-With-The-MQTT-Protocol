"""A CircuitPython program that demonstrates how to use the MQTT protocol.

Description
-----------

A CircuitPython program that demonstrates how to use the MQTT protocol.
It can be run on either a Raspberry Pi SBC or a Raspberry Pi Pico W
microcontroller board.

The Raspberry Pi acts as an MQTT client and connects to the MQTT broker.

The client listens for (subscribes to) the following commands (topics):

- <client_id>/command/cpu_temperature (qos = 1, retained = false, message = get)
- <client_id>/command/D5 (qos = 1, retained = false, message = get | high | low)

The client reports (publishes to) the following status (topics):

- <client_id>/status/cpu_temperature (qos = 0, retained = true,
  message = temperature)
- <client_id>/status/D5 (qos = 0, retained = true, message = high | low)

The following Mosquitto commands can be used on your computer to interact with
the Raspberry Pi client.  Change the client ID, username, and password options
to those values specified within the *secrets.h* module and the MQTT broker
server configuration.

- $ mosquitto_sub -v -h raspberrypi.local -p 1883 -u <username> -P <password>
  -q 1 -t <client_id>/#
- $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password> -q 1
  -t <client_id>/command/cpu_temperature -m get
- $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password> -q 1
  -t <client_id>/command/D5 -m get
- $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password> -q 1
  -t <client_id>/command/D5 -m high
- $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password> -q 1
  -t <client_id>/command/D5 -m low

Circuit
-------

- No external components are connected to the board.

Libraries/Modules
-----------------

- *time* Standard Library
    - https://docs.python.org/3/library/time.html
    - Provides access to the *sleep* function.
- *socket* Standard Library
    - https://docs.python.org/3/library/socket.html
    - Provides a low-level networking interface on a Raspberry Pi SBC.
- *board* CircuitPython Core Module
    - https://circuitpython.readthedocs.io/en/latest/shared-bindings/board/
    - Provides access to the board's GPIO pins and hardware.
- *digitalio* CircuitPython Core Module
    - https://circuitpython.readthedocs.io/en/latest/shared-bindings/digitalio/
    - Provides basic digital pin support.
- *microcontroller* CircuitPython Core Module
    - https://circuitpython.readthedocs.io/en/latest/shared-bindings/microcontroller/
    - Provides access to the microcontroller's pin references and CPU
      temperature.
- *socketpool* CircuitPython Core Module
    - https://docs.circuitpython.org/en/latest/shared-bindings/socketpool/
    - Provides a low-level networking interface on a Raspberry Pi Pico W.
- *wifi* CircuitPython Core Module
    - https://docs.circuitpython.org/en/latest/shared-bindings/wifi/
    - Provides low-level WiFi functionality on a Raspberry Pi Pico W.
- *GPIO Zero* Library
    - https://gpiozero.readthedocs.io
    - Provides access to the CPU temperature on a Raspberry Pi SBC.
- *RPi.GPIO* Library
    - https://pypi.org/project/RPi.GPIO/
    - Provides access to the *cleanup* method on a Raspberry Pi SBC.
- *Adafruit_CircuitPython_Logging* Library
    - https://docs.circuitpython.org/projects/logging/
    - Provides logging support.
- *Adafruit_CircuitPython_MiniMQTT* Library
    - https://docs.circuitpython.org/projects/minimqtt/
    - Provides MQTT client connectivity.
- *secrets* Local Module
    - Contains the secrets (usernames, passwords, and other parameters) used for
      accessing the local WiFi network and the MQTT broker server.

Notes
-----

- The separate *secrets.py* module contains the secrets (usernames, passwords,
  and other parameters) used for accessing the local WiFi network and the MQTT
  broker server.  Replace the placeholders within that file with the appropriate
  values for your setup before running this program.
- Comments are Sphinx (reStructuredText) compatible.

TODO
----

- None.

Author(s)
---------

- Created by John Woolsey on 06/12/2023.
- Modified by John Woolsey on 08/03/2023.

Copyright (c) 2023 Woolsey Workshop.  All rights reserved.

Members
-------
"""


# Imports
from time import sleep
import board
from digitalio import DigitalInOut, Direction
import microcontroller
try:
    import gpiozero
    import RPi.GPIO as GPIO
    IS_RASPBERRY_PI_SBC = True
except:
    IS_RASPBERRY_PI_SBC = False
if IS_RASPBERRY_PI_SBC:
    import socket
elif board.board_id == "raspberry_pi_pico_w":
    import socketpool
    import wifi
import adafruit_logging as logger
import adafruit_minimqtt.adafruit_minimqtt as MQTT
try:
    import secrets
except ImportError:
    print("WiFi and MQTT secrets are stored in secrets.py.")
    raise


# Pin Mapping
if IS_RASPBERRY_PI_SBC:
    gpio_d5: microcontroller.Pin = DigitalInOut(board.D5)
    """The D5 GPIO pin."""
elif board.board_id == "raspberry_pi_pico_w":
    gpio_d5: microcontroller.Pin = DigitalInOut(board.GP5)  # use board.LED to control on-board LED
    """The D5 GPIO pin."""


# Global Constants
DEBUG: int = 1
"""Enables MQTT client debugging messages;
`0` = no messages are printed,
`1` = only program messages are printed, and
`2` = program and MQTT logging messages are printed.
"""


# Global Variables
previous_gpio_d5_value: bool = False
"""The previous value of the D5 GPIO pin."""

previous_cpu_temperature_value: float = 0.0
"""The previous value of the CPU temperature."""

high_cpu_temperature_alert: bool = False
"""The current status of the high cpu temperature alert;
`False` = alert is off, `True` = alert is on.
"""

cpu_temperature_threshold_high: float = 58
"""The high temperature threshold that enables the high cpu temperature alert."""

cpu_temperature_threshold_low: float = 56
"""The low temperature threshold that disables the high cpu temperature alert."""


# Global Instances
mqtt_client: MQTT = None
"""The instance of the MQTT client."""


# MQTT Callback Functions
def mqtt_command_cpu_temperature_received(client: MQTT, topic: str, message: str) -> None:
    """The callback function that gets called when an MQTT message is received
    from the broker with the *<client_id>/command/cpu_temperature* topic.

    Processes the incoming *cpu_temperature* command (message).

    :param MQTT client: The MQTT client that received the message; not utilized.
    :param str topic: The topic of the incoming MQTT based command.
    :param str message: The message of the incoming MQTT based command.
    """

    if DEBUG:
        print(f"Command received: {topic} {message}")
    if message == "get":
        mqtt_publish_cpu_temperature_status()
    else:
        if DEBUG:
            print("ERROR: Unknown command.")


def mqtt_command_d5_received(client: MQTT, topic: str, message: str) -> None:
    """The callback function that gets called when an MQTT message is received
    from the broker with the *<client_id>/command/D5* topic.

    Processes the incoming *D5* command (message).

    :param MQTT client: The MQTT client that received the message; not utilized.
    :param str topic: The topic of the incoming MQTT based command.
    :param str message: The message of the incoming MQTT based command.
    """

    if DEBUG:
        print(f"Command received: {topic} {message}")
    if message == "get":
        mqtt_publish_gpio_d5_status()
    elif message in ("high", "low"):
        gpio_d5.value = True if message == "high" else False
        if DEBUG:
            print(f"D5 GPIO pin set {message}.")
        mqtt_publish_gpio_d5_status()
    else:
        if DEBUG:
            print("ERROR: Unknown command.")


def mqtt_connected(client: MQTT, userdata: any, flags: int, rc: int) -> None:
    """The callback function that gets called when the MQTT client connects to
    the broker.

    Reports the broker connection status to the user.

    :param MQTT client: The MQTT client that connected.
    :param any userdata: Arbitrary callback data; not utilized.
    :param int flags: The response flags; not utilized.
    :param int rc: The connect operation's return code; not utilized.
    """

    if DEBUG:
        print(f"\nBroker connected: {client.broker}")


def mqtt_disconnected(client: MQTT, userdata: any, rc: int) -> None:
    """The callback function that gets called when the MQTT client disconnects
    from the broker.

    Reports the broker connection status to the user.

    :param MQTT client: The MQTT client that disconnected.
    :param any userdata: Arbitrary callback data; not utilized.
    :param int rc: The disconnect operation's return code; not utilized.
    """

    if DEBUG:
        print(f"Broker disconnected: {client.broker}")


def mqtt_message_received(client: MQTT, topic: str, message: str) -> None:
    """The callback function that gets called when an MQTT command (message)
    other than *cpu_temperature* and *D5* is received from the broker.

    Alerts the user to an unknown command being received.

    :param MQTT client: The MQTT client that received the message; not utilized.
    :param str topic: The topic of the incoming MQTT based command.
    :param str message: The message of the incoming MQTT based command.
    """

    if DEBUG:
        print(f"Command received: {topic} {message}")
        print("ERROR: Unknown command.")


def mqtt_published(client: MQTT, userdata: any, topic: str, pid: int) -> None:
    """The callback function that gets called when an MQTT message is published
    to the broker.

    Reports the published message to the user.

    Note, since this callback function does not have access to the actual
    messages (payloads) of the published messages, the messages are reported to
    the user directly when the messages are published.  Hence, this callback
    function is not currently being utilized, but is left here for demonstration
    purposes.

    :param MQTT client: The MQTT client that published the message;
        not utilized.
    :param any userdata: Arbitrary callback data; not utilized.
    :param str topic: The topic of the published MQTT based command.
    :param int pid: The message ID; not utilized.
    """

    if DEBUG:
        # print(f"Status published: {topic} {message}")  # preferred, but unavailable
        print(f"Status published: {topic}")


def mqtt_subscribed(client: MQTT, userdata: any, topic: str, granted_qos: int) -> None:
    """The callback function that gets called when an MQTT client subscribes to
    a topic with the broker.

    Reports the subscribed topic to the user.

    :param MQTT client: The MQTT client that subscribed to a topic;
        not utilized.
    :param any userdata: Arbitrary callback data; not utilized.
    :param str topic: The topic of the MQTT subscription.
    :param int granted_qos: The granted Quality of Service (QoS) of the MQTT
        subscription; not utilized.
    """

    if DEBUG:
        print(f"Subscribed to topic: {topic}")


def mqtt_unsubscribed(client: MQTT, userdata: any, topic: str, pid: int) -> None:
    """The callback function that gets called when an MQTT client unsubscribes
    from a topic with the broker.

    Reports the unsubscribed topic to the user.

    :param MQTT client: The MQTT client that unsubscribed from a topic;
        not utilized.
    :param any userdata: Arbitrary callback data; not utilized.
    :param str topic: The topic of the canceled MQTT subscription.
    :param int pid: The message ID; not utilized.
    """

    if DEBUG:
        print(f"Unsubscribed from topic: {topic}")


# User Functions
def configure_mqtt_client() -> None:
    """Configures the MQTT client.

    Turns on debug logging, if enabled, and sets MQTT callback functions.
    """

    global mqtt_client

    # Setup WiFi network and MQTT broker connections
    if IS_RASPBERRY_PI_SBC:
        socket_pool = socket
    if board.board_id == "raspberry_pi_pico_w":
        wifi.radio.connect(secrets.wifi["ssid"], secrets.wifi["password"])  # connect to WiFi network
        socket_pool = socketpool.SocketPool(wifi.radio)
    mqtt_client = MQTT.MQTT(
        broker=secrets.mqtt["broker_url"],
        username=secrets.mqtt["broker_username"],
        password=secrets.mqtt["broker_password"],
        client_id=secrets.mqtt["client_id"],
        socket_pool=socket_pool
    )

    # Enable debugging messages
    if DEBUG == 2:  # display MQTT debugging messages
        mqtt_client.enable_logger(logger, log_level=logger.DEBUG)

    # Assign MQTT client callback functions
    mqtt_client.on_connect = mqtt_connected
    mqtt_client.on_disconnect = mqtt_disconnected
    mqtt_client.on_message = mqtt_message_received
    # mqtt_client.on_publish = mqtt_published  # not utilized
    mqtt_client.on_subscribe = mqtt_subscribed
    mqtt_client.on_unsubscribe = mqtt_unsubscribed
    mqtt_client.add_topic_callback(
        f"{secrets.mqtt['client_id']}/command/cpu_temperature",
        mqtt_command_cpu_temperature_received
    )
    mqtt_client.add_topic_callback(
        f"{secrets.mqtt['client_id']}/command/D5",
        mqtt_command_d5_received
    )


def connect_mqtt_broker() -> None:
    """Connects to the MQTT broker."""

    if DEBUG:
        print("Connecting to MQTT broker...", end="")
    while mqtt_client.connect():
        if DEBUG:
            print(".", end="")
        sleep(1)  # wait 1 second


def mqtt_check_and_report_status() -> None:
    """Checks the status of the current CPU temperature and D5 GPIO pin values
    and reports any significant changes to the MQTT broker.

    Turns on or off the high temperature alert (publishes MQTT based commands to
    turn on/off the Arduino LED) depending on the CPU's temperature value.
    """

    # CPU Temperature Status
    current_cpu_temperature_value: float = 0
    if IS_RASPBERRY_PI_SBC:
        current_cpu_temperature_value = gpiozero.CPUTemperature().temperature
    elif board.board_id == "raspberry_pi_pico_w":
        current_cpu_temperature_value = microcontroller.cpu.temperature
    if abs(current_cpu_temperature_value - previous_cpu_temperature_value) > 2.0:
        mqtt_publish_cpu_temperature_status()

    # GPIO D5 Status
    current_gpio_d5_value: bool = gpio_d5.value
    if current_gpio_d5_value != previous_gpio_d5_value:
        mqtt_publish_gpio_d5_status()

    # High CPU Temperature Alert
    global high_cpu_temperature_alert
    if current_cpu_temperature_value > cpu_temperature_threshold_high and not high_cpu_temperature_alert:
        high_cpu_temperature_alert = True
        if DEBUG:
            print("High temperature alert enabled.")
        mqtt_client.publish("Arduino/command/LED", "on", qos=1)  # hard-coded client ID for Arduino
        if DEBUG:
            print("Command published: Arduino/command/LED on")
    elif current_cpu_temperature_value < cpu_temperature_threshold_low and high_cpu_temperature_alert:
        high_cpu_temperature_alert = False
        if DEBUG:
            print("High temperature alert disabled.")
        mqtt_client.publish("Arduino/command/LED", "off", qos=1)  # hard-coded client ID for Arduino
        if DEBUG:
            print("Command published: Arduino/command/LED off")


def mqtt_publish_cpu_temperature_status() -> None:
    """Publishes the status (value) of the CPU's temperature to the MQTT broker."""

    global previous_cpu_temperature_value
    current_cpu_temperature_value: float = 0
    if IS_RASPBERRY_PI_SBC:
        current_cpu_temperature_value = gpiozero.CPUTemperature().temperature
    elif board.board_id == "raspberry_pi_pico_w":
        current_cpu_temperature_value = microcontroller.cpu.temperature
    mqtt_client.publish(
        f"{secrets.mqtt['client_id']}/status/cpu_temperature",
        current_cpu_temperature_value,
        retain=True
    )
    if DEBUG:
        print(f"Status published: {secrets.mqtt['client_id']}/status/cpu_temperature {current_cpu_temperature_value}")
    previous_cpu_temperature_value = current_cpu_temperature_value


def mqtt_publish_gpio_d5_status() -> None:
    """Publishes the status (value) of the D5 GPIO pin to the MQTT broker."""

    global previous_gpio_d5_value
    current_gpio_d5_value: bool = gpio_d5.value
    current_gpio_d5_status: str = "high" if current_gpio_d5_value == True else "low"
    mqtt_client.publish(
        f"{secrets.mqtt['client_id']}/status/D5",
        current_gpio_d5_status,
        retain=True
    )
    if DEBUG:
        print(f"Status published: {secrets.mqtt['client_id']}/status/D5 {current_gpio_d5_status}")
    previous_gpio_d5_value = current_gpio_d5_value


def main() -> None:
    """The main program entry."""

    def loop() -> None:
        """The common looping code for all architectures."""

        if not mqtt_client.is_connected():  # keep broker connected
            mqtt_client.reconnect()
        mqtt_client.loop(1)  # listen for incoming commands; the timeout argument (1) is not typically needed, but I get the "Resource temporarily unavailable" error if I don't provide a value
        mqtt_check_and_report_status()  # report status changes

    if DEBUG:
        print("Running in DEBUG mode.  Turn off for normal operation.")
    if IS_RASPBERRY_PI_SBC:
        print("Press CTRL-C to exit.")

    # Pin configuration
    gpio_d5.direction = Direction.OUTPUT
    gpio_d5.value = False

    # MQTT configuration and connection
    configure_mqtt_client()
    connect_mqtt_broker()

    # Publish initial status
    mqtt_publish_cpu_temperature_status()
    mqtt_publish_gpio_d5_status()

    # Subscribe to commands
    mqtt_client.subscribe(f"{secrets.mqtt['client_id']}/command/#", qos=1)

    # Platform specific
    if IS_RASPBERRY_PI_SBC:
        try:
            while True:
                loop()
        except KeyboardInterrupt:  # detect CTRL-C pressed
            print()
        finally:  # clean up and report status before exiting
            mqtt_client.unsubscribe(f"{secrets.mqtt['client_id']}/command/#")
            gpio_d5.value = False
            mqtt_publish_cpu_temperature_status()
            mqtt_publish_gpio_d5_status()
            mqtt_client.disconnect()
            GPIO.cleanup()
    elif board.board_id == "raspberry_pi_pico_w":
        while True:
            loop()
    else:
        print(f"ERROR: The {board.board_id} board is not supported.")


if __name__ == "__main__":  # required for generating Sphinx documentation
    main()
