# MQTT Client demo
# Continuously monitor two different MQTT topics for data,
# check if the received data matches two predefined 'commands'
 
import paho.mqtt.client as mqtt
import sys
import socket
 
subName = str(sys.argv[1])
#brokerAddress = str(sys.argv[2])
brokerAddress = "192.168.57.192"
topic = str(sys.argv[2])

print(brokerAddress + "\n")

SUB_TOPIC_1 = "greetings"
SUB_TOPIC_2 = "info"

USERNAME = "username"
PASSWORD = "password"

PORT_ADDRESS = 1883
KEEP_ALIVE_TIME = 60

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("\nSubscriber: " + 0)
    print("Connected with result code "+str(rc) + "\n")
 
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic + "/" + SUB_TOPIC_1)
    client.subscribe(topic + "/" + SUB_TOPIC_2)
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

#    if msg.payload == "Hello":
#       print("Received message #1, do something")
#        # Do something
#
#
#   if msg.payload == "World!":
#        print("Received message #2, do something else")
#        # Do something else
 
# Create an MQTT client and attach our routines to it.
client = mqtt.Client(subName)

client.on_connect = on_connect
client.on_message = on_message
 
client.username_pw_set(USERNAME, PASSWORD)
client.connect(brokerAddress, PORT_ADDRESS, KEEP_ALIVE_TIME)
 
# Process network traffic and dispatch callbacks. This will also handle
# reconnecting. Check the documentation at
# https://github.com/eclipse/paho.mqtt.python
# for information on how to use other loop*() functions
client.loop_forever()