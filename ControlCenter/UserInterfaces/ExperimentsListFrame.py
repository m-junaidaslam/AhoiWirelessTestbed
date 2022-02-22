'''
Created on Jun 18, 2019

@author: junai
'''

from tkinter import Frame, Scrollbar, VERTICAL, RIGHT, LEFT, X, Y, Canvas, BOTH, NW, Button, TOP, SUNKEN
from ControlCenter.UserInterfaces import ExperimentUi
from ControlCenter.UserInterfaces.DialogUtilities import SelTxRxDialog, showInfoMessage, SelPrrParams, SelRangeParams, SelResultDialog
from ControlCenter.UserInterfaces import PrrEvaluationGUI, RangeEvaluationGUI
from ControlCenter.Evaluation import ResultsHandler

class ExperimentsListFrame(Frame):
    
    def __init__(self, master, rootPath, expsType, expHandler, nodesManager, mWhSupport):
        super().__init__(master=master)
        self.rootPath = rootPath
        self.expHandler = expHandler
        self.expsType = expsType
        self.nodesManager = nodesManager
        self.expUis = []
        self.mWhSupport = mWhSupport
        self.resHandler = ResultsHandler.ResultsHandler(rootPath, expsType)
        
        self.config(background="gray", height=2, bd=2, relief=SUNKEN)
        
        frameButtons = Frame(self)
        
        self.btnNew = Button(
            master=frameButtons, text="New " + self.expsType, foreground="white", background='cadetblue',
             command=self.startExp, font=('Helvetica', '16', 'bold'), borderwidth=4, relief="raised")
        self.btnNew.pack(side=LEFT, fill=X, expand=True, padx=3, pady=3)
        
        
        self.btnRefresh = Button(
            master=frameButtons, text="Refresh", foreground="white", background='cadetblue',
             command=self.createList, font=('Helvetica', '16', 'bold'), borderwidth=4, relief="raised")
        self.btnRefresh.pack(side=RIGHT, fill=X, expand=True, padx=3, pady=3)
        
        frameButtons.pack(side=TOP, fill=X, padx=1, pady=5)
        
        self.canvas = Canvas(self, bg='gray')
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        yscroll = Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
                
        self.canvas['yscrollcommand'] = yscroll.set
        
#         self.canvas.bind("<MouseWheel>", self._onMousewheel)
        
        mWhSupport.add_support_to(self.canvas, yscrollbar=yscroll, what="pages")
        
        self.canvas.bind("<Button-4>", self._onMousewheel)
        self.canvas.bind("<Button-5>", self._onMousewheel)
        
        self.listFrame = Frame(self.canvas, background="#b22222")
        self.listFrameId = self.canvas.create_window((0, 0), window=self.listFrame, anchor=NW) # Canvas equivalent of pack()
        
        self.listFrame.bind("<Configure>", self._onFrameConfigure)
        self.canvas.bind('<Configure>', self._onFrameSize)
        self.listFrame.bind("<MouseWheel>", self._onMousewheel)
        
        yscroll.pack(side=RIGHT, fill=Y)

        self.createList()
        
        
    def _onFrameConfigure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _onMousewheel(self, event):
        self.canvas.yview_scroll(-1*(int(event.delta/120)), "units")
        
    def _onFrameSize(self, event):
        canvasWidth = event.width
        self.canvas.itemconfig(self.listFrameId, width=canvasWidth)
            
    def startExp(self, expName=None, expData=None):
        txNodeIds, rxNodeIds = self.getTxRxNodesDialog()
                    
        if (txNodeIds is not None) and (rxNodeIds is not None):
            txNodes = self.nodesManager.getNodesByIds(txNodeIds)
            rxNodes = self.nodesManager.getNodesByIds(rxNodeIds)
            newExpName = expName
            newExpData = expData
            if (newExpName is None) or (newExpData is None):
                lastExpName = None
                if self.expUis:
                    lastExpName = self.expUis[0].expName
                newExpName, newExpData = self.getParamasDialog(lastExpName)
            
            if (newExpName is not None) and (newExpData is not None):
                if self.expsType == self.expHandler.KEY_PRR_TEST:
                    PrrEvaluationGUI.PrrEvaluationGUI(
                        parent=self.master, 
                        rootPath=self.rootPath, 
                        expName=newExpName, 
                        runExp=True, 
                        mWhSupport=self.mWhSupport, 
                        resHandler=self.resHandler, 
                        txNodes=txNodes, 
                        rxNodes=rxNodes, 
                        expData=newExpData
                        )
                    
                elif self.expsType == self.expHandler.KEY_RNG_TEST:
                    RangeEvaluationGUI.RangeEvaluationGUI(
                        parent=self.master, 
                        rootPath=self.rootPath, 
                        expName=newExpName, 
                        runExp=True, 
                        resHandler=self.resHandler, 
                        mWhSupport=self.mWhSupport, 
                        txNodes=txNodes, 
                        rxNodes=rxNodes, 
                        expData=newExpData
                        )
                                        

    def showExpResults(self, expName):
        resFiles = self.expHandler.getAllResFiles(expName, self.expsType)
        
        if resFiles:
            resDiag = SelResultDialog(self.master, resFiles, expName, self.resHandler.deleteResult, self.resHandler.renameResult)
            
            if resDiag.result is not None:
                if self.expsType == self.expHandler.KEY_PRR_TEST:
                    evaPrrResGui = PrrEvaluationGUI.PrrEvaluationGUI(
                        parent=self.master, 
                        rootPath=self.rootPath, 
                        expName=expName, 
                        runExp=False, 
                        mWhSupport=self.mWhSupport, 
                        resHandler=self.resHandler, 
                        txNodes=None, 
                        rxNodes=None, 
                        expData=None
                        )
                    evaPrrResGui.loadResult(resDiag.result)
                else:
                    evaRngResGui = RangeEvaluationGUI.RangeEvaluationGUI(
                        parent=self.master, 
                        rootPath=self.rootPath, 
                        expName=expName, 
                        runExp=False, 
                        mWhSupport=self.mWhSupport, 
                        resHandler=self.resHandler, 
                        txNodes=None, 
                        rxNodes=None, 
                        expData=None)
                    evaRngResGui.loadResult(resDiag.result)
        else:
            showInfoMessage(expName, "No saved results found!")
            
                    
    def getParamasDialog(self, lastExpName=None, editExp=False):
        dia = None
        if editExp:
            expName = lastExpName
        else:
            expName = "New"
        if self.expsType == self.expHandler.KEY_PRR_TEST:
            dia = SelPrrParams(self, "PRR: " + expName, self.expHandler, lastExpName, editExp)
            
        elif self.expsType == self.expHandler.KEY_RNG_TEST:
            dia = SelRangeParams(self, "Range: " + expName, self.expHandler, lastExpName, editExp)
            
        self.createList()
            
        return dia.name, dia.result
                
    def getTxRxNodesDialog(self):
        txNodes = None
        rxNodes = None
        
        while True:
            txNodes = None
            rxNodes = None
            selTxRxDia = SelTxRxDialog(self, "Select Modems", self.nodesManager.nodes, self.mWhSupport)
            if (not selTxRxDia.resTxNodes) or (not selTxRxDia.resRxNodes):
                break
            else:
                txNodes = selTxRxDia.resTxNodes
                rxNodes = selTxRxDia.resRxNodes
                
                if txNodes and rxNodes:
                    if (len(txNodes) != 1) or (len(rxNodes) != 1):
                        break
                    else:
                        if txNodes[0] != rxNodes[0]:
                            break
                        else:
                            showInfoMessage("Operation Failed", "Sending and receiving modems should be different!")
                    
                else:
                    showInfoMessage("Operation Failed", "At least one node should be selected for transmission and reception!")
        
        return txNodes, rxNodes
    
    def createList(self):
#         print("Create NodesListFrame")
        self.destroyList()
        allExpNames = self.expHandler.getAllExpDirs(self.expsType)
        allExps = []
        for expName in allExpNames:
#             print(expName)
            allExps.append(self.expHandler.readExperiment(expName, self.expsType))
        
        if allExps:
            zipNamesExps = self.zipAndSort(allExpNames, allExps, True)
            
            for zips in zipNamesExps:
                self.appendList(zips[0], zips[1])
                
        else:
            showInfoMessage("Not Found", "No saved experiments")
            
    def appendList(self, newExpName, newExpData):
        expUi = ExperimentUi.ExperimentUi(
            self.listFrame, newExpName, self.expsType, newExpData, self.expHandler, 
            self.getParamasDialog, self.startExp, self.showExpResults
            )
        expUi.pack(fill='x', expand=True, padx=2, pady=2)
        self.expUis.append(expUi)        
        
    def zipAndSort(self, expNames, exps, reverse):
        zipExps = zip(expNames, exps)
        return sorted(zipExps, key=lambda pair: pair[1].basic.time, reverse=reverse)
        
    def sortByExpDates(self, expNames, exps, reverse):
        zipExps = zip(expNames, exps)
        sortZipExps = sorted(zipExps, key=lambda pair: pair[1].basic.time, reverse=reverse)
        tupleExps = list(zip(*sortZipExps))
        listSortExpNames = list(tupleExps[0])
        listSortExps = list(tupleExps[1])
        return listSortExpNames, listSortExps
            
    def destroyList(self):
        for expUi in self.expUis:
            expUi.destroy()