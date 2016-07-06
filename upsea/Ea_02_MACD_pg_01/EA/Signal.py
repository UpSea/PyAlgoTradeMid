# -*- coding: utf-8 -*-
from pyalgotrade.technical import macd

import sys,os
import pandas as pd
import time as time
import datetime as dt

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'BaseClass'))
sys.path.append(xpower)
from midBaseStrategy import midBaseStrategy as midBaseStrategy

#mid graphic result output
from Analyzer import Analyzer

#mid money
dataRoot = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))        
sys.path.append(dataRoot)
import money.moneyFixed  as moneyFixed
import money.moneyFirst  as moneyFirst
import money.moneySecond as moneySecond
  
class MACD(midBaseStrategy):
    def __init__(self):    
        self.__initDataCenter()
        self.__initEa()
    def __initEa(self):
        #mid 1)signal 控制参数
        self.longAllowed = True
        self.shortAllowed = True         
        self.__shortPeriod = 20
        self.__longPeriod = 40        
        #mid 2)signal 计算指标图形化输出控制
        self.toPlot = True   
        self.analyzer  = Analyzer(Globals=[])   
        #mid 3)money 风险策略控制
        self.money = moneySecond.moneySecond()  
    def __initDataCenter(self):
        #mid 数据中心存取参数定义，决定当前被回测数据的储存属性，用于获取candledata，feeds 
        self.dataProvider = 'mt5'
        self.storageType = 'csv'
        self.period = 'm5'
        self.instruments = ['XAUUSD']        
        self.instrument = self.instruments[0]   
    def initIndicators(self):
        #mid 3)
        self.__macd = macd.MACD(self.closePrices, 15, 20,10,maxLen=self.mid_DEFAULT_MAX_LEN)
    def addIndicators(self):
        #mid 此处生成的数据仅由Analyzer消费
        self.result['histogram'] = list(self.__macd.getHistogram())
        self.result['signal']= list(self.__macd.getSignal())        
        
        a= list(self.__macd.getHistogram())
        b= list(self.__macd.getSignal())
        b= list(self.__macd.getSignal())
    def calcSignal(self):
        self.buySignal,self.sellSignal = False,False
        
        histogram = self.__macd.getHistogram()[-1]
        signal = self.__macd.getSignal()[-1]
        if signal is None:
            return        
        
        if(self.longAllowed):
            if self.longPosition is None:
                #mid 无多仓，检查是否需要开多仓
                if signal > 0:
                    self.buySignal = True   
        if(self.shortAllowed):
            if self.shortPosition is None:
                if signal < 0:
                    self.sellSignal = True 
    def onBars(self, bars):     
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordPositions()      