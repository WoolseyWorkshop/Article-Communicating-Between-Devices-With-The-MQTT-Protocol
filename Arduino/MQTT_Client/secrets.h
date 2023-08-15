/**
 * @file secrets.h
 *
 * @brief The secrets file.
 *
 * @section description_secrets_h Description
 * Contains the secrets (usernames, passwords, and other parameters) used for
 * accessing the local WiFi network and the MQTT broker server.
 *
 * @section notes_secrets_h Notes
 * - Replace the placeholders with the values appropriate for your setup.
 * - Comments are Doxygen compatible.
 *
 * @section todo_secrets_h TODO
 * - None.
 *
 * @section author_secrets_h Author(s)
 * - Created by John Woolsey on 06/16/2023.
 * - Modified by John Woolsey on 07/31/2023.
 *
 * Copyright (c) 2023 Woolsey Workshop.  All rights reserved.
 */


// WiFi Network
#define WIFI_SSID     "your_ssid"      ///< The SSID (name) of the local WiFi network.
#define WIFI_PASSWORD "your_password"  ///< The password for authorized access to the local WiFi network.

// MQTT Broker
#define MQTT_BROKER_IP       "000.000.000.000"  ///< The IP address of the MQTT broker server.
#define MQTT_BROKER_PORT     1883               ///< The server port of the MQTT broker server.
#define MQTT_BROKER_USERNAME "your_username"    ///< The username for authorized access to the MQTT broker server.
#define MQTT_BROKER_PASSWORD "your_password"    ///< The password for authorized access to the MQTT broker server.
#define MQTT_CLIENT_ID       "Arduino"          ///< The unique client ID (name) for the MQTT client.
