"""
KiMQTT - Simple and convenient MQTT client library

Features:
- Simple MQTT broker connection
- Asynchronous message handling
- Automatic reconnection
- Multiple broker support
- SSL/TLS support
- QoS levels support
- Convenient publish/subscribe interface
"""

from .mqtt import MQTT

__version__ = '0.1.1'
__author__ = 'kimifish'
__email__ = 'kimifish@proton.me'
__license__ = 'MIT'

__all__ = ['MQTT']

# Default MQTT ports
DEFAULT_PORT = 1883
DEFAULT_SSL_PORT = 8883

# Example usage:
"""
from kiMQTT import MQTT

# Create client
client = MQTT(
    host="localhost",
    port=1883,
    client_id="test_client"
)

# Connect to broker
client.connect()

# Subscribe to topic
@client.subscribe("test/topic")
def on_message(msg):
    print(f"Received message: {msg.payload} in topic {msg.topic}")

# Publish message
client.publish("test/topic", "Hello, MQTT!")
"""
