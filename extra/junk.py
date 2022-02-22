'''
Created on Jul 2, 2019

@author: junai
'''
#     allexpsnames = expHandler.getAllExps(expHandler.KEY_PRR_TEST)
#     print("\nExpnames")
#     print(allexpsnames)
#      
#     allexps = []
#      
#     for expname in allexpsnames:
#         allexps.append(expHandler.readExperiment(expname, expHandler.KEY_PRR_TEST))
#      
#     print("\nExps")
#     for exp in allexps:
#         print(exp)
#          
#     allexpsnames, allexps = sortByExpDates(allexpsnames, allexps, False)
#      
#     print("\nSorted Expnames")
#     print(allexpsnames)
#      
#     print("\nSorted Exps")
#     for exp in allexps:
#         print(exp)
        
#     tempPrrTest(nodesManager, expHandler)
    
#     tempRangeTest(expHandler)



#     NodesListFrame.NodesListFrame(win, nodesManager, ctrlCHandler).pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
#     ExperimentsListFrame.ExperimentsListFrame(win, expHandler.KEY_PRR_TEST, expHandler, nodesManager).pack(
#         side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True)
 
 
 
 
#     expHandler = ExperimentsHandler.ExperimentsHandler()
#     prrTest = expHandler.createPrrTest(0, 32, "0, -12", "-9, -1, 5", 1.58, "9, 5, 1", "0, 5, 8, 10, 12", "02")
#     rangeTest = expHandler.createRangeTest(0, 32, "0, -12", "-9, -1, 5", 1.58, "9, 5, 1", 5.2, 54545.4)
#     
#     prrFile1 = expHandler.saveExperiment(prrTest, expHandler.KEY_PRR_TEST)
#     prrFile2 = expHandler.saveExperiment(prrTest, expHandler.KEY_PRR_TEST, "MyPrrTest")
#     
#     rangeFile1 = expHandler.saveExperiment(rangeTest, expHandler.KEY_RNG_TEST)
#     rangeFile2 = expHandler.saveExperiment(rangeTest, expHandler.KEY_RNG_TEST, "MyRangeTest")
    
#     dia = DialogUtilities.SelPrrParams(win, "PRR: "+prrFile1, prrFile1, expHandler)
#     if dia.result is not None:
#         print("Dia result is not none")
#         prrFile3 = expHandler.saveExperiment(dia.result, expHandler.KEY_PRR_TEST, dia.name)
#         print("New file is: " + prrFile3)
#     
#     dia2 = DialogUtilities.SelRangeParams(win, "Range: "+rangeFile1, rangeFile1, expHandler)
#     if dia2.result is not None:
#         rangeFile3 = expHandler.saveExperiment(dia2.result, expHandler.KEY_RNG_TEST, dia2.name)
#         print("New file is: " + rangeFile3)
#     ExperimentUi.ExperimentUi(win, prrFile1, expHandler.KEY_PRR_TEST, expHandler).pack()
    
    
    
#     rangeEval = RangeEvaluation.RangeEvaluation
#     distance = rangeEval.calcDistance(rangeEval, os.path.join(rangeEval.logPath, "testfile.log"))
#     
#     print("\nDistance")
#     rangeEval.printDistanceDict(rangeEval, distance)
#     
#     print("\nMean Distance")
#     rangeEval.printDistanceDict(rangeEval, rangeEval.getMeanDistances(rangeEval, distance))    

#     rangeEval.readDistance(nodesManager.nodes[1], "TaskDescription_Organisation_localization_logs.log")

# import ExperimentsHandler
# 
# expHandler = ExperimentsHandler.ExperimentsHandler()
# resDirs = expHandler.getAllExpDirs(expHandler.KEY_PRR_TEST)
# print(resDirs)
#     

# from matplotlib import pyplot as plt
# import pickle
# import os
# import PrrEvaluationGUI
# import tkinter as tk
# 
# root = tk.Tk()
# 
# resPath = os.path.join(os.path.dirname(__file__), "data", "prr", "PrrTest4", "results", "2019-07-07(16.07.26).pkl")
# pklFile = open(resPath, 'rb')
# 
# dictFigs = None
# if os.path.isfile(resPath):
#     dataFile = open(resPath, 'rb')
#     dictFigs = pickle.load(dataFile)
#     dataFile.close()
# 
# figs = []
# for key, value in dictFigs.items():
#     print(key)
#     figs.append(value)
# 
# evaGui = PrrEvaluationGUI.PrrEvaluationGUI(root, "PrrTest4", False, mWhSupport=None, txNodes=None, rxNodes=None, expData=None)
# evaGui.loadResult(figs)
# 
# root.mainloop()

# import DialogUtilities
# import tkinter as tk
# 
# resList = []
# for i in range(0, 5000):
#     resList.append(str(i))
#     
# root = tk.Tk()
# diagTest = DialogUtilities.SelResultDialog(root, resList, "just testing")
# print(diagTest.result)
# root.mainloop()



from tkinter import Tk, simpledialog
     
root = Tk()
res = simpledialog.askstring("Save Results", "Save results as:")
print("Result: {}".format(res))
root.mainloop()



