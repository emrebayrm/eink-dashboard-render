# homeassistant/sensor/temperature/state
# homeassistant/sensor/humidity/state 45

import paho.mqtt.client as mqtt
import os

BROKER = os.getenv("HOME_STATUS_MQTT_BROKER")
PORT = 1883
CURRENT_TEMPERATURE_TOPIC = "homeassistant/sensor/temperature/state"
CURRENT_HUMIDITY_TOPIC = "homeassistant/sensor/humidity/state"
CLIENT_ID = "homestatus-provider-client"
USERNAME = os.getenv("HOME_STATUS_MQTT_USERNAME")    # set if broker requires auth
PASSWORD = os.getenv("HOME_STATUS_MQTT_PASSWORD")

class HomeStatusProvider:
    def __init__(self):
        self._running = False
        self.client = mqtt.Client(CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._temp = 0
        self._humidity = 0

    # Callback when the client connects to the broker
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            # Subscribe to topic upon successful connection
            client.subscribe(CURRENT_TEMPERATURE_TOPIC, qos=1)
            client.subscribe(CURRENT_HUMIDITY_TOPIC, qos=1)
        else:
            print(f"Failed to connect, return code {rc}")

    # Callback when a message is received from the broker
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"Received `{payload}` from `{topic}` topic")
        if topic == CURRENT_TEMPERATURE_TOPIC:
            self._temp = payload
        elif topic == CURRENT_HUMIDITY_TOPIC:    
            self._humidity = payload

    def start(self):
        """
        Connect to the broker and start the network loop in the background.
        """
        if not self._running:
            self.client.username_pw_set(username=USERNAME, password=PASSWORD)
            try:
                self.client.connect(BROKER, PORT, keepalive=60)
                self.client.loop_start()
                self._running = True
                print("MQTT client loop started.")
            except Exception as e:
                print(f"Error connecting to MQTT broker: {e}")
                return

    def stop(self):
        """
        Stop the network loop and disconnect cleanly.
        """
        if self._running:
            self.client.loop_stop()
            self.client.disconnect()
            self._running = False
            print("MQTT client loop stopped and disconnected.")

    def get_status(self):
        # TODO: replace with actual home status data
        return f"LivingRoom: {self._temp}°C, {self._humidity}%"
