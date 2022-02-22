import os.path
import datetime as dt
import re
import collections
from configparser import ConfigParser
import shutil


class ExperimentsHandler(object):
    """Manage saving and loading of Range and PRR experiments from file system"""
    
    PARAM_FILE_NAME = "params.txt"
    
    KEY_BASIC_TEST = 'BasicTest'
    KEY_TIME = 'time'
    KEY_AGC = 'testAgc'
    KEY_PKT_CNT = 'pktCount'
    KEY_TX_GAIN = 'txGain'
    KEY_RX_GAIN = 'rxGain'
    KEY_SLEEP_TIME = 'sleepTime'
    KEY_SPREAD_LEN = 'spreadLen'
    
    
    KEY_BASIC = 'basic'
    
    KEY_PRR_TEST = 'PrrTest'
    KEY_PAYLOAD_LEN = 'payloadLen'
    KEY_PKT_TYPE = 'pktType'
    
    KEY_RNG_TEST = 'RangeTest'
    KEY_RNG_DELAY = 'rangeDelay'
    KEY_SOUND_SPEED = 'soundSpeed'
    
    KEY_PARAMS = 'Parameters'
    
    # Common test configurations for both PRR and Range testing
    BasicTest = collections.namedtuple(
        KEY_BASIC_TEST,
         [KEY_TIME, KEY_AGC, KEY_PKT_CNT, KEY_TX_GAIN, KEY_RX_GAIN,
            KEY_SLEEP_TIME, KEY_SPREAD_LEN]
         )
    
    # Test configurations for PRR testing
    PrrTest = collections.namedtuple(
        KEY_PRR_TEST,
         [KEY_BASIC, KEY_PAYLOAD_LEN, KEY_PKT_TYPE]
         )
    
    # Test configurations for Range Testing
    RangeTest = collections.namedtuple(
        KEY_RNG_TEST,
         [KEY_BASIC, KEY_RNG_DELAY, KEY_SOUND_SPEED]
         )
    
    def __init__(self, rootPath):
        expPath = os.path.join(rootPath,"data")
        self.prrPath = os.path.join(expPath, "prr")     # Path where PRR experiment data is stored
        self.rangePath = os.path.join(expPath, "range") # Path where Range experiment data is stored
        self.confParser = ConfigParser()       
        
    def saveExperiment(self, expData, expType, expName = None):
        """Save an experiment to params.txt file in experiment's directory"""
        self.confParser.remove_section(self.KEY_PARAMS)
        self.confParser.add_section(self.KEY_PARAMS)
        
        self.confParser.set(self.KEY_PARAMS, self.KEY_TIME, expData.basic.time)
        self.confParser.set(self.KEY_PARAMS, self.KEY_AGC, str(expData.basic.testAgc))
        self.confParser.set(self.KEY_PARAMS, self.KEY_PKT_CNT, str(expData.basic.pktCount))
        self.confParser.set(self.KEY_PARAMS, self.KEY_TX_GAIN, cleanCSVStr(expData.basic.txGain))
        self.confParser.set(self.KEY_PARAMS, self.KEY_RX_GAIN, cleanCSVStr(expData.basic.rxGain))
        self.confParser.set(self.KEY_PARAMS, self.KEY_SLEEP_TIME, str(expData.basic.sleepTime))
        self.confParser.set(self.KEY_PARAMS, self.KEY_SPREAD_LEN, cleanCSVStr(expData.basic.spreadLen))
        
        filePath = None
        
        if expType == self.KEY_PRR_TEST:
            self.confParser.set(self.KEY_PARAMS, self.KEY_PAYLOAD_LEN, cleanCSVStr(expData.payloadLen))
            self.confParser.set(self.KEY_PARAMS, self.KEY_PKT_TYPE, expData.pktType)
            filePath = self.prrPath
        elif expType == self.KEY_RNG_TEST:
            self.confParser.set(self.KEY_PARAMS, self.KEY_RNG_DELAY, str(expData.rangeDelay))
            self.confParser.set(self.KEY_PARAMS, self.KEY_SOUND_SPEED, str(expData.soundSpeed))
            filePath = self.rangePath
        else:
            return None
        
        if expName is None:
            newExpName = expData.basic.time
        else:
            newExpName = expName
        
        filePath = os.path.join(filePath, newExpName)
        
        if not os.path.exists(filePath):
            os.makedirs(filePath)
            
#         print("File path: " + filePath)
#         print("File name: " + extFileName)
        
        targetFile = os.path.join(filePath, self.PARAM_FILE_NAME)
        with open(targetFile, 'w') as Configfile:
            self.confParser.write(Configfile)
            
        return newExpName
    
    
    def readExperiment(self, expName, expType):
        """Read experiment from params file and return it in form of test configurations"""
        self.confParser.remove_section(self.KEY_PARAMS)
        
        expPath = None
        if expType == self.KEY_PRR_TEST:
            expPath = self.prrPath
        else:
            expPath = self.rangePath
        
        name = os.path.join(expPath, expName, self.PARAM_FILE_NAME)
        
#         if not name.lower().endswith(".txt"):
#             name = name + ".txt"
#         print("Read Filename: " + name)
#         print(name)
        self.confParser.read(name)
        
        basicTest = self.BasicTest(
            self.confParser.get(self.KEY_PARAMS, self.KEY_TIME),
            int(self.confParser.get(self.KEY_PARAMS, self.KEY_AGC)),
            int(self.confParser.get(self.KEY_PARAMS, self.KEY_PKT_CNT)),
            self.confParser.get(self.KEY_PARAMS, self.KEY_TX_GAIN),
            self.confParser.get(self.KEY_PARAMS, self.KEY_RX_GAIN),
            float(self.confParser.get(self.KEY_PARAMS, self.KEY_SLEEP_TIME)),
            self.confParser.get(self.KEY_PARAMS, self.KEY_SPREAD_LEN)
            )
        
        if expType == self.KEY_PRR_TEST:
            return self.PrrTest(
                basicTest, 
                self.confParser.get(self.KEY_PARAMS, self.KEY_PAYLOAD_LEN),
                self.confParser.get(self.KEY_PARAMS, self.KEY_PKT_TYPE)
                )
        elif expType == self.KEY_RNG_TEST:
            return self.RangeTest(
                basicTest, 
                self.confParser.get(self.KEY_PARAMS, self.KEY_RNG_DELAY),
                float(self.confParser.get(self.KEY_PARAMS, self.KEY_SOUND_SPEED))
                )
            
        return None
        
        
    def deleteExp(self, expName, expType):
        """Delete an experiment from file system"""
        expPath = None
        if expType == self.KEY_PRR_TEST:
            expPath = self.prrPath
        else:
            expPath = self.rangePath
        
        name = os.path.join(expPath, expName)
        
#         if not name.lower().endswith(".txt"):
#             name = name + ".txt"
#         os.remove(name)
        if os.path.exists(name):
            try:
                shutil.rmtree(name)
            except Exception as e:
                print("Failed to delete experiment: " + str(e))
        

    def getAllExpFiles(self, expType):  # Deprecated
        """Get a list of all saved experiments files of particular type (PRR or Range)"""
        files = []
        expPath = None
        if expType == self.KEY_PRR_TEST:
            expPath = self.prrPath
        else:
            expPath = self.rangePath
             
        for _r, _d,f in os.walk(expPath):
            for file in f:
                if '.txt' in file:
                    fileName, _fileExtension = os.path.splitext(file)
                    #files.append(os.path.join(r,file)) #to show with full path
                    files.append(fileName)
                     
        return files
     
    
    def getAllExpDirs(self, expType):
        """Get a list of all saved experiments of particular type (PRR or Range)"""
        expPath = None
        retDirs = []
        if expType == self.KEY_PRR_TEST:
            expPath = self.prrPath
        else:
            expPath = self.rangePath
            
        if not os.path.exists(expPath):
            os.makedirs(expPath)
        
        currDirs = os.listdir(expPath)
            
        for currDir in currDirs:
            
            filePath = os.path.join(expPath, currDir, self.PARAM_FILE_NAME)
#             print(filePath)
            if os.path.isfile(filePath):
                retDirs.append(currDir)
            else:
                self.deleteExp(currDir, expType)
            
        return retDirs
    
    def getAllResFiles(self, expName, expType):
        """Returns the saved result files of an experiment of particular type"""
        if expType == self.KEY_PRR_TEST:
            expPath = self.prrPath
        else:
            expPath = self.rangePath
        
        resPath = os.path.join(expPath, expName, "results")
        files = []
        for _r, _d, f in os.walk(resPath):
            for file in f:
                if '.pkl' in file:
                    fileName, _fileExtension = os.path.splitext(file)
                    files.append(fileName)
         
        files.sort(reverse=True)       
        return files
            
    
    def __createBasicTest(self, testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen):
        """Create common test configurations of PRR and Range test"""
        return self.BasicTest(getNow(), testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen)
    
    def createPrrTest(self, testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen, payloadLen, pktType):
        """Create PRR test configurations"""
        return self.PrrTest(
            self.__createBasicTest(testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen),
            payloadLen, pktType
            )
        
    def createRangeTest(self, testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen, rangeDelay, soundSpeed):
        """Create Range test configurations"""
        return self.RangeTest(
            self.__createBasicTest(testAgc, pktCount, txGain, rxGain, sleepTime, spreadLen),
            rangeDelay, soundSpeed
            )
    
def getNow():
    """Returns current time"""
    return dt.datetime.now().strftime("%Y-%m-%d(%H.%M.%S)")

def strToIntList(inpStr):
    """Converts string of comma separated integers to list"""
    result = re.findall(r"\d+", inpStr)
    numbers = [int(x) for x in result]
    return numbers

def cleanCSVStr(inpStr):
    """Give proper spacing and commas to user input comma separated integers string"""
    mList = re.findall(r"\d+", inpStr)
    return ', '.join(mList)

def strToFloatList(inpStr):
    """Converts string of comma separated floats to list"""
    return list(map(float, inpStr.split(',')))