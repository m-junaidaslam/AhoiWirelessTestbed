'''
Created on Jul 2, 2019

@author: junai
'''
from ControlCenter.UserInterfaces.DialogUtilities import showInfoMessage
from ControlCenter.Evaluation import RangeEvaluation
import tkinter.ttk as ttk
from tkinter import Toplevel, Label, TOP, Frame, BOTTOM, BOTH, X, Scrollbar, VERTICAL, HORIZONTAL, RIGHT, Y, Canvas, NW, SUNKEN, IntVar, simpledialog
import threading
import os
import numpy as np
import datetime as dt

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
from ControlCenter.Evaluation.ExperimentsHandler import getNow
from collections import defaultdict


class RangeEvaluationGUI(Toplevel):
    
#     resPath = os.path.join(os.path.dirname(os.getcwd()), "data", "range")
    
    def __init__(self, parent, rootPath, expName, runExp, mWhSupport, resHandler, txNodes=None, rxNodes=None, expData=None):
        super().__init__(parent)
        rangePath = os.path.join(rootPath, "data", "range")
        self.grab_set()
        self.runExp = runExp
        self.expName = expName
        self.resHandler = resHandler
        if runExp:
            self.rangeEval = RangeEvaluation.RangeEvaluation(txNodes, rxNodes, rangePath, expName, expData, self.progUpdate)
            self.expData = expData
            
        self.resPath = os.path.join(rangePath, expName, "results")
        self.title(expName)
        self.state("zoomed")
        self.ax = []
        self.txNode = None
        self.rxNodes = []
        self.rxPkts = defaultdict(list)
        self.maxPkts = 0
        self.ani = []
        self.figs = []
        self.mWhSupport = mWhSupport
        
        self.plotNbr = 0
        self.windowHeight = 0

        self.nextPlot = False
        
        self.body()

    
    def body(self):
        
        if self.runExp:
            self.style = ttk.Style(self)
            # add label in the layout
            self.style.layout('text.Horizontal.TProgressbar', 
                         [('Horizontal.Progressbar.trough',
                           {'children': [('Horizontal.Progressbar.pbar',
                                          {'side': 'left', 'sticky': 'ns'})],
                            'sticky': 'nswe'}), 
                          ('Horizontal.Progressbar.label', {'sticky': ''})])
            # set initial text
            self.style.configure('text.Horizontal.TProgressbar', font='courier 13 bold', foreground='brown', text="0 / " + str(self.rangeEval.maxWait))
            
            self.pbVar = IntVar(self)
            self.progBar = ttk.Progressbar(self, orient='horizontal', length=800, mode='determinate', variable=self.pbVar, style='text.Horizontal.TProgressbar')
            self.progBar['maximum'] = self.rangeEval.maxWait
            self.pbVar.set(0)
            self.progBar.pack(side=TOP, fill=X, padx=1, pady=5)
        
        self.frameLow = Frame(self, background='white')
        self.frameLow.pack(side=BOTTOM, fill=BOTH, padx=1, pady=3, expand= True)
        
        self.canvas = canvas = Canvas(self.frameLow, bg='white', relief=SUNKEN)       
        canvas.config(highlightthickness=0) 

        #Create a Scrollbar Horisontal
        hbar=Scrollbar(self.frameLow,orient=HORIZONTAL)
        hbar.pack(side=BOTTOM,fill=X)
        hbar.config(command=canvas.xview)

        #Create a Scrollbar Vertical
        vbar=Scrollbar(self.frameLow,orient=VERTICAL)
        vbar.pack(side=RIGHT,fill=Y)
        vbar.config(command=canvas.yview)

        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        canvas.pack(side=TOP,expand=True,fill=BOTH)
        
        self.mWhSupport.add_support_to(self.canvas, xscrollbar=vbar, yscrollbar=hbar, what="pages")
        
        #Create a Frame in the canvas
        self.canvFrame = Frame(canvas, bg='white')
        self.canvFrame.pack()

        self.bind("<Escape>", self.cancel)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        
        if self.runExp:
            self.rangeRunThread = threading.Thread(target=self.startEvaluation, name="rangeEval_" + self.rangeEval.expName, args=[])
            self.rangeRunThread.daemon = True
            self.rangeRunThread.start()
            
#         return self.progBar
        return self.frameLow     
    
    def _onFrameConfigure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
           
    def _onFrameSize(self, event):
        canvasWidth = event.width
        canvasHeight = event.height
        self.canvas.itemconfig(self.canvFrameId, width=canvasWidth, height=canvasHeight)

    def progUpdate(self, totProg: int, nextPlot, txNode, rxNodes, rxData, maxPkts):
#         print("Total progress: {}, MaxProgress: {}".format(totProg, self.rangeEval.maxWait))
#         print("Maximum packets: {}".format(maxPkts))
        self.pbVar.set(totProg)
        strPb = str(int((self.pbVar.get() / self.rangeEval.maxWait) * 100)) + "% (" + str(self.pbVar.get()) + "/" + str(self.rangeEval.maxWait) + ")"
        self.style.configure('text.Horizontal.TProgressbar', 
                    text=strPb)  # update label
        self.txNode = txNode
        self.nodeNames = []
        self.rxPkts = rxData
        self.rxNodes = rxNodes

            
        self.maxPkts = maxPkts
        self.nextPlot = nextPlot
        
        if nextPlot:
            self.addNextPlot()
            self.nextPlot = False
        
    def addNextPlot(self, newFig=None):
        #Create space for the plot and tool bar.
        if self.ani:
            if self.ani[len(self.ani) - 1] is not None:
                self.ani[len(self.ani) - 1].event_source.stop()
        self.windowHeight += 660
        self.plotNbr += 1
        if newFig is None:    
            self.figs.append(Figure(figsize=(9, 4), dpi=150))
        else:
            self.figs.append(newFig)
        
        Label(self.canvFrame, 
              text="Plotnumber: " + str(self.plotNbr),
               font=("helevetica", '16', 'bold'), bg='#FF7F24').pack(side=TOP,fill=X)

        frm = Frame(self.canvFrame, bg='#9FB6CD')
        frm.pack(side=TOP, fill=X)

        self.canvasMPL2, self.canvasMPLToolBar2 = self.getFigCanvas(self.figs[len(self.figs) - 1], frm)
        
        self.ani.append(animation.FuncAnimation(self.figs[len(self.figs) - 1], self.plotValues, interval=500))
        
        self.canvasMPL2.pack(side=TOP)
        self.canvasMPLToolBar2.pack(side=TOP)
        
        canvWidth = self.winfo_width() - 15
        
        self.canvas.config(width=canvWidth,height= self.windowHeight)
        self.canvas.config(scrollregion=(0,0,canvWidth, self.windowHeight))
        self.canvFrameId = self.canvas.create_window(0,0, anchor = NW, window = self.canvFrame, width = canvWidth, height = self.windowHeight)
        
#         self.canvFrame.bind("<Configure>", self._onFrameConfigure)
#         self.canvas.bind('<Configure>', self._onFrameSize)

        
        self.canvas.focus_set() #Doesnt work with FigureCanvasTkAgg, this steals the focus 
        self.canvas.configure(yscrollincrement='25')
        self.canvas.yview_moveto(1)
        
        if newFig is None:
            self.ax.append(self.figs[len(self.figs) - 1].add_subplot(111))
            self.ax[len(self.ax) - 1].set_facecolor(color='lightgray')
            self.ax[len(self.ax) - 1].tick_params(axis='both', labelsize=8, width=1, length=1)
        
    def plotValues(self, i):
#         print("Plot Values")
        if self.ax and not self.nextPlot:
            self.ax[len(self.ax) - 1].clear()
            for key, value in self.rxPkts.items():
                nodeName = [mod.name for mod in self.rxNodes if key == mod.nodeId]
                weights = np.ones_like(value)/float(len(value))
                self.ax[len(self.ax) - 1].hist(value, weights=weights, rwidth=0.5, histtype='barstacked', label=nodeName)
                self.ax[len(self.ax) - 1].legend(prop={'size': 8})
            self.ax[len(self.ax) - 1].set_xlabel("Estimated Distance (m)")
            self.ax[len(self.ax) - 1].set_ylabel("Relative Frequency (Probability Density)")
            self.ax[len(self.ax) - 1].set_title(
                "Transmitter(Tx) Modem: {}, Sent Packets: {}".format(self.txNode.name, str(self.maxPkts)) +
                "\nAGC: {}".format(bool(self.expData.basic.testAgc)) + 
                ", Pkt Count: {}".format(self.expData.basic.pktCount) + 
                ", Tx Gain: {}".format(self.expData.basic.txGain) + 
                ", Rx Gain: {}".format(self.expData.basic.rxGain) + 
                "\nSleep: {}".format(self.expData.basic.sleepTime) + 
#                 "\nSleep: {}".format(3.0) +     #For simulation
                ", Spread: {}".format(self.expData.basic.spreadLen) + 
                ", Range Delay: {}".format(self.expData.rangeDelay) + 
#                 ", Range Delay: {}".format(3) +     #For simulation
                ", Sound Speed: {}".format(self.expData.soundSpeed), 
                fontsize=8)
        
    def startEvaluation(self):
        self.rangeEval.run()
        if self.ani:
            if self.ani[len(self.ani) - 1] is not None:
                self.ani[len(self.ani) - 1].event_source.stop()
        if self.rangeEval.rangeRun:
            showInfoMessage("Success", "Range Test is complete.")
        
    def loadResult(self, resFile):
        figs = self.resHandler.getResFigs(self.expName, resFile)
        for fig in figs:
            self.addNextPlot(fig)       
        
    def cancel(self, event=None):
        if self.runExp:
            saveName = simpledialog.askstring("Save Results", "Name", initialvalue=getNow())
            if saveName is not None:
                if saveName:
                    self.resHandler.saveResult(self.expName, saveName, self.figs)
        self.destroy()
        self.grab_release()
        if self.runExp:
            self.rangeEval.rangeRun = False
            print("RangeEvaluationGUI cancelled")
        
    def getFigCanvas(self, figure, masterWidget):
        '''
        Returns canvas of plot and canvas of tool bar
        '''
        canvas = FigureCanvasTkAgg(figure, master=masterWidget)
        toolbar = NavigationToolbar2Tk(canvas, masterWidget)
        toolbar.update()
        #return the plot and the toolbar
        return canvas.get_tk_widget(), canvas._tkcanvas
    
    
def getNow():
    return dt.datetime.now().strftime("%Y-%m-%d(%H.%M.%S)")