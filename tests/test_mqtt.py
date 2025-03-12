import unittest
from unittest.mock import Mock, patch, MagicMock
import paho.mqtt.client

# Create mock for kimiUtils
mock_killer = MagicMock()
mock_killer.kill_now = False

mock_utils = MagicMock()
mock_utils.Singleton = type('Singleton', (), {'__init__': lambda x: None})

mock_logger = MagicMock()

# Apply patches for all kimiUtils modules
@patch('src.kiMQTT.mqtt.killer', mock_killer)
@patch('src.kiMQTT.mqtt.Singleton', mock_utils.Singleton)
@patch('src.kiMQTT.mqtt.get_logger', return_value=mock_logger)
class TestMQTT(unittest.TestCase):
    """Test suite for MQTT class"""

    def setUp(self):
        """Reset singleton instance before each test"""
        # Import MQTT here after patches are applied
        from mqtt import MQTT
        self.MQTT = MQTT
        self.MQTT._instances = {}
        self.host = "test.mosquitto.org"
        self.port = 1883
        self.test_topic = "test/topic"
        self.test_payload = "test message"

    def test_singleton(self, *args):
        """Verify that class implements Singleton pattern correctly"""
        mqtt1 = self.MQTT(host=self.host, port=self.port)
        mqtt2 = self.MQTT(host=self.host, port=self.port)
        self.assertIs(mqtt1, mqtt2)

    def test_invalid_init(self, *args):
        """Test initialization with invalid parameters"""
        with self.assertRaises(ValueError):
            self.MQTT(host=None, port=self.port)
        with self.assertRaises(ValueError):
            self.MQTT(host=self.host, port=None)

    @patch('paho.mqtt.client.Client')
    @patch('time.sleep')
    def test_connect(self, mock_sleep, mock_client, *args):
        """Test successful connection to broker"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.is_connected.side_effect = [False, True, True]
        mock_client.return_value = mock_instance

        # Test connection
        mqtt = self.MQTT(host=self.host, port=self.port)
        result = mqtt.connect()

        # Verify results
        self.assertTrue(result)
        mock_instance.connect.assert_called_once_with(
            host=self.host,
            port=self.port,
            keepalive=60
        )
        mock_instance.loop_start.assert_called_once()
        mock_sleep.assert_called_with(1)

    @patch('paho.mqtt.client.Client')
    @patch('time.sleep')
    def test_connect_with_error(self, mock_sleep, mock_client, *args):
        """Test connection error handling and retry mechanism"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.is_connected.side_effect = [False, False, True, True]
        mock_instance.connect.side_effect = [
            OSError("Connection refused"),
            None
        ]
        mock_client.return_value = mock_instance

        # Test connection
        mqtt = self.MQTT(host=self.host, port=self.port)
        result = mqtt.connect()

        # Verify results
        self.assertTrue(result)
        self.assertEqual(mock_instance.connect.call_count, 2)
        mock_sleep.assert_any_call(5)
        mock_sleep.assert_any_call(1)

    @patch('paho.mqtt.client.Client')
    def test_subscribe(self, mock_client, *args):
        """Test topic subscription"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.is_connected.return_value = True
        mock_client.return_value = mock_instance

        # Test subscription
        mqtt = self.MQTT(host=self.host, port=self.port)
        def callback(msg):
            pass

        mqtt.subscribe(self.test_topic, callback)

        # Verify results
        self.assertEqual(mqtt.callback_dict[self.test_topic], callback)
        mock_instance.subscribe.assert_called_once_with(self.test_topic, qos=0)

    @patch('paho.mqtt.client.Client')
    def test_publish(self, mock_client, *args):
        """Test message publication"""
        # Setup mock
        mock_instance = Mock()
        mock_instance.is_connected.return_value = True
        mock_client.return_value = mock_instance

        # Test publication
        mqtt = self.MQTT(host=self.host, port=self.port)
        mqtt.publish(self.test_topic, self.test_payload, qos=1)

        # Verify results
        mock_instance.publish.assert_called_once_with(
            self.test_topic,
            self.test_payload,
            qos=1,
            retain=False
        )

    def test_multiple_servers(self, *args):
        """Test multiple server configuration"""
        hosts = ["server1.com", "server2.com"]
        mqtt = self.MQTT(host=hosts, port=self.port)
        self.assertEqual(mqtt.host, hosts)

    @patch('paho.mqtt.client.Client')
    def test_on_message(self, mock_client, *args):
        """Test message handling"""
        mqtt = self.MQTT(host=self.host, port=self.port)

        # Setup test callback
        callback_called = False
        def test_callback(msg):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(msg.payload, self.test_payload)

        # Subscribe to topic
        mqtt.subscribe(self.test_topic, test_callback)

        # Create test message
        test_msg = Mock()
        test_msg.topic = self.test_topic
        test_msg.payload = self.test_payload

        # Trigger message handler
        mqtt.on_message(None, None, test_msg)

        # Verify results
        self.assertTrue(callback_called)


if __name__ == '__main__':
    unittest.main()
