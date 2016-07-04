# -*- coding: utf-8 -*-
import time as time
import datetime as dt
class eaController():
    def __init__(self,ea):
        self.ea = ea
        self.eaList = []
    def runByPhase(self,timeFrom,timeTo,phases,toPlot):
        #mid str to pyTimeStamp
        timeStampFrom = int(time.mktime(time.strptime(timeFrom, "%Y-%m-%d %H:%M:%S")))
        timeStampTo   = int(time.mktime(time.strptime(timeTo, "%Y-%m-%d %H:%M:%S")))    
        print timeFrom,timeTo
        
        interval = (timeStampTo - timeStampFrom)/phases
        
        startTimeStamp = timeStampFrom
        self.results02 = []
        for index in range(phases):
            endTimeStamp = startTimeStamp + interval
            
            #mid pyTimeStamp to datetime
            timeFromDatetime = dt.datetime.utcfromtimestamp(startTimeStamp)
            timeToDatetime = dt.datetime.utcfromtimestamp(endTimeStamp)
            
            self.ea.run(timeFrom = timeFromDatetime,timeTo = timeToDatetime)

            self.eaList.append(self.ea)
            result02 = self.ea.summary() 
            self.results02.append(result02)
            
            startTimeStamp = endTimeStamp
        print  "------------------------"
        print timeFrom,' to ',timeTo
        print  "------------------------"
        for result in self.results02:
            print result      