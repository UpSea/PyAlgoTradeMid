# -*- coding: utf-8 -*-
import time as time
import datetime as dt
class eaController():
    def __init__(self,ea):
        self.ea = ea
        self.eaList = []
    def runByPhase(self,timeFrom,timeTo,phases,toPlot):
        #mid str to pyTimeStamp
        #self.toPlot = toPlot
        self.ea.toPlot = toPlot
        timeStampFrom = time.mktime(time.strptime(timeFrom, "%Y-%m-%d %H:%M:%S"))
        timeStampTo   = time.mktime(time.strptime(timeTo, "%Y-%m-%d %H:%M:%S")) 
        print timeFrom,timeTo
        
        interval = (timeStampTo - timeStampFrom)/phases
        
        startTimeStamp = timeStampFrom
        results = []
        for index in range(phases):
            endTimeStamp = startTimeStamp + interval
            
            #mid pyTimeStamp to datetime
            #timeFromDatetime = dt.datetime.utcfromtimestamp(startTimeStamp)
            #timeToDatetime = dt.datetime.utcfromtimestamp(endTimeStamp)            
            
            timeFromDatetime = dt.datetime.fromtimestamp(startTimeStamp)
            timeToDatetime = dt.datetime.fromtimestamp(endTimeStamp)
            
            self.ea.run(timeFrom = timeFromDatetime,timeTo = timeToDatetime)

            self.eaList.append(self.ea)
            summary = self.ea.detail() 
            results.append(summary)
            
            startTimeStamp = endTimeStamp
        print  "------------------------"
        print timeFrom,' to ',timeTo
        print  "------------------------"
        for result in results:
            print result      