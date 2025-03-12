"""
KiMQTT - Simple and convenient MQTT client library

Features:
- Simple MQTT broker connection
- Asynchronous message handling
- Automatic reconnection
- SSL/TLS support
- QoS levels support
- Convenient publish/subscribe interface
"""

from .mqtt import MQTT

__version__ = '0.1.4'
__author__ = 'kimifish'
__email__ = 'kimifish@proton.me'
__license__ = 'MIT'

__all__ = ['MQTT']

# Default MQTT ports
DEFAULT_PORT = 1883
DEFAULT_SSL_PORT = 8883