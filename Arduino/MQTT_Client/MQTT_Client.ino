/**
 * @mainpage MQTT Client
 *
 * @section description_main Description
 * An Arduino sketch that demonstrates how to use the MQTT protocol.
 *
 * The Arduino board acts as an MQTT client and connects to the MQTT broker.
 *
 * The client listens for (subscribes to) the following commands (topics):
 * - <client_id>/command/A0 (qos = 1, retained = false, message = get)
 * - <client_id>/command/LED (qos = 1, retained = false,
 *   message = get | on | off)
 *
 * The client reports (publishes to) the following status (topics):
 * - <client_id>/status/A0 (qos = 0, retained = true, message = adc_value)
 * - <client_id>/status/LED (qos = 0, retained = true, message = on | off)
 *
 * The following Mosquitto commands can be used on your computer to interact
 * with the Arduino client.  Change the client ID, username, and password
 * options to those values specified within the secrets.h header file and the
 * MQTT broker server configuration.
 * - $ mosquitto_sub -v -h raspberrypi.local -p 1883 -u <username> -P <password>
 *   -q 1 -t <client_id>/#
 * - $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password>
 *   -q 1 -t <client_id>/command/A0 -m get
 * - $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password>
 *   -q 1 -t <client_id>/command/LED -m get
 * - $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password>
 *   -q 1 -t <client_id>/command/LED -m on
 * - $ mosquitto_pub -h raspberrypi.local -p 1883 -u <username> -P <password>
 *   -q 1 -t <client_id>/command/LED -m off
 *
 * @section circuit_main Circuit
 * - No external components are connected to the board.
 *
 * @section notes_main Notes
 * - The separate secrets.h header file contains the secrets (usernames,
 *   passwords, and other parameters) used for accessing the local WiFi network
 *   and the MQTT broker server.
 *   Replace the placeholders within that file with the appropriate values for
 *   your setup before running this sketch.
 * - Use the Serial Monitor to view printed output while in DEBUG mode.
 *
 * Copyright (c) 2023 Woolsey Workshop.  All rights reserved.
 */


/**
 * @file MQTT_Client.ino
 *
 * @brief The primary Arduino sketch implementation file.
 *
 * @section description_mqtt_client_ino Description
 * The primary Arduino sketch implementation file.
 *
 * @section libraries_mqtt_client_ino Libraries
 * - *WiFiNINA* Arduino Library
 *   - https://www.arduino.cc/en/Reference/WiFiNINA
 *   - Provides access to the Arduino Uno WiFi Rev2 on-board WiFi module.
 * - *PubSubClient* Contributed Library
 *   - https://github.com/knolleary/pubsubclient
 *   - Provides MQTT client connectivity.
 * - *secrets* Local Header File
 *   - Contains the secrets (usernames, passwords, and other parameters) used
 *     for accessing the local WiFi network and the MQTT broker server.
 *
 * @section notes_mqtt_client_ino Notes
 * - Include the appropriate WiFi library if you are using a board other than
 *   the *Arduino Uno WiFi Rev2*.
 * - Comments are Doxygen compatible.
 *
 * @section todo_mqtt_client_ino TODO
 * - None.
 *
 * @section author_mqtt_client_ino Author(s)
 * - Created by John Woolsey on 06/16/2023.
 * - Modified by John Woolsey on 07/31/2023.
 *
 * Copyright (c) 2023 Woolsey Workshop.  All rights reserved.
 */


// Includes
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include "secrets.h"


// Defines
#define DEBUG 1  ///< The mode of operation; 0 = normal, 1 = debug.


// Global Constants
// Secrets stored in secrets.h file
const char WiFiSSID[] = WIFI_SSID;                       ///< The WiFi network SSID (name).
const char WiFiPassword[] = WIFI_PASSWORD;               ///< The WiFi network password.
const char MQTTBrokerIP[] = MQTT_BROKER_IP;              ///< The MQTT broker IP address.
const uint16_t MQTTBrokerPort = MQTT_BROKER_PORT;        ///< The MQTT broker port.
const char MQTTBrokerUsername[] = MQTT_BROKER_USERNAME;  ///< The MQTT broker username.
const char MQTTBrokerPassword[] = MQTT_BROKER_PASSWORD;  ///< The MQTT broker password.
const char MQTTClientID[] = MQTT_CLIENT_ID;              ///< The MQTT client ID.


// Global Variables
uint8_t previousLEDValue = LOW;  ///< The previous value of the on-board LED.
int previousA0Value = 0;         ///< The previous value of the A0 analog input pin.


// Global Instances
WiFiClient wifiClient;                ///< The instance of the WiFi client.
PubSubClient mqttClient(wifiClient);  ///< The instance of the MQTT client.


// Functions
/**
 * Configures the MQTT client.
 */
void configureMQTTClient() {
   mqttClient.setServer(MQTTBrokerIP, MQTTBrokerPort);
   mqttClient.setCallback(mqttCommandReceived);
}


/**
 * Initializes the Serial Monitor.
 */
void configureSerialMonitor() {
   Serial.begin(9600);  // initialize serial bus
   while (!Serial);     // wait for serial connection
}


/**
 * Connects to the MQTT broker.
 */
void connectMQTTBroker() {
   // Connect to MQTT broker
   if (DEBUG) {
      Serial.print("Connecting to MQTT broker (");
      Serial.print(MQTTBrokerIP);
      Serial.print(")...");
   }
   while (!mqttClient.connected()) {
      if (mqttClient.connect(MQTTClientID, MQTTBrokerUsername, MQTTBrokerPassword)) {
         if (DEBUG) Serial.println("connected.");
      } else {
         delay(1000);  // wait 1 second for connection
         if (DEBUG) {
            Serial.print(".");
            // The following is used for debugging connection failures
            // Serial.print("\nERROR: Client failed to connect with error code: ");
            // Serial.println(mqttClient.state());
         }
      }
   }
}


/**
 * Connects to the WiFi network.
 */
void connectWiFiNetwork() {
   // Check WiFi module connection
   if (WiFi.status() == WL_NO_MODULE) {
      if (DEBUG) Serial.println("ERROR: Communication with WiFi module failed.");
      while (true);  // don't continue
   } else {
      if (DEBUG) Serial.println("WiFi module found.");
   }

   // Check WiFi module firmware
   if (DEBUG) {
      String version = WiFi.firmwareVersion();
      if (version < WIFI_FIRMWARE_LATEST_VERSION) {
         Serial.println("Please upgrade the WiFi module firmware.");
      }
   }

   // Connect to WiFi network
   if (DEBUG) {
      Serial.print("Connecting to WiFi network (");
      Serial.print(WiFiSSID);
      Serial.print(")...");
   }
   // Connect to WPA/WPA2 network.  Change the begin() arguments if using open or WEP network.
   WiFi.begin(WiFiSSID, WiFiPassword);
   while (WiFi.status() != WL_CONNECTED) {
      delay(1000);  // wait 1 second for connection
      if (DEBUG) Serial.print(".");
   }
   if (DEBUG) Serial.println("connected.");
}


/**
 * Checks the status of the current A0 and LED_BUILTIN values and reports any
 * significant changes to the MQTT broker.
 */
void mqttCheckAndReportStatus() {
   // A0 Status
   int currentA0Value = analogRead(A0);
   if (abs(currentA0Value - previousA0Value) > 100) {
      mqttPublishA0Status();
   }

   // LED Status
   uint8_t currentLEDValue = digitalRead(LED_BUILTIN);
   if (currentLEDValue != previousLEDValue) {
      mqttPublishLEDStatus();
   }
}


/**
 * The callback function that gets called when an MQTT message is received from
 * the broker.
 *
 * Parses and processes the incoming MQTT command (message).
 *
 * @param topic    The topic of the incoming MQTT based command.
 * @param payload  The message of the incoming MQTT based command.
 * @param length   The message length of the incoming MQTT based command.
 */
void mqttCommandReceived(char* topic, byte* payload, unsigned int length) {
   // Convert payload bytes to message C-string
   char message[length + 1];
   for (unsigned int i = 0; i < length; i++) {
      message[i] = (char)payload[i];
   }
   message[length] = '\0';

   // Print command
   if (DEBUG) {
      Serial.print("Command received: ");
      Serial.print(topic);
      Serial.print(" ");
      Serial.println(message);
   }

   // Process command
   char commandA0[sizeof(MQTTClientID) + sizeof("/command/A0")] = "";
   strcat(commandA0, MQTTClientID);
   strcat(commandA0, "/command/A0");
   char commandLED[sizeof(MQTTClientID) + sizeof("/command/LED")] = "";
   strcat(commandLED, MQTTClientID);
   strcat(commandLED, "/command/LED");
   if (!strcmp(topic, commandA0) && !strcmp(message, "get")) {
      mqttPublishA0Status();
   } else if (!strcmp(topic, commandLED) && !strcmp(message, "get")) {
      mqttPublishLEDStatus();
   } else if (!strcmp(topic, commandLED) && !strcmp(message, "on")) {
      digitalWrite(LED_BUILTIN, HIGH);
      if (DEBUG) Serial.println("Turned on LED.");
      mqttPublishLEDStatus();
   } else if (!strcmp(topic, commandLED) && !strcmp(message, "off")) {
      digitalWrite(LED_BUILTIN, LOW);
      if (DEBUG) Serial.println("Turned off LED.");
      mqttPublishLEDStatus();
   } else {
      if (DEBUG) Serial.println("ERROR: Unknown command.");
   }
}


/**
 * Publishes the status (value) of the A0 analog input pin to the MQTT broker.
 */
void mqttPublishA0Status() {
   char topic[sizeof(MQTTClientID) + sizeof("/status/A0")] = "";
   strcat(topic, MQTTClientID);
   strcat(topic, "/status/A0");
   int currentA0Value = analogRead(A0);
   char status[5] = "";
   itoa(currentA0Value, status, 10);  // convert integer reading to C-string
   if (mqttClient.publish(topic, status, true)) {  // retain = true
      if (DEBUG) {
         Serial.print("Status published: ");
         Serial.print(topic);
         Serial.print(" ");
         Serial.println(status);
      }
      previousA0Value = currentA0Value;
   } else {
      if (DEBUG) Serial.println("ERROR: Unable to publish A0 status.");
   }
}


/**
 * Publishes the status (state) of the LED_BUILTIN pin to the MQTT broker.
 */
void mqttPublishLEDStatus() {
   char topic[sizeof(MQTTClientID) + sizeof("/status/LED")] = "";
   strcat(topic, MQTTClientID);
   strcat(topic, "/status/LED");
   uint8_t currentLEDValue = digitalRead(LED_BUILTIN);
   char status[4] = "";
   strcpy(status, currentLEDValue == HIGH ? "on" : "off");
   if (mqttClient.publish(topic, status, true)) {  // retain = true
      if (DEBUG) {
         Serial.print("Status published: ");
         Serial.print(topic);
         Serial.print(" ");
         Serial.println(status);
      }
      previousLEDValue = currentLEDValue;
   } else {
      if (DEBUG) Serial.println("ERROR: Unable to publish LED status.");
   }
}


/**
 * Subscribes to commands (topics) from the MQTT broker.
 */
void mqttSubscribeToCommands() {
   char topic[sizeof(MQTTClientID) + sizeof("/command/#")] = "";
   strcat(topic, MQTTClientID);
   strcat(topic, "/command/#");
   if (mqttClient.subscribe(topic, 1)) {  // QoS = 1
      if (DEBUG) {
         Serial.print("Subscribed to topic: ");
         Serial.println(topic);
      }
   } else {
      if (DEBUG) {
         Serial.print("ERROR: Unable to subscribe to topic: ");
         Serial.println(topic);
      }
   }
}


/**
 * The standard Arduino setup function used for setup and configuration tasks.
 */
void setup() {
   // Pin configuration
   pinMode(LED_BUILTIN, OUTPUT);

   // Serial Monitor
   if (DEBUG) configureSerialMonitor();

   // WiFi and MQTT connections
   configureMQTTClient();
   connectWiFiNetwork();
   connectMQTTBroker();

   // Publish initial status
   mqttPublishA0Status();
   mqttPublishLEDStatus();

   // Subscribe to commands
   mqttSubscribeToCommands();
}


/**
 * The standard Arduino loop function used for repeating tasks.
 */
void loop() {
   // Keep broker connected
   if (!mqttClient.connected()) {
      connectMQTTBroker();
      mqttSubscribeToCommands();
   }

   // Listen for incoming commands
   mqttClient.loop();

   // Report status changes
   mqttCheckAndReportStatus();
}
