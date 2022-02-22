'''
Created on Jul 9, 2019

@author: junai
'''

import os
import pickle
from ControlCenter.Evaluation.ExperimentsHandler import ExperimentsHandler

class ResultsHandler(object):
    '''
    classdocs
    '''
    
    def __init__(self, rootPath, expsType):
        '''
        Constructor
        '''
        if expsType == ExperimentsHandler.KEY_PRR_TEST:
            self.expPath = os.path.join(rootPath, "data", "prr")
        elif expsType == ExperimentsHandler.KEY_RNG_TEST:
            self.expPath = os.path.join(rootPath, "data", "range")
        
    def saveResult(self, expName, saveName, figs):
        dictFigs = dict()
        resPath = os.path.join(self.expPath, expName, "results")
        if not os.path.exists(resPath):
            os.makedirs(resPath)
        pklFilePath = os.path.join(resPath, saveName + ".pkl")
        pklFile = open(pklFilePath, 'wb')
        i = 0
        for fig in figs:
            dictFigs["fig"+str(i)] = fig
            i += 1
            
        pickle.dump(dictFigs, pklFile)
        pklFile.close()
        
        
    def getResFigs(self, expName, resFile):    
        resPath = os.path.join(self.expPath, expName, "results", resFile + ".pkl")        
        dictFigs = None
        figs = []
        if os.path.isfile(resPath):
            dataFile = open(resPath, 'rb')
            dictFigs = pickle.load(dataFile)
            dataFile.close()
            
        if dictFigs is not None:
            for _key, value in dictFigs.items():
                figs.append(value)
            
        return figs      
    
    def deleteResult(self, expName, resFile):
        resPath = os.path.join(self.expPath, expName, "results", resFile + ".pkl")  
        if os.path.exists(resPath):
            os.remove(resPath)
            return True
        else:
            print('File does not exists')
            return False
        
    def renameResult(self, expName, resFile, newResFile):
        resPath = os.path.join(self.expPath, expName, "results", resFile + ".pkl")
        newResPath = os.path.join(self.expPath, expName, "results", newResFile + ".pkl")
        if os.path.exists(resPath):
            os.rename(resPath, newResPath)
            return True
        else:
            print('File does not exists')
            return False
    