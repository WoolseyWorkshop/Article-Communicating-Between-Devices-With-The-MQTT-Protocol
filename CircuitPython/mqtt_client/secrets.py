"""The secrets file.

Description
-----------

Contains the secrets (usernames, passwords, and other parameters) used for
accessing the local WiFi network and the MQTT broker server.

Notes
-----

- Replace the placeholders with the values appropriate for your setup.
- WiFi credentials are only required for use with the Raspberry Pi Pico W.
- Comments are Sphinx (reStructuredText) compatible.

TODO
----

- None.

Author(s)
---------

- Created by John Woolsey on 06/12/2023.
- Modified by John Woolsey on 08/02/2023.

Copyright (c) 2023 Woolsey Workshop.  All rights reserved.

Members
-------
"""


# WiFi Network
wifi: dict[str, str] = {
    "ssid": "your_ssid",
    "password": "your_password"
}
"""Dictionary containing secrets for accessing the local WiFi network.

:param str ssid: The SSID (name) of the local WiFi network.
:param str password: The password for authorized access to the local WiFi
    network.
"""

# MQTT Broker
mqtt: dict[str, str] = {
    "broker_url": "raspberrypi.local",
    "broker_username": "your_username",
    "broker_password": "your_password",
    "client_id": "RaspberryPi"
}
"""Dictionary containing secrets for accessing the MQTT broker server.

:param str broker_url: The URL of the MQTT broker server.
:param str broker_username: The username for authorized access to the MQTT
    broker server.
:param str broker_password: The password for authorized access to the MQTT
    broker server.
:param str client_id: The unique client ID (name) for the MQTT client.
"""
