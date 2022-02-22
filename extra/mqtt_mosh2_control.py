import paho.mqtt.client as mqtt
from serial.tools.list_ports import comports
import modem
import tkinter as tk
from packet import getHeaderBytes
from packet import getFooterBytes
from packet import printPacket
from tkinter import StringVar
import string
import time

bPortSelected = False

cmdTypeList = {
    "version" : 0x80,
    "cpuspeed" : 0x82,
    "config" : 0x83,
    "id" : 0x84,
    "batvoltage" : 0x85,
    "startbootloader" : 0x86,
    "reset" : 0x87,
    "freqbandsnum" : 0x90,
    "freqbands" : 0x91,
    "freqcarriersnum" : 0x90,
    "freqcarriers" : 0x93,
    "rxthresh" : 0x94,
    "spreadcode" : 0x95,
    "filterraw" : 0x96,
    "synclen" : 0x96,
    "agc" : 0x98,
    "rxgain" : 0x99,
    "distanceto" : 0xA9,
    "powerlevel" : 0xB8,
    "packetstat" : 0xC0,
    "packetstatclear" : 0xC1,
    "syncstat" : 0xC2,
    "syncstatclear" : 0xC3,
    "sfdstat" : 0xC4,
    "sfdstatclear" : 0xC5,
    "allstat" : 0xC6,
    "allstatclear" : 0xC7,
    "rangedelay" : 0xA8,
    "rxlevel" : 0xB9,
    "sniffingmode" : 0xA1,
    "peakwinlen" : 0x9B,
    "transducer" : 0x9C,
    "testfreq" : 0xB1,
    "testsweep" : 0xB2,
    "testnoise" : 0xB3,
    "txgain" : 0x9A
    }


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
    print("\nMQTT Broker")
    print("Connected with result code "+str(rc)+"\n")
    
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOP_RESP + "/+/+")
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Will auto-reconnect")
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload) + "\n")
    cmdMsg.set(msg.topic+" "+str(msg.payload))
    
    if TOP_PORT in msg.topic:
        print("Asking for ports") 
        funPort(client, msg)
    
#    
    
def funPort(client, msg):
    if TOP_GET in msg.topic:
        availablePorts = "Available Ports:\n"
        for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
            availablePorts = availablePorts +"{:2}: {:20} \n".format(n, port)
            ports.append(port)
              
        if len(ports) == 0:
            print("ERROR: no serial port available")
            return None
        else:
            print("Publish: " + availablePorts)
            client.publish("cl1" + "/" + TOP_RESP + "/" + TOP_PORT, availablePorts)
    elif TOP_SET in msg.topic:
        index = int(msg.payload) - 1
        myModem = modem.Modem(ports[index])
        myModem.addRxCallback(modemRxCallBack)
        print("Modem port is: " + ports[index])    
        
def funId():
    print("Replace with your code")
    
def funCmd():
    print("Replace with your code")
    

def modemRxCallBack(pkt):
    print("Modem Rx Call Back")


# win = tk.Tk()
cmdMsg = StringVar()

# Create an MQTT client and attach our routines to it.
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

ports = []

clientID = "CC1"
mqttClient = mqtt.Client(clientID)

global myModem

def main():
#     win.title("Mosh")
#     
#     cmdMsg.set("Hello")
#     lbl_cmd = tk.Label(win, textvariable=cmdMsg)
#     lbl_cmd.pack()

    mqttClient.on_connect = on_connect
    mqttClient.on_message = on_message
     
    mqttClient.username_pw_set(USERNAME, PASSWORD)
    mqttClient.connect(brokerAddress, PORT_ADDRESS, KEEP_ALIVE_TIME)
    

    mqttClient.loop_forever()
     
    # Process network traffic and dispatch callbacks. This will also handle
    # reconnecting. Check the documentation at
    # https://github.com/eclipse/paho.mqtt.python
    # for information on how to use other loop*() functions
    # win.mainloop()
    
if __name__ == "__main__":
    main()