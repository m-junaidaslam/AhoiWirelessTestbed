#! /usr/bin/env python3
"""A."""
import time
import configparser
import os
import modem
from serial.tools.list_ports import comports
import time
import sys
import string

# from packet import getBytes
from packet import getHeaderBytes
from packet import getFooterBytes


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


def askForComPort():
    """Ask user for com port to use."""
    sys.stdout.write("Available Ports:\n")
    ports = []
    for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
        sys.stdout.write("{:2}: {:20} \n".format(n, port))
        ports.append(port)
    while True:
        port = input("Enter port index: ")
        try:
            index = int(port) - 1
            if not 0 <= index < len(ports):
                raise ValueError
        except ValueError:
            sys.stdout.write("Invalid port selected\n")
            continue
        else:
            port = ports[index]
        return port


#def startTest(modem, role, src, pktcount, payload, s0, s1, sleepTime, pktType, txGain, distance):
def startTest(modem, role, dst, pktcount, payload, rxg, sleepTime, pktType, txGain, spread):
    """Start a single test."""
    #filename = "{}_".format(time.strftime("%d%m%Y-%H%M%S"))
    
    # prepare file name
    filename = ""
    #filename += "id{:03d}_".format(src)
    filename += "{}_".format(role)
    filename += "pkt-{:04d}_".format(pktcount)
    filename += "pay-{:03d}_".format(payload)
    if rxg is None:
        filename += "rxg-ac_"
    else:
        filename += "rxg-{:02d}_".format(rxg)
    filename += "txg-{:02d}_".format(txGain)
    filename += "fs-{:1d}".format(spread)
    filename += ".{}".format(time.strftime("%Y%m%d-%H%M%S"))
    filename += ".log"
    
    # FIXME wait time in modem calls

    modem.logOn(file_name=filename)
    
    modem.id()
    modem.getVersion()
    modem.getConfig()
    modem.spreadCode(spread)
    modem.rangeDelay()
    modem.txGain(txGain)
    if rxg is None:
        modem.agc(1)
        modem.rxGain()
    else:
        modem.agc(0)
        #modem.rxGain(0, s0)
        modem.rxGain(1, rxg)  # HACK
    modem.clearPacketStat()
    modem.clearSyncStat()
    modem.clearSfdStat()
    # more stats
    modem.getPowerLevel()
    modem.rxThresh()
    modem.rxLevel()
    
    # run experiment after user OK
    if role == "tx":
        if dst is None :
            dst = "0xFF"
        input("RX ready?")
        for i in range(0, pktcount):
            data = bytes(os.urandom(payload))
            modem.send(src=0x00, dst=dst, payload=data, status=2, dsn= (i % 256), type=pktType)
            time.sleep(sleepTime)
        print("TX DONE!")
    else:
        input("TX done?")
    
    # stats
    modem.getPacketStat()
    modem.getSyncStat()
    modem.getSfdStat()
    modem.getPowerLevel()

    # finalize
    time.sleep(1)
    modem.logOff()



def main():
    dev = askForComPort()
    myModem = modem.Modem(dev)
    myModem.addRxCallback(printRxRaw)
    
    # open config
    testConfig = configparser.ConfigParser()
    testConfig.read('config.ini')
    
    # read config
    #role = testConfig['PARAMETERS'].getboolean('role')
    #if not role in ["tx", "rx"]:
    #    print("Ups, role '{}' is invalid. Aborting.".format(role))
    #    sys.exit(1)
    while True:
        role = input("Are you rx or tx:")
        if role in ["tx", "rx"]:
            print("Ok. You are {}.".format(role))
            break

    # read config
    testAgc    = testConfig['PARAMETERS'].getboolean('testAgc')
    pktCount   = testConfig['PARAMETERS'].getint('pktCount')
    pktType    = int(testConfig['PARAMETERS']['pktType'], 16)
    sleepTime  = testConfig['PARAMETERS'].getfloat('sleepTime')
    payloadLen = list(map(int, testConfig['PARAMETERS']['payloadLength']
                         .split(',')))
    #filterS0   = testConfig['PARAMETERS']['filterS0'].split(',')
    rxGain     = list(map(int, testConfig['PARAMETERS']['rxGain'].split(',')))
    txGain     = list(map(int, testConfig['PARAMETERS']['txGain'].split(',')))
    spreadLen  = list(map(int, testConfig['PARAMETERS']['spreadLength'].split(',')))
    
    #
    testIdx = 0
    sp = spreadLen;  # no array
    #for dst in dstList:
    for sp in spreadLen:
        for pl in payloadLen:
            for tx in txGain:
                if testAgc:
                    doTest = input("Do test #{} (pkts={},pay={},AGC,txgain={},spread={})? [Y/n/exit]"
                                   .format(testIdx, pktCount, pl, tx, sp))
                    if doTest.lower() == "exit":
                        myModem.close()
                        return
                    if doTest.lower() in ["n", "no", "nein"]:
                        print("Skip test #{}.".format(testIdx))
                    else:
                        startTest(modem=myModem, role=role, #dst=dst,
                                  pktcount=pktCount, payload=pl, rxg=None, sleepTime=sleepTime, pktType=pktType, txGain=tx, spread=sp)
                    testIdx = testIdx + 1
                for rxg in rxGain:
                    if rxg >= 0:
                        doTest = input("Do test #{} (pkts={},pay={},rxgain={},txgain={},spread={})? [Y/n/exit]"
                                       .format(testIdx, pktCount, pl, rxg, tx, sp))
                        if doTest.lower() == "exit":
                            myModem.close()
                            return
                        if doTest.lower() in ["n", "no", "nein"]:
                            print("Skip test #{}.".format(testIdx))
                        else:
                            startTest(modem=myModem, role=role, #dst=dst,
                                      pktcount=pktCount, payload=pl, rxg=rxg, sleepTime=sleepTime, pktType=pktType, txGain=tx, spread=sp)
                        testIdx = testIdx + 1

    myModem.close()


if __name__ == "__main__":
    main()
