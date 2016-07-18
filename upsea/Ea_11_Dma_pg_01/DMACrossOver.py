# -*- coding: utf-8 -*-
import os,sys
from PyQt4 import QtGui,QtCore
import time as time
import datetime as dt

import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir))
sys.path.append(xpower)
from Ea_00_BaseClass import midEaController

import EA.Signal as signal
            
if __name__ == "__main__": 
    app = QtGui.QApplication(sys.argv)    
    startRun = time.clock()
    
    signal = signal.DMACrossOver()
    eaController = midEaController.eaController(signal)
    eaController.runByPhase('2000-09-27 00:00:00', '2015-07-09 00:00:00', 1,True)
    endRun = time.clock()
    print "run time: %f s" % (endRun - startRun)       
    sys.exit(app.exec_())  
