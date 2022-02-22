#! /usr/bin/env python3

#
# Copyright 2016-2019
# 
# Bernd-Christian Renner, Jan Heitmann, and
# Hamburg University of Technology (TUHH).
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""This is Modem Shell (mosh)."""

from serial.tools.list_ports import comports
import sys
import signal
import re
import time
import string
# import binascii
import os.path
try:
    import readline
except ImportError:
    print("No readline found. Arrow keys eventually won't work.")

import modem

# from packet import getBytes
from packet import getHeaderBytes
from packet import getFooterBytes


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


def readInput():
    """Read input from console."""
    global runFile
    global prompted

    if (runFile):
        inp = runFile.readline()

        if (len(inp) > 0):
            inp = inp.rstrip('\n')
            print('\nmosh@%s >> %s (from "%s")' % (dev, inp, runFileName))
        else:
            runFile.close()
            runFile = False

    if (not runFile):
        prompted = True
        inp = input("\nmosh@%s >> " % (dev))
        prompted = False

    return inp

    # try:
    #     value = raw_input()
    #     do_stuff(value) # next line was found
    # except (EOFError):
    #     break #end of file reached


def printUsage(cmd):
    """Print usage of mosh."""
    if cmd in cmdList:
        print("USAGE: %s %s" % (cmd, cmdList[cmd]['param']))
    else:
        print("ERROR: no help available for unknown command")
    return


def askForComPort():
    """Ask user for com port to use."""
    sys.stdout.write("Available Ports:\n")
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
        sys.stdout.write("{:2}: {:20} \n".format(n, port))
        ports.append(port)
        
    if len(ports) == 0:
        print("ERROR: no serial port available")
        exit()
        
    while True:
        port = input("Enter port index (0 to abort): ")
        try:
            index = int(port) - 1
            if index < 0:
                sys.stdout.write("Bye bye\n")
                exit()
            if not 0 <= index < len(ports):
                raise ValueError
        except ValueError:
            sys.stdout.write("Invalid port selected\n")
            continue
        else:
            port = ports[index]
        return port


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigInt_handler)
    # print('Press Ctrl+C')
    # signal.pause()

    ##
    # process command lines arguments
    ##

    if len(sys.argv) > 1:
        dev = sys.argv[1]
    else:
        dev = askForComPort()

    # print "mosh@%s" % (dev)

    # serial port config
    # configure the serial connections
    # (the parameters differs on the device you are connecting to)

    # rxThread = threading.Thread(receivePacket)
    # rxThread.start()
    # doLog = False
    # serConn.open()
    # ser.isOpen()
    # ##
    # cmd shell part
    ##
    print("\nEnter your commands below.\r\n"
          "Type \"help\" for a list of commands, type \"exit\" to leave"
          )

    # input = 1
    myModem = modem.Modem(dev)
    myModem.addRxCallback(printRxRaw)

    while True:
        # get keyboard input (blocking)

        # TODO read from file if provided via run command

        inp = readInput()

        # split input into command and params
        inp = inp.strip()  # strip leading/trailing spaces
        inp = re.sub("\s{2,}", " ", inp)  # remove multiple spaces (make one)
        inp = inp.split(' ', 1)
        cmd = inp[0]

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

# eof
