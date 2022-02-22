'''
Created on May 4, 2019

@author: junai
'''
import ControlMosh
from serial.tools.list_ports import comports
import paho.mqtt.client as mqtt
from packet import getHeaderBytes
from packet import getFooterBytes
from packet import printPacket
import time
import string
import threading

modemConnected = False


def printRxRaw(pkt):
    res = getHeaderBytes(pkt)
    res += pkt.payload
    if(pkt.header.type < 0x80):
        res += getFooterBytes(pkt)
    output = "RX@"
    output += "{:.3f}".format(time.time())
    output += " "
    output += byteArray2HexString(res)
    output += "("
    output += "".join(filter(
                 lambda x: x in string.printable,
                 pkt.payload.decode('ascii', 'ignore')))
    output += ")"
    print("")
    print(output)
    
    printPacket(pkt)
    print("Header: " + byteArray2HexString(getHeaderBytes(pkt)))
    print("Payload: " + str(pkt.payload))
    print("Footer: " + byteArray2HexString(getFooterBytes(pkt)))

def byteArray2HexString(byteArray):
    return "".join("%02X " % b for b in byteArray)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global clientID
    print("\nI am Client: {}".format(clientID))
    print("Connected with result code "+str(rc)+"\n")
 
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOP_CMD + "/" + clientID + "/+/+")
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Will auto-reconnect")
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload) + "\n")
    
    if TOP_PORT in msg.topic:
        print("Get/set ports") 
        funPort(client, msg)
    
    if TOP_ID in msg.topic:
        print("Set/Get Modem ID")
        funId(client, msg)
        
    if TOP_SHELL in msg.topic:
        print("Execute command")
        funShell(client, msg)
        
    
    
def funPort(client, msg):
    if TOP_GET in msg.topic:
        startPortsPublishThread(client, 1)
#         availablePorts = "Available Ports:\n"
#           ports = []
#         for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
#             availablePorts = availablePorts +"{:2}: {:20} \n".format(n, port)
#             ports.append(port)
#                
#         if len(ports) == 0:
#             print("ERROR: no serial port available")
#             return None
#         else:
#             print("Publish: " + availablePorts)
#             client.publish("cl1" + "/" + TOP_RESP + "/" + TOP_PORT, availablePorts)
            
    elif TOP_SET in msg.topic:
        print(ports)
        if str(msg.payload.decode("utf-8")).isdigit():
            index = int(msg.payload.decode("utf-8")) - 1
            if (index < ports.__len__()) and (index >= 0) :
                global modemConnected
                modemConnected = True
                print("Setting serial port: modemConnected: " + str(myMosh.isModemConnected()))
                if myMosh.isModemConnected():
                    print("disconnecting modem")
                    myMosh.disconnectModem()
                    print("Modem disconnected")

                myMosh.connectModem(ports[index], printRxRaw)
                print("Modem port is: " + ports[index])
                print("Modem Connected: " + str(myMosh.isModemConnected()))
            else:
                print("Incorrect port number")
                
        else:
            print("Sent port number is not a digit")
        
def funId(client, msg):
    if TOP_GET in msg.topic:
        print("Evaluation command ID")
        myMosh.evalCmd("id")
    elif TOP_SET in msg.topic:
        print("Setting Modem Id: " + str(msg.payload))
        #client.publish("cl1" + "/" + TOP_RESP + "/" + TOP_ID , myModem.id(str(msg.payload)))
    
def funShell(client, msg):
    if TOP_GET in msg.topic:
        print("Evaluation command ID")
        myMosh.evalCmd(msg.payload.decode("utf-8"))
    elif TOP_SET in msg.topic:
        print("Setting Modem Id: " + str(msg.payload))
        #client.publish("cl1" + "/" + TOP_RESP + "/" + TOP_ID , myModem.id(str(msg.payload)))
    
def publishPorts(pubTime, client, availablePorts):
    pubDelay = 1
    loopLimit = pubTime/pubDelay
    looper = 0    
    while looper < loopLimit:
        global clientID
        client.publish(TOP_RESP + "/" + clientID + "/" + TOP_PORT, availablePorts)
        print("Thread, Modem Connected {}".format(modemConnected))
        time.sleep(pubDelay)
        looper += 1

def startPortsPublishThread(client, publishTime):
    availablePorts = "Available Ports:\n"
    del ports[:]
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
        availablePorts = availablePorts +"{:2}: {:20} \n".format(n, port)
        ports.append(port)
    portsPublishThread = threading.Thread(target=publishPorts, name="port_publisher", args=(publishTime, client, availablePorts))
    portsPublishThread.start()
    
def publishAlive(pubDelay, client):
    while True:
        global clientID
        client.publish(TOP_RESP + "/" + clientID + "/" + TOP_ALIVE, "I am alive")
        print("Alive message sent!")
        time.sleep(pubDelay)
    
def startAlivePublishThread(client, pubDelay):
    lifePublishThread = threading.Thread(target=publishAlive, name="alive_publisher", args=(pubDelay, client))
    lifePublishThread.start()
    
def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

brokerAddress = "192.168.57.240"
    
TOP_CMD = "cmd"
TOP_RESP = "resp"
    
TOP_SET = "set"
TOP_GET = "get"
TOP_EXEC = "exec"
    
TOP_PORT = "port"
TOP_ID = "id"
TOP_SHELL = "shell"
TOP_ALIVE = "alive"

USERNAME = "username"
PASSWORD = "password"
    
PORT_ADDRESS = 1883
KEEP_ALIVE_TIME = 60
    
clientID = getserial()
print("Client ID: {}".format(clientID))

ports = []
  
myMosh = ControlMosh.Mosh2()
print("Modem Connected: " + str(myMosh.isModemConnected()))

def main():
    # Create an MQTT client and attach our routines to it.
    client = mqtt.Client(clientID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(brokerAddress, PORT_ADDRESS, KEEP_ALIVE_TIME)
    
    startAlivePublishThread(client, 10)
    startPortsPublishThread(client, 5)
     
    # Process network traffic and dispatch callbacks. This will also handle
    # reconnecting. Check the documentation at
    # https://github.com/eclipse/paho.mqtt.python
    # for information on how to use other loop*() functions
    client.loop_forever()
    
if __name__ == "__main__":
    main()