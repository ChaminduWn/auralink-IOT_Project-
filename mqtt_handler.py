import paho.mqtt.client as mqtt
import json

class MQTTHandler:
    def __init__(self, broker, port, topic_sensor, topic_backend, on_message_callback):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.topic_sensor = topic_sensor
        self.topic_backend = topic_backend
        self.on_message_callback = on_message_callback

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message_callback
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("✅ Connected to MQTT broker")
        self.client.subscribe(self.topic_sensor)

    def publish(self, message):
        self.client.publish(self.topic_backend, json.dumps(message))

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()