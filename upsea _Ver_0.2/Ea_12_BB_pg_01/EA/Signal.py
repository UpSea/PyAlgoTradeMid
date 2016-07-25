# -*- coding: utf-8 -*-
from pyalgotrade.technical import bollinger

import sys,os
import pandas as pd
import time as time
import datetime as dt

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'Ea_00_BaseClass'))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy

#mid graphic result output
from Analyzer import Analyzer

#mid money
dataRoot = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))        
sys.path.append(dataRoot)
import Ea_02_money.moneyFixed  as moneyFixed
import Ea_02_money.moneyFirst  as moneyFirst
import Ea_02_money.moneySecond as moneySecond
  
class BollingerBands(midBaseStrategy):
    def __init__(self):    
        self.__initDataCenter()
        self.__initEa()
    def __initEa(self):
        #mid 1)signal 控制参数
        self.InKLine = True        
        self.longAllowed = True
        self.shortAllowed = True         
        self.__shortPeriod = 5
        self.__longPeriod = 20  
        self.__period = 12
        self.__numStd = 2
        #mid 2)signal 计算指标图形化输出控制
        #self.toPlot = True   
        self.analyzer  = Analyzer(Globals=[])   
        #mid 3)money 风险策略控制
        #self.money = moneySecond.moneySecond()  
        self.money = moneyFixed.moneyFixed()     
 
    def __initDataCenter(self):
        #mid 数据中心存取参数定义，决定当前被回测数据的储存属性，用于获取candledata，feeds 
        self.dataProvider = 'tushare'
        self.storageType = 'mongodb'
        self.period = 'D'
        self.instruments = ['600839']        
        self.instrument = self.instruments[0]   
    def initIndicators(self):
        #mid 3)

        
        self.__bbands = {}
        for instrument in self.instruments:
            self.__bbands[instrument] = bollinger.BollingerBands(
                self.closePrices[instrument],self.__period, self.__numStd,
                maxLen=self.mid_DEFAULT_MAX_LEN)
    def addIndicators(self,instrument):
        #mid 此处生成的数据仅由Analyzer消费
        upperBand = self.__bbands[instrument].getUpperBand()
        middleBand = self.__bbands[instrument].getMiddleBand()
        lowerBand = self.__bbands[instrument].getLowerBand()
        
        upper = pd.DataFrame(data=list(upperBand),index=upperBand.getDateTimes(),columns = ['upper'])  
        middle = pd.DataFrame(data=list(middleBand),index = middleBand.getDateTimes(),columns = ['middle'])        
        lower = pd.DataFrame(data=list(lowerBand),index=lowerBand.getDateTimes(),columns = ['lower'])
        
    
        self.results[instrument] = self.results[instrument].join(upper)
        self.results[instrument] = self.results[instrument].join(middle)
        self.results[instrument] = self.results[instrument].join(lower)
        
        
        
        #self.result['upper'] = list(self.__bbands.getUpperBand())
        #self.result['middle']= list(self.__bbands.getMiddleBand())
        #self.result['lower'] = list(self.__bbands.getLowerBand())
    def calcSignal(self):

        
        self.buySignal,self.sellSignal = {},{}
        for instrument in self.instruments:
            self.buySignal[instrument],self.sellSignal[instrument] = False,False
            
            lower = self.__bbands[instrument].getLowerBand()[-1]
            upper = self.__bbands[instrument].getUpperBand()[-1]
            clsoe = self.closePrices[instrument][-1]
            if lower is None:
                return        
            
            if self.longPosition[instrument] is None:
                #mid 无多仓，检查是否需要开多仓
                if clsoe < lower:
                    self.buySignal[instrument] = True   
            if self.shortPosition[instrument] is None:
                if clsoe > upper:
                    self.sellSignal[instrument] = True 
    def onBars(self, bars):     
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordAccount()      