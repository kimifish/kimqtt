# kiMQTT

A simple and convenient Python library for MQTT protocol interaction. Provides a high-level interface for MQTT broker communication.

## Features

- Simple MQTT broker connection
- Asynchronous message handling
- Automatic reconnection on connection loss
- Support for QoS levels 0, 1, and 2
- Convenient interface for publishing and subscribing to topics
- Multiple broker support
- SSL/TLS support
- Authentication support

## Installation

```bash
pip install kimqtt
```

## Quick Start

```python
from kiMQTT import MQTT

# Create and connect client
client = MQTT(
    host="localhost",
    port=1883,
    client_id="test_client"
)
client.connect()

# Subscribe to topic
@client.subscribe("sensors/#")
def handle_sensor_data(message):
    print(f"Received: {message.payload} from {message.topic}")

# Publish message
client.publish("sensors/temperature", "23.5")
```

## License

MIT License

## Author

kimifish