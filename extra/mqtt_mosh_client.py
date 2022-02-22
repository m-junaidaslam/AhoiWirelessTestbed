import paho.mqtt.client as mqtt
from serial.tools.list_ports import comports
import modem
import time
import string
import os.path
import re

from packet import getHeaderBytes
from packet import getFooterBytes

##
# setup commands
##
cmdList = {
    "allstat": {
        'func': "doAllStat",
        'param': ''
    },
    "allstatclear": {
        'func': "doAllStatClear",
        'param': ''
    },
    "version": {
        'func': "doVersion",
        'param': ''
    },
    "config": {
        'func': "doConfig",
        'param': ''
    },
    "freqbandsnum": {
        'func': "doFreqBandsNum",
        'param': '[num:int]'
    },
    "freqbands": {
        'func': "doFreqBands",
        'param': '[FREQ_BAND_NUM_MAX]x[FREQ_CARRIER_NUM_MAX]'
    },  # TODO
    "freqcarriersnum": {
        'func': "doFreqCarriersNum",
        'param': '[num:int]'
    },
    "freqcarriers": {
        'func': "doFreqCarriers",
        'param': '[FREQ_BAND_NUM_MAX]x[FREQ_CARRIER_NUM_MAX]'
    },  # TODO
    "distance": {
        'func': "doDistance",
        'paran': '[int:id]'
    },
    "rxthresh": {
        'func': "doRxThresh",
        'param': '[thresh:int]'
    },  # --> syncThresh
    "rxlevel": {
        'func': "doRxLevel",
        'param': ''
    },   # --> syncLevel
    "spreadcode": {
        'func': "doSpreadCode",
        'param': 'length:int'
    },
    "filterraw": {
        'func': "doFilterRaw",
        'param': '[stage:int value:int]'
    },
    "synclen": {
        'func': "doSyncLen",
        'param': 'len:int'
    },
    "sniffing": {
            'func': "doSniffingMode",
            'param': 'en:bool'
    },
    "agc": {
        'func': "doAgc",
        'param': 'en:(on/off)'
    },
    "rxgain": {
        'func': "doRxGain",
        'param': 'stage:int level:int'
    },
    "powerlevel": {
        'func': "doPowerLevel",
        'param': ''
    },
    "packetstat": {
        'func': "doPacketStat",
        'param': ''
    },
    "packetstatclear": {
        'func': "doPacketStatClear",
        'param': ''
    },
    "peakwinlen": {
        'func': "doPeakWinLen",
        'param': '[winlen:float(ms)]'
    },
    "range": {
        'func': "doRange",
        'param': 'rep:int delay:float(sec) [addr:int data:string]'
    },
    "range-delay": {
        'func': "doRangeDelay",
        'param': 'delay:float(ms)'
    },
    "reset": {
        'func': "doReset",
        'param': ''
        },
    "sample": {
        'func': "doSample",
        'param': 'trig:int len:int post'
    },
    "send": {
        'func': "doSend",
        'param': 'addr:int pkttype:hex [ack:ACK_TYPE data:str]'
    },
    "sendrep": {
        'func': "doSendRep",
        'param': 'rep:int delay:float(sec) addr:int pkttype:hex [data:string]'
    },
    "sfdstat": {
        'func': "doSfdStat",
        'param': ''
    },
    "sfdstatclear": {
        'func': "doSfdStatClear",
        'param': ''
    },
    "syncstat": {
        'func': "doSyncStat",
        'param': ''
    },
    "syncstatclear": {
        'func': "doSyncStatClear",
        'param': ''
    },
    "transducer": {
        'func': "doTransducer",
        'param': '[tranducer:uint(TRANSDUCER_*)]'
    },
    "txgain": {
        'func': "doTxGain",
        'param': 'value:int'
    },
    # "debug": {
    #    'func': "doDebugMode",
    #    'param': 'enable:bool'
    # },
    "id": {
        'func': "doId",
        'param': '[id:int]'
    },
    # "i2c": {
    #    'func': "doI2C",
    #    'param': 'write:bool addr:uint8 cmd:uint8 data:uint8'
    # },
    "testfreq": {
        'func': "doTestFreq",
        'param': '[index:int [lvl:int]]'
    },
    "testsweep": {
        'func': "doTestSweep",
        'param': '[gaincomp:bool<false> gap:uint<0>)]'
    },
    "testnoise": {
        'func': "doTestNoise",
        'param': '[gaincomp:bool<false> step:uint<1> duration:uint<1>]'
    },
    "batvol": {
        'func': "doBatVol",
        'param': ''
    },
    "bootloader": {
        'func': "doBootloader",
        'param': ''
    }
}


def doSniffingMode(inp):
    """Get/set sniffing mode status."""
    sniffing = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        if (param[0] == 'on'):
            sniffing = 1
        elif (param[0] == 'off'):
            sniffing = 0
        else:
            return -1
    return myModem.sniffingMode(sniffing)

def doAgc(inp):
    """Get/Set AGC status."""
    agc_status = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        if (param[0] == 'on'):
            agc_status = 1
        elif (param[0] == 'off'):
            agc_status = 0
        else:
            return -1

    return myModem.agc(agc_status)


def doBatVol(inp):
    """Get Battery Voltage."""
    return myModem.getBatVoltage()


def doBootloader(inp):
    """Reset uC and start Bootloader."""
    return myModem.startBootloader()


def doDistance(inp):
    """Get stored distance."""
    id = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        id = int(param[0])
    return myModem.getDistanceTo(id)


def doRxGain(inp):
    """Get/Set rx gain level."""
    stage = None
    level = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 2:
            return -1

        stage = int(param[0])
        level = int(param[1])
    return myModem.rxGain(stage, level)


def doPeakWinLen(inp):
    """Get/set peak window length."""
    winlen = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        winlen = int(float(param[0]) * 1000)
    return myModem.peakWinLen(winlen)


def doTransducer(inp):
    """Get/set transducer type."""
    t = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        t = int(param[0])
    return myModem.transducer(t)


def doConfig(inp):
    """Get modem config."""
    return myModem.getConfig()


def doFilterRaw(inp):
    """Get/Set rx gain."""
    stage = None
    level = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 2:
            return -1

        stage = int(param[0])
        level = param[1]
    return myModem.filterRaw(stage, level)


def doFreqBands(inp):
    """Get/Set freq band setup."""
    print("WARNING: setter not implemented")
    # howto = 'USAGE: TODO'

    # if len(inp) > 1:
    #    param = inp[1].split(' ')
    #    if len(param) != 4:
    #      return -1

    #    data = bytearray()
    #    for i in range(4):
    #        data += int(param[i]).to_bytes(1, 'big')

    return myModem.freqBands()


def doFreqBandsNum(inp):
    """Get/Set freq bands num."""
    num = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        num = int(param[0])

    return myModem.freqBandsNum(num)


def doFreqCarriers(inp):
    """Get/Set freq carrier setup."""
    print("WARNING: setter not implemented")
    # howto = 'USAGE: TODO'

    # if len(inp) > 1:
    #    param = inp[1].split(' ')
    #    if len(param) != 4:
    #        #return -1
    #
    #    data = bytearray()
    #    for i in range(4):
    #        data += int(param[i]).to_bytes(1, 'big')

    return myModem.freqCarriers()


def doFreqCarriersNum(inp):
    """Get/Set freq carrier num."""
    num = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        num = int(param[0])
    return myModem.freqCarrierNum(num)


def doId(inp):
    """Get/Set modem id."""
    print("Called Function")
    modem_id = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        modem_id = int(param[0])
    return myModem.id(modem_id)


def doLogOpen(fn):
    """Open Log file."""
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
    return myModem.logOn(param[0])


def doLogClose():
    """Close log file."""
    myModem.logOff()
    return 0


def doPacketStat(inp):
    """Get packet stats."""
    return myModem.getPacketStat()


def doPacketStatClear(inp):
    """Clear packet stat."""
    return myModem.clearPacketStat()


def doSyncStat(inp):
    """Get sync stats."""
    return myModem.getSyncStat()


def doSyncStatClear(inp):
    """Clear sync stat."""
    return myModem.clearSyncStat()

def doSfdStat(inp):
    """Get sfd stats."""
    return myModem.getSfdStat()


def doSfdStatClear(inp):
    """Clear sfd stat."""
    return myModem.clearSfdStat()

def doAllStat(inp):
    """Get al tx/rx stats."""
    return myModem.getAllStat()


def doAllStatClear(inp):
    """Clear all tx/rx stat."""
    return myModem.clearAllStat()

def doPause(inp):
    """Do nothing for a while."""
    if len(inp) != 2:
        return -1

    param = inp[1].split(' ')
    if len(param) != 1:
        return -1

    delay = float(param[0])
    print("sleeping %g seconds ..." % delay)
    time.sleep(delay)

    return 0


def doPowerLevel(inp):
    """Get power level."""
    return myModem.getPowerLevel()


##
# run commands from file (batch mode)
##
runFile = False
runFileName = ''


def doRun(inp):
    """Run script from file."""
    global runFile, runFileName

    if len(inp) != 2:
        return -1

    param = inp[1].split(' ')
    if len(param) != 1:
        return -1

    runFileName = param[0]
    if (os.path.isfile(runFileName)):
        runFile = open(runFileName, 'r')
        print("running commands from \"%s\"" % runFileName)
        return 0

    else:
        print("file \"%s\" does not exist" % runFileName)
        return 1


def doRxLevel(inp):
    """Get Rx threshold level."""
    return myModem.rxLevel()


def doRxThresh(inp):
    """Set up rx threshold."""
    thresh = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        thresh = int(param[0])
    return myModem.rxThresh(thresh)


def doRange(inp):
    """Get distance to other modems."""
    if (len(inp) < 2):
        return -1

    # rep / delay
    param = inp[1].split(' ')
    if (len(param) < 2):
        return -1

    rep = int(param[0])
    delay = float(param[1])
    dst = 255
    if (len(param) > 2 and param[2] != '*'):
        dst = int(param[2])
    data = bytearray()
    if (len(param) > 3):
        data = param[3].encode('ascii')

    # send rep times with delay
    sigInt_disable()
    for i in range(0, rep):
        if sigInt_check():
            return 0
        
        if i > 0:
            time.sleep(delay)

        # appendable data (debugging, testing, etc.)
        # for c in '01234567012345670123456701234567' :
        # hexdata += ('\\x%x' % ord(c))
        # 'R' == 0x52 ;-)
        ret = myModem.send(type=0x52, dst=dst, src=0, dsn=(i%256), status=2, payload=data)
        if ret != 0:
            return -1

    sigInt_enable()

    return 0


def doRangeDelay(inp):
    """Set delay for range answer."""
    delay = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if(len(param) != 1):
            return -1
        delay = int(param[0])
    return myModem.rangeDelay(delay)


def doReset(inp):
    """Reset the modem."""
    return myModem.reset()


def doSample(inp):
    """Get samples."""
    if (len(inp) < 2):
        return -1

    param = inp[1].split(' ')
    if (len(param) < 3):
        return -1

    trig = int(param[0])
    num = int(param[1])
    post = int(param[2])
    return myModem.sample(trig, num, post)


def doSend(inp):
    """Send a packet."""
    if(len(inp) != 2):
        return -1

    # send pkttype data
    param = inp[1].split(' ')
    if (len(param) < 2):
        return -1
    # dst = MM_ADDR_BCAST
    dst = None
    if (param[0] != '*'):
        if not param[0].isdigit():
            return -1
        dst = int(param[0])
    try:
        pkttype = int(param[1], 16)
    except ValueError:
        return -1
    ack = 0
    if(len(param) > 2):
        try:
            ack = int(param[2])
        except ValueError:
            ack = 0

    data = ''
    # print param
    if len(param) > 3:
        data = data.join(param[3:])
    # string -> hex
    # hexdata = ''
    # for c in data:
    #     hexdata += ('\\x%x' % ord(c))
    # print("data:", data)
    # print("databytearray:", bytearray(data, 'ascii'))

    return myModem.send(src=0, dst=dst, type=pkttype, status=ack,
                        payload=data.encode('ascii', 'ignore'))
    # return sendPacket(pkttype, bytearray(data, 'ascii'))


def doSendRep(inp):
    """Send multiple packets (including sequence number)."""
    if (len(inp) < 2):
        return -1

    # send pkttype data
    param = inp[1].split(' ')
    if (len(param) < 4) or (len(param) > 5):
        return -1

    # init
    try:
        rep = int(param[0])
        delay = float(param[1])
    except ValueError:
        return -1

    if (param[2] != '*'):
        if not param[2].isdigit():
            return -1
        dst = int(param[2])
    try:
        pkttype = int(param[3], 16)
    except ValueError:
        return -1
    data = ''
    if len(param) == 5:
        data = param[4]

    # string -> hex
    # hexdata = ''
    # for c in data:
    #     hexdata += ('\\x%x' % ord(c))

    # send rep times with delay
    sigInt_disable()
    for i in range(0, rep):
        if sigInt_check():
            return 0
        
        if i > 0:
            time.sleep(delay)

        # seqno = "\\x%02x" % (i)

        print("send-rep packet %3u of %u" % (i+1, rep))
        ret = myModem.send(src=0, dst=dst, type=pkttype, status=0, dsn=(i%256),
                           payload=data.encode('ascii', 'ignore'))
        if ret != 0:
            return -1

    sigInt_enable()

    return 0


def doSpreadCode(inp):
    """Set up spread-code."""
    length = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        length = int(param[0])
    return myModem.spreadCode(length)


def doSyncLen(inp):
    """Get/Set sync/preamble length."""
    length = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        length = int(param[0])

    return myModem.syncLen(length)


def doTestFreq(inp):
    """Test single frequency."""
    freq_idx = None
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) < 1 or len(param) > 2 :
            return -1
        freq_idx = int(param[0])
        freq_lvl = 0
        if (len(param) == 2) :
          freq_lvl = min(int(param[1]), 100)

    return myModem.testFreq(freq_idx, freq_lvl)


def doTestSweep(inp):
    """Test frequency sweep."""
    gc  = False
    gap = 0
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) < 0 or len(param) > 2 :
            return -1

        gc = param[0] == 'True' or param[0] == 'true' #or isint(param[0]) != 0
        if len(param) > 1 :
            gap = int(param[1])

    return myModem.testSweep(gc, gap)


def doTestNoise(inp):
    """Test noise (white noise in comm band) output."""
    gc   = False
    step = 1
    dur  = 1
    if len(inp) > 1:
        param = inp[1].split(' ')
        if len(param) < 0 or len(param) > 3 :
            return -1

        gc = param[0] == 'True' or param[0] == 'true' #or int(param[0]) != 0
        if len(param) > 1 :
            gap = int(param[1])
        if len(param) > 2 :
            dur = int(param[2])

    return myModem.testNoise(gc, step, dur)


def doTxGain(inp):
    """Get/set Tx gain."""
    value = None
    if (len(inp) > 1):
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1

        value = int(param[0])

    return myModem.txGain(value)


def doWaitKey(inp):
    """Wait for input."""
    if len(inp) > 2:
        return -1

    match = ''
    if len(inp) == 2:
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
        match = param[0]

    if match == '':
        prompt = '\nwaiting - hit enter to continue ... '
    else:
        prompt = '\nwaiting - enter "%s" to continue ... ' % (match)
    while True:
        inp = input(prompt)
        if match == '' or match == inp:
            break

    return 0


def doVersion(inp):
    """Get/set modem id."""
    return myModem.getVersion()

##
# CTRL-C handler
##
sigIntEn = True
gIrq = False
def sigInt_handler(signal, frame):
    """Handle SIGINT (Ctrl+C)."""
    if sigIntEn:
        print('Received SIGINT, closing.')
        myModem.close()
        exit()
    
    else:
        global gIrq
        gIrq = True
        #sigIntEn = True
        

def sigInt_enable():
    global sigIntEn, gIrq
    sigIntEn = True
    gIrq = False


def sigInt_disable():
    global sigIntEn, gIrq
    sigIntEn = False
    gIrq = False


def sigInt_check():
    global gIrq
    if gIrq:
        sigInt_enable()
        return True
    return False


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
#     print("\nSubscriber: " + "0")
#     print("Connected with result code "+str(rc)+"\n")
 
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("test/greetings")
    #client.subscribe("test/info")
    client.subscribe("+/" + TOP_CMD + "/+/+")
    
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Will auto-reconnect")
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload) + "\n")
    
    if TOP_PORT in msg.topic:
        print("Asking for ports") 
        funPort(msg)
    
    if TOP_ID in msg.topic:
        print("Set/Get Modem ID")
        funId(msg)
        
    
    
def funPort(msg):
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
        myModem.addRxCallback(printRxRaw)
        print("Modem port is: " + ports[index])    
        
def funId(msg):
    if TOP_GET in msg.topic:
        print("Evaluation command ID")
        evalCommand(msg.payload.decode("utf-8"))
    elif TOP_SET in msg.topic:
        print("Setting Modem Id: " + str(msg.payload))
        #client.publish("cl1" + "/" + TOP_RESP + "/" + TOP_ID , myModem.id(str(msg.payload)))
    
def funCmd():
    print("Replace with your code")
    
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

def byteArray2HexString(byteArray):
    return "".join("%02X " % b for b in byteArray)

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

def printUsage(cmd):
    """Print usage of mosh."""
    if cmd in cmdList:
        print("USAGE: %s %s" % (cmd, cmdList[cmd]['param']))
    else:
        print("ERROR: no help available for unknown command")
    return

def printInp():
    print(inp[0])

def evalCommand(newCmd):
    inp = newCmd.strip()  # strip leading/trailing spaces
    inp = re.sub("\s{2,}", " ", inp)  # remove multiple spaces (make one)
    inp = inp.split(' ', 1)
    cmd = inp[0]
    print("Evaluate:" + cmd)

    if (len(cmd) > 0 and cmd[0] != '#'):
        if cmd == 'exit' or cmd == 'quit':
            # rxThread.join()
            myModem.close()
            exit()

        elif cmd == 'help':
            if len(inp) == 1:
                print("\navailable commands:\n")
                for c in sorted(cmdList):
                    print("  " + c)
            elif len(inp) == 2:
                printUsage(inp[1])
            else:
                print("ERROR: invalid call of \"help\"")

        elif cmd == 'logon':
            doLogOpen(inp)

        elif cmd == 'logoff':
            doLogClose()

        elif cmd == 'run':
            doRun(inp)

        elif cmd == 'pause':
            doPause(inp)

        elif cmd == 'waitkey':
            doWaitKey(inp)

        else:
            if cmd in cmdList:
                try:
                    ret = eval(cmdList[cmd]['func'])(inp)
                except ValueError:
                    # not the best error handling but better than what we had before
                    # (at least no crash)
                    print("ERROR: Could not parse one of the parameters")

                if ret != 0:
                    print("ERROR: improper parameter list!")
                    printUsage(inp[0])

                if runFile:
                    # HACK sleep shortly to wait for reply
                    # before executing next command
                    time.sleep(0.1)
                else:
                    # HACK sleep shortly to show rx
                    # after rx without new prompt
                    time.sleep(0.01)
            else:
                print("ERROR: unknown command ")


# Create an MQTT client and attach our routines to it.
brokerAddress = "192.168.57.240"

TOP_CMD = "cmd"
TOP_RESP = "resp"

TOP_SET = "set"
TOP_GET = "get"

TOP_PORT = "port"
TOP_ID = "id"


USERNAME = "username"
PASSWORD = "password"

PORT_ADDRESS = 1883
KEEP_ALIVE_TIME = 60

#client_id = getserial()
client_id = "23444"
client = mqtt.Client(client_id)

ports = []
for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
    ports.append(port)

print("Port:" + ports[0])
#global myModem
myModem = modem.Modem(ports[0])
myModem.addRxCallback(printRxRaw)

global inp

def main():

    client.on_connect = on_connect
    client.on_message = on_message
     
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(brokerAddress, PORT_ADDRESS, KEEP_ALIVE_TIME)
    

    client.loop_forever()
     
    # Process network traffic and dispatch callbacks. This will also handle
    # reconnecting. Check the documentation at
    # https://github.com/eclipse/paho.mqtt.python
    # for information on how to use other loop*() functions
    
if __name__ == "__main__":
    main()