import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture(autouse=True)
def mock_paho():
    """Mock the entire paho.mqtt.client module"""
    with patch('mqtt.paho.mqtt.client') as mock_paho:
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        mock_client.loop_start.return_value = None
        mock_client.loop_stop.return_value = None
        mock_client.disconnect.return_value = None
        mock_paho.Client.return_value = mock_client
        yield mock_paho

@pytest.fixture
def mqtt_class():
    """Import MQTT class after mocking dependencies"""
    with patch('mqtt.time.sleep'):  # Mock sleep to speed up tests
        from mqtt import MQTT
        MQTT._instance = None  # Reset singleton
        return MQTT

@pytest.fixture
def mqtt_config():
    """Common test configuration"""
    return {
        'host': 'test.mosquitto.org',
        'port': 1883,
        'test_topic': 'test/topic',
        'test_payload': 'test message'
    }

def test_singleton(mqtt_class, mqtt_config):
    """Verify singleton pattern implementation"""
    mqtt1 = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    mqtt2 = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    assert mqtt1 is mqtt2

@pytest.mark.parametrize('host,port', [
    (None, 1883),
    ('localhost', None),
    ('', 1883),
])
def test_invalid_init(mqtt_class, host, port):
    """Test initialization with invalid parameters"""
    with pytest.raises((ValueError, TypeError)):
        mqtt_class(host=host, port=port)

def test_connect_success(mqtt_class, mqtt_config, mock_paho):
    """Test successful connection to broker"""
    client_mock = mock_paho.Client.return_value
    # Добавляем больше значений для полного цикла подключения
    client_mock.is_connected.side_effect = [
        False,  # Initial check
        False,  # After connect
        True,   # Final check
        True    # Additional check for safety
    ]
    
    mqtt = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    mqtt.connect()

    client_mock.connect.assert_called_once_with(
        host=mqtt_config['host'],
        port=mqtt_config['port'],
        keepalive=60
    )
    client_mock.loop_start.assert_called_once()

def test_connect_with_retry(mqtt_class, mqtt_config, mock_paho):
    """Test connection retry on failure"""
    client_mock = mock_paho.Client.return_value
    
    # Эмулируем два сервера в списке хостов
    test_hosts = ['server1.example.com', 'server2.example.com']
    mqtt = mqtt_class(host=test_hosts, port=mqtt_config['port'])
    
    # Настраиваем последовательность ответов для is_connected
    client_mock.is_connected.side_effect = [
        False,  # Начальная проверка для server1
        False,  # После подключения к server1
        False,  # Начальная проверка для server2
        False,  # После подключения к server2
        False,  # Начальная проверка для server1 (второй круг)
        True,   # После успешного подключения к server1
        True,   # Финальная проверка
    ]
    
    # Счетчик попыток подключения
    attempt_count = 0
    
    def connect_responses(**kwargs):
        nonlocal attempt_count
        attempt_count += 1
        
        # На третьей попытке возвращаем успешное подключение
        if attempt_count >= 3:
            return None
            
        raise OSError("Connection refused")
    
    client_mock.connect.side_effect = connect_responses
    
    with patch('mqtt.time.sleep') as mock_sleep:
        connected = mqtt.connect()
        
        # Сбрасываем моки после теста
        client_mock.is_connected.side_effect = None
        client_mock.is_connected.return_value = True
        client_mock.connect.side_effect = None
        client_mock.connect.return_value = None
    
    assert connected is True, "Should return True on successful connection"
    
    # Проверяем последовательность вызовов connect с правильными хостами
    connect_calls = client_mock.connect.call_args_list[:3]  # Берем только первые 3 вызова
    assert len(connect_calls) == 3, "Should try to connect 3 times"
    
    # Проверяем параметры каждого вызова connect
    expected_hosts = [test_hosts[0], test_hosts[1], test_hosts[0]]  # server1, server2, server1
    for i, call in enumerate(connect_calls):
        args, kwargs = call
        assert kwargs['host'] == expected_hosts[i], f"Wrong host on attempt {i+1}"
        assert kwargs['port'] == mqtt_config['port']
        assert kwargs['keepalive'] == 60
    
    # Проверяем вызовы sleep
    assert mock_sleep.call_count == 4, "Expected exactly 4 sleep calls"
    
    # Проверяем, что loop_start вызывался для каждой попытки подключения
    assert client_mock.loop_start.call_count == 2, "Expected loop_start to be called twice"

def test_subscribe_method(mqtt_class, mqtt_config, mock_paho):
    """Test topic subscription using method"""
    client_mock = mock_paho.Client.return_value
    mqtt = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    
    def callback(msg):
        pass

    mqtt.subscribe(mqtt_config['test_topic'], callback)

    assert mqtt.callback_dict[mqtt_config['test_topic']] == callback
    client_mock.subscribe.assert_called_once_with(
        mqtt_config['test_topic'],
        qos=0  # Default QoS value
    )

def test_subscribe_decorator(mqtt_class, mqtt_config, mock_paho):
    """Test topic subscription using decorator"""
    client_mock = mock_paho.Client.return_value
    mqtt = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])

    @mqtt.subscribe(mqtt_config['test_topic'])
    def callback(msg):
        pass

    assert mqtt.callback_dict[mqtt_config['test_topic']] == callback
    client_mock.subscribe.assert_called_once_with(
        mqtt_config['test_topic'],
        qos=0  # Default QoS value
    )

def test_publish(mqtt_class, mqtt_config, mock_paho):
    """Test message publication"""
    client_mock = mock_paho.Client.return_value
    mqtt = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    mqtt.publish(
        topic=mqtt_config['test_topic'], 
        payload=mqtt_config['test_payload']
    )

    client_mock.publish.assert_called_once_with(
        mqtt_config['test_topic'],
        mqtt_config['test_payload'],
        qos=None,  # Default value
        retain=False  # Default value
    )

def test_message_handling(mqtt_class, mqtt_config, mock_paho):
    """Test message handling with callbacks"""
    mqtt = mqtt_class(host=mqtt_config['host'], port=mqtt_config['port'])
    received_messages = []

    @mqtt.subscribe(mqtt_config['test_topic'])
    def callback(msg):
        received_messages.append(msg.payload)

    test_msg = Mock()
    test_msg.topic = mqtt_config['test_topic']
    test_msg.payload = mqtt_config['test_payload']
    mqtt.on_message(None, None, test_msg)

    assert received_messages == [mqtt_config['test_payload']]

def test_context_manager(mqtt_class, mqtt_config, mock_paho):
    """Test context manager protocol implementation"""
    client_mock = mock_paho.Client.return_value
    # Настраиваем последовательность ответов для всех возможных вызовов is_connected
    client_mock.is_connected.side_effect = [False, False, True, True, True, True]
    
    with mqtt_class(host=mqtt_config['host'], port=mqtt_config['port']) as mqtt:
        # Проверяем, что подключение произошло
        assert client_mock.connect.called
        assert client_mock.loop_start.called
        
        # Сбрасываем side_effect на постоянное значение True для оставшихся проверок
        client_mock.is_connected.side_effect = None
        client_mock.is_connected.return_value = True
    
    # Проверяем отключение
    assert client_mock.disconnect.called
    assert client_mock.loop_stop.called
