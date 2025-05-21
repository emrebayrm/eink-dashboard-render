
"""
Install with: pip install paho-mqtt
"""
import paho.mqtt.client as mqtt
import json, os

# MQTT broker settings
BROKER = os.getenv("WEATHER_MQTT_BROKER")
PORT = 1883
CURRENT_WEATHER_TOPIC = "weather/current"
WEATHER_FORECAST_TOPIC = "weather/estimation"
CLIENT_ID = "weather-provider-client"
USERNAME = os.getenv("WEATHER_MQTT_USERNAME")    # set if broker requires auth
PASSWORD = os.getenv("WEATHER_MQTT_PASSWORD")


def weather_emoji(code: int) -> str:
    """
    Return the weather emoji for a given weather code.
    """
    if code == 0:
        return "☀️"
    elif code == 1:
        return "🌤️"
    elif code == 2:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif code in (45, 48):
        return "🌫️"
    elif 51 <= code <= 57:
        return "🌦️"
    elif 61 <= code <= 67:
        return "🌧️"
    elif 71 <= code <= 77:
        return "❄️"
    elif 80 <= code <= 82:
        return "🌦️"
    elif code == 95:
        return "⛈️"
    else:
        return "?"

# Data provider classes with placeholder methods
class WeatherProvider:
    def __init__(self):
        self._running = False
        self.client = mqtt.Client(CLIENT_ID)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._current_weather = 0
        self._highs = [0,0,0,0,0]
        self._lows = [0,0,0,0,0]
        self._weather_code = "☀️"

        # Callback when the client connects to the broker
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            # Subscribe to topic upon successful connection
            client.subscribe(CURRENT_WEATHER_TOPIC, qos=1)
            client.subscribe(WEATHER_FORECAST_TOPIC, qos=1)
        else:
            print(f"Failed to connect, return code {rc}")

    # Callback when a message is received from the broker
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"Received `{payload}` from `{topic}` topic")
        if topic == CURRENT_WEATHER_TOPIC:
            self._parse_current_weather(payload)
        elif topic == WEATHER_FORECAST_TOPIC:
            self._parse_forecast_weather(payload)
    
    def _parse_current_weather(self, payload):
        """
        Example Data: {"temperature":15.6,"windspeed":13.0,"winddirection":30.0,"time":"2025-05-19T21:30"}
        """
        # Parse the JSON
        data = json.loads(payload)

        # Extract values
        self._current_weather = data['temperature']

    def _parse_forecast_weather(self, payload):
        """
        Example Data: {"time":["2025-05-19","2025-05-20","2025-05-21","2025-05-22","2025-05-23"],"temperature_2m_max":[20.4,19.8,16.2,13.0,12.6],"temperature_2m_min":[9.7,11.9,11.9,9.7,8.5],"weathercode":[2,3,3,53,51]}
        """
        data = json.loads(payload)

        self._highs = data["temperature_2m_max"]
        self._lows = data["temperature_2m_min"]
        self._weather_code = weather_emoji(data["weathercode"][0])


    def start(self):
        """
        Connect to the broker and start the network loop in the background.
        """
        if not self._running:
            self.client.username_pw_set(username=USERNAME, password=PASSWORD)
            self.client.connect(BROKER, PORT, keepalive=60)
            self.client.loop_start()
            self._running = True
            print("MQTT client loop started.")

    def stop(self):
        """
        Stop the network loop and disconnect cleanly.
        """
        if self._running:
            self.client.loop_stop()
            self.client.disconnect()
            self._running = False
            print("MQTT client loop stopped and disconnected.")

    def get_weather_icon(self):
        # TODO: replace with actual weather icon retrieval
        return self._weather_code
    def get_current_temperature(self):
        # TODO: replace with actual temperature
        return str(self._current_weather) + "°C"
    def get_sun_times(self):
        # TODO: replace with actual sunrise/sunset times
        return ("6:00", "18:00")
    
    def get_highs_and_lows(self):
        # TODO: replace with actual 5-day forecast data
        return self._highs, self._lows