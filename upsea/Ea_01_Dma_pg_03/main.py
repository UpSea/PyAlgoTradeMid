# -*- coding: utf-8 -*-
import os,sys
from PyQt4 import QtGui,QtCore
import time as time
import datetime as dt

import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
sys.path.append(xpower)
from BaseClass import midEaController

import EA.Dma_crossover as ea
            
if __name__ == "__main__": 
    app = QtGui.QApplication(sys.argv)    
    startRun = time.clock()
    
    ea = ea.DMACrossOver()
    eaController = midEaController.eaController(ea)
    eaController.runByPhase('2016-05-10 00:00:00', '2016-05-30 00:00:00', 2,True)
    
    endRun = time.clock()
    print "run time: %f s" % (endRun - startRun)       
    sys.exit(app.exec_())  
