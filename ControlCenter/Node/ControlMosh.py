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

import time
import os.path

class ControlMosh:
    """
    
    """
    
#     logPath = os.path.join(os.path.dirname(os.getcwd()), "data", "mosh")
    
    def __init__(self, rootPath, ctrlCHandler):
        """Initialize modem."""
        print("Mosh initialized")
        self.logPath = os.path.join(rootPath, "data", "mosh")
        print("ControlMosh rp: {}".format(self.logPath))
        self.moshEnabled = False
        self.ctrlCHandler = ctrlCHandler
        
        # run commands from file (batch mode)
        self.runFile = False
        self.runFileName = ''
        self.rxForward = None
        
        
    def setRxForward(self, rxF):
        self.rxForward = rxF
    
    def start(self, myModem):
        self.moshEnabled = True
        self.myModem = myModem
        print("modem rx call back added")
        self.myModem.addRxCallback(self.rxCallBack)
        
    def stop(self):
        self.moshEnabled = False
        print("Mosh: Remove modem call back")
        self.myModem.close()
        self.myModem.removeRxCallback(self.rxCallBack)
    
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
    
    
    def doSniffingMode(self, inp):
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
        return self.myModem.sniffingMode(sniffing)
    
    def doAgc(self, inp):
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
    
        return self.myModem.agc(agc_status)
    
    
    def doBatVol(self, inp):
        """Get Battery Voltage."""
        return self.myModem.getBatVoltage()
    
    
    def doBootloader(self, inp):
        """Reset uC and start Bootloader."""
        return self.myModem.startBootloader()
    
    
    def doDistance(self, inp):
        """Get stored distance."""
        id = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
            id = int(param[0])
        return self.myModem.getDistanceTo(id)
    
    
    def doRxGain(self, inp):
        """Get/Set rx gain level."""
        stage = None
        level = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 2:
                return -1
    
            stage = int(param[0])
            level = int(param[1])
        return self.myModem.rxGain(stage, level)
    
    
    def doPeakWinLen(self, inp):
        """Get/set peak window length."""
        winlen = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
            winlen = int(float(param[0]) * 1000)
        return self.myModem.peakWinLen(winlen)
    
    
    def doTransducer(self, inp):
        """Get/set transducer type."""
        t = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
            t = int(param[0])
        return self.myModem.transducer(t)
    
    
    def doConfig(self, inp):
        """Get modem config."""
        return self.myModem.getConfig()
    
    
    def doFilterRaw(self, inp):
        """Get/Set rx gain."""
        stage = None
        level = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 2:
                return -1
    
            stage = int(param[0])
            level = param[1]
        return self.myModem.filterRaw(stage, level)
    
    
    def doFreqBands(self, inp):
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
    
        return self.myModem.freqBands()
    
    
    def doFreqBandsNum(self, inp):
        """Get/Set freq bands num."""
        num = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            num = int(param[0])
    
        return self.myModem.freqBandsNum(num)
    
    
    def doFreqCarriers(self, inp):
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
    
        return self.myModem.freqCarriers()
    
    
    def doFreqCarriersNum(self, inp):
        """Get/Set freq carrier num."""
        num = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            num = int(param[0])
        return self.myModem.freqCarrierNum(num)
    
    
    def doId(self, inp):
        """Get/Set modem id."""
        modem_id = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
            modem_id = int(param[0])
        return self.myModem.id(modem_id)
    
    
    def doLogOpen(self, inp):
        """Open Log file."""
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
        return self.myModem.logOn(self.logPath, param[0])
    
    
    def doLogClose(self):
        """Close log file."""
        self.myModem.logOff()
        return 0
    
    
    def doPacketStat(self, inp):
        """Get packet stats."""
        return self.myModem.getPacketStat()
    
    
    def doPacketStatClear(self, inp):
        """Clear packet stat."""
        return self.myModem.clearPacketStat()
    
    
    def doSyncStat(self, inp):
        """Get sync stats."""
        return self.myModem.getSyncStat()
    
    
    def doSyncStatClear(self, inp):
        """Clear sync stat."""
        return self.myModem.clearSyncStat()
    
    def doSfdStat(self, inp):
        """Get sfd stats."""
        return self.myModem.getSfdStat()
    
    
    def doSfdStatClear(self, inp):
        """Clear sfd stat."""
        return self.myModem.clearSfdStat()
    
    def doAllStat(self, inp):
        """Get al tx/rx stats."""
        return self.myModem.getAllStat()
    
    
    def doAllStatClear(self, inp):
        """Clear all tx/rx stat."""
        return self.myModem.clearAllStat()
    
    def doPause(self, inp):
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
    
    
    def doPowerLevel(self, inp):
        """Get power level."""
        return self.myModem.getPowerLevel()
    
    
    def doRun(self, inp):
        """Run script from file."""
    
        if len(inp) != 2:
            return -1
    
        param = inp[1].split(' ')
        if len(param) != 1:
            return -1
    
        self.runFileName = param[0]
        if (os.path.isfile(self.runFileName)):
            self.runFile = open(self.runFileName, 'r')
            print("running commands from \"%s\"" % self.runFileName)
            return 0
    
        else:
            print("file \"%s\" does not exist" % self.runFileName)
            return 1
    
    
    def doRxLevel(self, inp):
        """Get Rx threshold level."""
        return self.myModem.rxLevel()
    
    
    def doRxThresh(self, inp):
        """Set up rx threshold."""
        thresh = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            thresh = int(param[0])
        return self.myModem.rxThresh(thresh)
    
    
    def doRange(self, inp):
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
        self.ctrlCHandler.sigInt_disable()
        for i in range(0, rep):
            if self.ctrlCHandler.sigInt_check():
                return 0
            
            if i > 0:
                time.sleep(delay)
    
            # appendable data (debugging, testing, etc.)
            # for c in '01234567012345670123456701234567' :
            # hexdata += ('\\x%x' % ord(c))
            # 'R' == 0x52 ;-)
            ret = self.myModem.send(type=0x52, dst=dst, src=0, dsn=(i%256), status=2, payload=data)
            if ret != 0:
                return -1
    
        self.ctrlCHandler.sigInt_enable()
    
        return 0
    
    
    def doRangeDelay(self, inp):
        """Set delay for range answer."""
        delay = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if(len(param) != 1):
                return -1
            delay = int(param[0])
        return self.myModem.rangeDelay(delay)
    
    
    def doReset(self, inp):
        """Reset the modem."""
        return self.myModem.reset()
    
    
    def doSample(self, inp):
        """Get samples."""
        if (len(inp) < 2):
            return -1
    
        param = inp[1].split(' ')
        if (len(param) < 3):
            return -1
    
        trig = int(param[0])
        num = int(param[1])
        post = int(param[2])
        return self.myModem.sample(trig, num, post)
    
    
    def doSend(self, inp):
        """Send a packet."""
        
        print("Send: {}".format([inp]))
        
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
        print("doSend")
        return self.myModem.send(src=0, dst=dst, type=pkttype, status=ack,
                            payload=data.encode('ascii', 'ignore'))
        # return sendPacket(pkttype, bytearray(data, 'ascii'))
    
    
    def doSendRep(self, inp):
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
        self.ctrlCHandler.sigInt_disable()
        for i in range(0, rep):
            if self.ctrlCHandler.sigInt_check():
                return 0
            
            if i > 0:
                time.sleep(delay)
    
            # seqno = "\\x%02x" % (i)
    
            print("send-rep packet %3u of %u" % (i+1, rep))
            ret = self.myModem.send(src=0, dst=dst, type=pkttype, status=0, dsn=(i%256),
                               payload=data.encode('ascii', 'ignore'))
            if ret != 0:
                return -1
    
        self.ctrlCHandler.sigInt_enable()
    
        return 0
    
    
    def doSpreadCode(self, inp):
        """Set up spread-code."""
        length = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            length = int(param[0])
        return self.myModem.spreadCode(length)
    
    
    def doSyncLen(self, inp):
        """Get/Set sync/preamble length."""
        length = None
        if len(inp) > 1:
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            length = int(param[0])
    
        return self.myModem.syncLen(length)
    
    
    def doTestFreq(self, inp):
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
    
        return self.myModem.testFreq(freq_idx, freq_lvl)
    
    
    def doTestSweep(self, inp):
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
    
        return self.myModem.testSweep(gc, gap)
    
    
    def doTestNoise(self, inp):
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
    
        return self.myModem.testNoise(gc, step, dur)
    
    
    def doTxGain(self, inp):
        """Get/set Tx gain."""
        value = None
        if (len(inp) > 1):
            param = inp[1].split(' ')
            if len(param) != 1:
                return -1
    
            value = int(param[0])
    
        return self.myModem.txGain(value)
    
    
    def doWaitKey(self, inp):
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
    
    
    def doVersion(self, inp):
        """Get/set modem id."""
        return self.myModem.getVersion()
    
    
    def readInput(self):
        """Read input from console."""
     
        if (self.runFile):
            inp = self.runFile.readline()
     
            if (len(inp) > 0):
                inp = inp.rstrip('\n')
                print('\nmosh@%s >> %s (from "%s")' % (self.myModem.nodeId, inp, self.runFileName))
            else:
                self.runFile.close()
                self.runFile = False
     
        if (not self.runFile):
            inp = input("\nmosh@%s >> " % (self.myModem.nodeId))
     
        return inp
    
        # try:
        #     value = raw_input()
        #     do_stuff(value) # next line was found
        # except (EOFError):
        #     break #end of file reached
    
    def rxCallBack(self, rxNode, pkt):
#         print("Mosh rx call back with id: " + rxNode.nodeId)
        if rxNode.nodeId == self.myModem.nodeId:
#             print("Mosh packet received: " + rxNode.nodeId)
            self.rxForward(rxNode.nodeId, pkt)
            
    def evalCmd(self, cmd, inp):
        ret = eval("self." + self.cmdList[cmd]['func'])(inp)
        return ret
