# -*- coding: utf-8 -*-
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
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
import Ea_02_money.moneyFixedAmount  as moneyFixedAmount
import Ea_02_money.moneyFixedRatio  as moneyFixedRatio
import Ea_02_money.moneyFirst  as moneyFirst
import Ea_02_money.moneySecond as moneySecond
  
class DMACrossOver(midBaseStrategy):
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
        #mid 2)signal 计算指标图形化输出控制
        #self.toPlot = True   
        self.analyzer  = Analyzer(Globals=[])   
        #mid 3)money 风险策略控制
        money = "moneyFixedRatio"
        if(money == "moneySecond"):
            self.money = moneySecond.moneySecond()  
        elif(money == "moneyFixedAmount"):
            self.money = moneyFixedAmount.moneyFixedAmount() 
        elif(money == "moneyFixedRatio"):
            self.money = moneyFixedRatio.moneyFixedRatio() 
    def __getInstrumentsEastmoneyFormat(self):
        codesStr = """600000.SH
                600010.SH
                600016.SH
                600028.SH
                600029.SH
                600030.SH
                600036.SH
                600048.SH
                600050.SH
                600104.SH
                600109.SH
                600111.SH
                600518.SH
                600519.SH
                600637.SH
                600795.SH
                600837.SH
                600887.SH
                600893.SH
                600958.SH
                600999.SH
                601006.SH
                601088.SH
                601166.SH
                601169.SH
                601186.SH
                601211.SH
                601288.SH
                601318.SH
                601328.SH
                601336.SH
                601377.SH
                601390.SH
                601398.SH
                601601.SH
                601628.SH
                601668.SH
                601669.SH
                601688.SH
                601727.SH
                601766.SH
                601788.SH
                601800.SH
                601818.SH
                601857.SH
                601919.SH
                601985.SH
                601988.SH
                601989.SH
                601998.SH
                """    
        return codesStr
    def __getInstrumentsTushare(self):
        #mid 1)从excel赋值粘贴获得如下数据
        codesStr = self.__getInstrumentsEastmoneyFormat()
        #mid 2)将字符串使用split()分割为list，默认会去除\n和所有空格。
        #codeList = ['000021','000022']
        codeList = [code.split('.')[0] for code in codesStr.split()]     
        return codeList  
    def __getInstrumentsEastmoney(self):
        codesStr = self.__getInstrumentsEastmoneyFormat()
        #mid 2)将字符串使用split()分割为list，默认会去除\n和所有空格。
        #codeList = ['000021.SZ','000022.SZ']
        codeList = codesStr.split()
        return codeList
    def __getBenchSymbol(self):
        return "510050.SH"
    def __getBenchDataProvider(self):
        return "eastmoney"
    def __getInstruments(self,dataSource):
        if(dataSource == "tushare"):
            instruments = self.__getInstrumentsTushare()
        if(dataSource == "eastmoney"):
            instruments = self.__getInstrumentsEastmoney()
        return instruments[0:1]    
    def __initDataCenter(self):
        #mid 数据中心存取参数定义，决定当前被回测数据的储存属性，用于获取candledata，feeds 
        self.period = 'D'
        self.benchSymbol = self.__getBenchSymbol()
        self.benchDataProvider = self.__getBenchDataProvider()
        selector = "three"
        if(selector == "one"):
            self.dataProvider = 'tushare'
            self.storageType = 'mongodb'
            self.instruments = ['000096','000099','600839','600449']#,'600839']     
        if(selector == "tow"):
            self.dataProvider = 'tushare'
            self.storageType = 'mongodb'            
            #self.instruments = ['XAUUSD','EURUSD'] 
            self.instruments = self.__getInstruments(self.dataProvider)
        if(selector == "three"):
            self.dataProvider = 'eastmoney'
            self.storageType = 'mongodb'            
            #self.instruments = ['000021.SZ','000022.SZ'] #]
            self.instruments = self.__getInstruments(self.dataProvider)             
        if(selector == "four"):
            self.dataProvider = 'mt5'
            self.storageType = 'mongodb'            
            #self.instruments = ['XAUUSD','EURUSD'] 
            self.instruments = ['XAGUSD','XAUUSD']                    
    def initIndicators(self):
        #mid 3)
        self.__sma = {}
        self.__lma = {}        
        for instrument in self.instruments:
            self.__sma[instrument] = ma.SMA(self.closePrices[instrument], self.__shortPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
            self.__lma[instrument] = ma.SMA(self.closePrices[instrument],self.__longPeriod,maxLen=self.mid_DEFAULT_MAX_LEN)
    def addIndicators(self,instrument):
        #mid 此处生成的数据仅由Analyzer消费
        short_ema = pd.DataFrame(data=list(self.__sma[instrument]),index=self.__sma[instrument].getDateTimes(),columns = ['short_ema'])
        long_ema = pd.DataFrame(data=list(self.__lma[instrument]),index=self.__lma[instrument].getDateTimes(),columns = ['long_ema'])
        
        self.results[instrument] = self.results[instrument].join(short_ema)
        self.results[instrument] = self.results[instrument].join(long_ema)
        #self.results[instrument]['short_ema'] = e['short_ema']
        #self.results[instrument]['long_ema'] = list(self.__lma[instrument])
    def calcSignal(self):
        self.buySignal,self.sellSignal = {},{}
        for instrument in self.instruments:
            self.buySignal[instrument],self.sellSignal[instrument] = False,False
            #if(self.longAllowed):
            if self.longPosition[instrument] is None:
                #mid 无多仓，检查是否需要开多仓
                if cross.cross_above(self.__sma[instrument], self.__lma[instrument]) > 0:
                    self.buySignal[instrument] = True   
            #if(self.shortAllowed ):
            if self.shortPosition[instrument] is None:
                if cross.cross_below(self.__sma[instrument], self.__lma[instrument]) > 0:
                    self.sellSignal[instrument] = True 
    def onBars(self, bars):   
        time = self.getCurrentDateTime()
        if(time == dt.datetime(2001,11,8,0,0)):
            pass        
        self.calcSignal()
        self.closePosition()
        self.openPosition()
        self.recordAccount()      