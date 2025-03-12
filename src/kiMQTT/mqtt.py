import time
from typing import Optional, Union, List, Callable, Dict
import paho.mqtt.client
from paho.mqtt.client import MQTTMessage
import logging

from kimiUtils.utils import Singleton
from kimiUtils.logs import get_logger

# Constants
DEFAULT_PORT = 1883
DEFAULT_KEEPALIVE = 60
DEFAULT_QOS = 0
DEFAULT_RECONNECT_DELAY = 5
MAX_RECONNECT_ATTEMPTS = 3

log = logging.getLogger(__name__)

PayloadType = Union[str, int, float, bytes]

class MQTT(metaclass=Singleton):
    """
    MQTT client implementation with Singleton pattern.
    Provides high-level interface for MQTT broker interaction.

    Features:
    - Automatic reconnection
    - Multiple broker support
    - SSL/TLS support
    - QoS levels support
    - Callback-based message handling
    """

    def __init__(self, 
                 host: Union[str, List[str]],
                 port: int = DEFAULT_PORT,
                 client_id: Optional[str] = None,
                 keepalive: int = DEFAULT_KEEPALIVE,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 use_tls: bool = False,
                 connect_on_init: bool = False):
        """
        Initialize MQTT client.
        
        Args:
            host: String or list of strings with MQTT broker addresses
            port: Port number for connection
            client_id: Client identifier
            keepalive: Keep alive interval in seconds
            username: Username for authentication
            password: Password for authentication
            use_tls: Whether to use TLS for connection
            connect_on_init: Whether to connect immediately after initialization
        """
        if not host:
            raise ValueError("Host must be set")
        if isinstance(host, str):
            host = [host]
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.callback_dict: Dict[str, Callable] = {}
        self.client = None
        self.connected = False
        self.reconnect_attempts = 0
        self.shutdown = False

        # Callback mocks
        self.on_connect: Callable = self._on_connect
        self.on_disconnect: Callable = self._on_disconnect
        self.on_subscribe: Callable = self._on_subscribe

        self._setup_client(client_id)

        if connect_on_init:
            self.connect()

    def _setup_client(self, client_id: Optional[str] = None):
        """Setup MQTT client with necessary callbacks and settings"""
        try:
            from paho.mqtt.enums import CallbackAPIVersion
            self.client = paho.mqtt.client.Client(client_id=client_id, callback_api_version=CallbackAPIVersion.VERSION2)
        except AttributeError:
            self.client = paho.mqtt.client.Client(client_id=client_id)
        except Exception as e:
            log.error(e)
            return

        # Set callbacks
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect

        # Setup authentication if provided
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # Setup TLS if required
        if self.use_tls:
            self.client.tls_set()

    def connect(self) -> bool:
        """
        Connect to MQTT broker with reconnection support.
        
        Returns:
            bool: Connection success status
        """
        if not self.client:
            log.error("Something went wrong with paho-mqtt.")
            return False

        self.reconnect_attempts = 0
        server_counter = 0

        while not self.client.is_connected() and not self.shutdown:
            try:
                current_host = self.host[server_counter]
                log.info(f'MQTT starting - {current_host}:{self.port}...')
                
                self.client.connect(
                    host=current_host,
                    port=self.port,
                    keepalive=self.keepalive
                )
                self.loop_start()
                time.sleep(1)  # Give time to establish connection
                
                if self.client.is_connected():
                    log.info(f'MQTT connected to {current_host}:{self.port}')
                    self.connected = True
                    self.reconnect_attempts = 0
                    break
                
            except OSError as e:
                log.error(f'MQTT connection error: {e}')
                self.reconnect_attempts += 1
                
                if self.reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                    log.error("Max reconnection attempts reached")
                    break
                    
                time.sleep(DEFAULT_RECONNECT_DELAY)
                log.error('Trying another server...')
                server_counter = (server_counter + 1) % len(self.host)

        return self.client.is_connected()

    def disconnect(self):
        """Safely disconnect from the broker"""
        if self.client and self.client.is_connected():
            self.client.disconnect()
            self.client.loop_stop()
            self.connected = False

    def publish(self, 
                topic: str, 
                payload: PayloadType, 
                qos: Optional[int] = None, 
                retain: bool = False):
        """
        Publish message to a topic.
        
        Args:
            topic: Topic to publish to
            payload: Message to publish
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain the message on the broker
        """
        if not self.client.is_connected():
            log.warning("Not connected to broker. Attempting to reconnect...")
            if not self.connect():
                log.error("Failed to reconnect. Message not published.")
                return

        self.client.publish(topic, payload, qos=qos, retain=retain)
        log.debug(f"Published to {topic}: {payload}")

    def subscribe(self, topic: str, callback: Callable[[MQTTMessage], None], qos: int = DEFAULT_QOS):
        """
        Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
            callback: Message handler function
            qos: Quality of Service level
        """
        self.callback_dict[topic] = callback
        if self.client and self.client.is_connected():
            self.client.subscribe(topic, qos=qos)
            log.debug(f'Topic subscribed: {topic} → {callback.__qualname__}')
        else:
            log.info('MQTT not connected. Topic will be subscribed after connection.')

    def _subscribe_all_topics(self):
        """Resubscribe to all topics"""
        for topic in self.callback_dict:
            self.client.subscribe(topic)
            log.debug(f'Topic subscribed: {topic} → {self.callback_dict[topic].__qualname__}')

    def on_message(self, client, userdata, msg: MQTTMessage):
        """Handle incoming messages"""
        log.debug(f'MQTT msg: {msg.topic} - {msg.payload}')
        if msg.topic in self.callback_dict:
            try:
                self.callback_dict[msg.topic](msg)
            except Exception as e:
                log.error(f"Error in callback for topic {msg.topic}: {e}")

    def _on_connect(self, *args, **kwargs):
        """Handle connection event"""
        log.info(f'MQTT connection event: {args=} {kwargs=}')
        self._subscribe_all_topics()

    def _on_disconnect(self, *args, **kwargs):
        """Handle disconnection event"""
        log.info(f'MQTT disconnection event: {args=} {kwargs=}')

    def _on_subscribe(self, *args, **kwargs):
        """Handle subscription event"""
        log.debug(f'MQTT subscription event: {args=} {kwargs=}')

    def __del__(self):
        """Destructor for safe cleanup"""
        self.disconnect()

    def loop_start(self):
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

