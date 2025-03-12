# kiMQTT

A simple and convenient Python library for MQTT protocol interaction. Provides a high-level interface for MQTT broker communication.

## Features

- Simple MQTT broker connection
- Asynchronous message handling
- Automatic reconnection on connection loss
- Support for QoS levels 0, 1, and 2
- SSL/TLS support with certificate validation
- Username/password authentication
- Convenient interface for publishing and subscribing to topics

### Coming Soon
- Multiple broker support (in progress)

## Installation

```bash
pip install kimqtt
```

## Quick Start

```python
from kiMQTT import MQTT

# Basic usage
client = MQTT(
    host="localhost",
    port=1883,
    client_id="test_client"
)

# Secure connection with TLS and authentication
secure_client = MQTT(
    host="mqtt.example.com",
    port=8883,  # Default SSL port
    client_id="secure_client",
    username="user",
    password="pass",
    use_tls=True,
    ca_certs="/path/to/ca.crt",  # Optional: provide CA certificate
    certfile="/path/to/client.crt",  # Optional: client certificate
    keyfile="/path/to/client.key",  # Optional: client private key
)

# Connect and subscribe
client.connect()

@client.subscribe("sensors/#")
def handle_sensor_data(message):
    print(f"Received: {message.payload} from {message.topic}")

# Publish message
client.publish("sensors/temperature", "23.5")

# Disconnect when done
client.disconnect()
```

## SSL/TLS Support

The library supports various TLS configurations:

1. System default certificates:
```python
client = MQTT(host="mqtt.example.com", use_tls=True)
```

2. Custom CA certificate:
```python
client = MQTT(
    host="mqtt.example.com",
    use_tls=True,
    ca_certs="/path/to/ca.crt"
)
```

3. Client certificate authentication:
```python
client = MQTT(
    host="mqtt.example.com",
    use_tls=True,
    ca_certs="/path/to/ca.crt",
    certfile="/path/to/client.crt",
    keyfile="/path/to/client.key"
)
```

## License

MIT License

## Author

kimifish