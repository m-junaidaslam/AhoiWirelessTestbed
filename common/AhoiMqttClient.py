'''
Created on May 2, 2019

@author: junai

'''

import paho.mqtt.client as mqttClient
from common.packet import getBytes

class AhoiMqttClient(mqttClient.Client):
    """Child class of paho.mqtt.client for quick and easy interaction of AHOi modem with MQTT client."""
    
    QOS_PUB = 1 # Quality of service required for the message when publishing
    QOS_SUB = 1 # Quality of service required when subscribing to MQTT topic
    
    def __init__(self, clientId, brokerAddress, mqttPort=1883, keepAliveTime=60, username='username', password='password'):
        super().__init__(client_id=clientId, clean_session=True, transport="tcp")   # Initialize parent class
        self.clientId = clientId
        self.isAlive = True
        self.username_pw_set(username, password)
        self.connect(brokerAddress, mqttPort, keepAliveTime)
        
    def pubMsg(self, mqttTopic, mqttPayload):
        """Publish given payload to MQTT broker on given topic."""
#         print("AhoiMqttClient: publish message: topic = " + mqttTopic)
        self.publish(mqttTopic, mqttPayload, self.QOS_PUB, False)
    
    def pubPacket(self, mqttTopic, pkt):
        """Publish AHOi packet to MQTT broker on given topic."""
        self.publish(mqttTopic, getBytes(pkt), self.QOS_PUB, False)
        
    def subMsg(self, mqttTopic):
        """Subscribe to given MQTT topic"""
        self.subscribe(mqttTopic, self.QOS_SUB)
        
    def setOnConnectMethod(self, onConnectMethod):
        """Set method to be called when client is connected with MQTT broker."""
        self.on_connect = onConnectMethod
        
    def setOnDisconnectMethod(self, onDisconnectMethod):
        """Set method to be called when client is disconnected with MQTT broker."""
        self.on_disconnect = onDisconnectMethod
                
    def setOnMessageMethod(self, onMessageMethod):
        """Set method to be called when client received a message from MQTT broker."""
        self.on_message = onMessageMethod