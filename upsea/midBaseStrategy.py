# -*- coding: utf-8 -*-
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.dataseries import SequenceDataSeries
from pyalgotrade.dataseries import DEFAULT_MAX_LEN
import pandas as pd

class midBaseStrategy(strategy.BacktestingStrategy):
    def __init__(self, feeds = None, instrument = '',money = None,longAllowed=True,shortAllowed=True):
        strategy.BacktestingStrategy.__init__(self, feeds)
        
        #mid follow vars will be used in subclass
        self.feeds = feeds
        self.mid_DEFAULT_MAX_LEN = 10 * DEFAULT_MAX_LEN
        self.instrument = instrument
        self.longPosition = None
        self.shortPosition = None
        self.buySignal = False
        self.sellSignal = False
        self.money = money
        self.longAllowed = True
        self.shortAllowed = True 
        
        #mid follow vars will be used only this class
        self.__curPositionCost = 0  #mid init position value
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
        self.__position_volume = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)       #mid 当前持有头寸数量
        self.__position_cost = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)  #mid 当前持有头寸开仓成本
        self.__position_pnl = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)   #mid 当前持有头寸价值
        self.__portfolio_value = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__buy = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
        self.__sell = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
    def getAssetStructure(self):
        #mid --------------------------------
        #mid 当前账户资产结构如下方式获取
        #mid Long 和 Short不会同时存在
        #mid 在开仓前，若有反向持仓，则此过程查询并输出已持有的反向持仓
        broker = self.getBroker()
        portfolio_value = broker.getEquity()
        cash = broker.getCash()
        if self.shortPosition is not None or self.longPosition is not None:
            bars = self.getFeed().getCurrentBars()  

            positions = broker.getPositions()

            positionsOpenValue = {}
            positionsCloseValue = {}
            for key,value in positions.items():
                print "key:"+key+",value:"+str(value)
                bar = bars.getBar(key)
                openPrice = bar.getOpen() 
                closePrice = bar.getClose()
                share = broker.getShares(key)
                positionsOpenValue[key] = openPrice*share
                positionsCloseValue[key] = closePrice*share

            print 
            print 'current bar asset structure'
            print 'open cash %2.f.' % (cash)
            for key,value in positionsOpenValue.items():
                print "key:"+key+",value:"+str(value)
            print 'close cash %2.f.' % (cash)
            for key,value in positionsCloseValue.items():
                print "key:"+key+",value:"+str(value)    
            print 'portfolio:%2.f' % (portfolio_value)

            return portfolio_value,cash,sum(positionsCloseValue.values())
        return portfolio_value,cash,0
    def recordPositions(self):
        # record position      
        #######################################################################
        broker = self.getBroker()
        position = broker.getPositions()                   #mid position is dict of share
        share = broker.getShares(self.instrument)        #mid position is dict of share
        lastPrice = self.getLastPrice(self.instrument)  
        portfolio_value = broker.getEquity()               #mid 按close价格计算的权益
        cash = broker.getCash()

        position_value = portfolio_value - cash

        position_pnl = position_value - self.__curPositionCost

        print
        print 'cash: %.2f' %(cash)
        print 'position value: %.2f' % (portfolio_value - cash)
        print 'mid calc: %.2f' %(lastPrice*share+cash)
        print 'broker returned: %.2f' %(portfolio_value)


        curTime = self.getCurrentDateTime()
        currentTime = self.getCurrentDateTime()

        self.__position_volume.appendWithDateTime(currentTime,abs(share))  

        self.__position_cost.appendWithDateTime(currentTime,abs(self.__curPositionCost))

        self.__position_pnl.appendWithDateTime(currentTime,position_pnl)

        self.__portfolio_value.appendWithDateTime(currentTime,portfolio_value)  
        self.__buy.appendWithDateTime(currentTime,self.buySignal)              
        self.__sell.appendWithDateTime(currentTime,self.sellSignal) 
    def getInstrument(self):
        return self.instrument
    def getPortfolio(self):
        return self.__portfolio_value
    def getPositionVolume(self):
        return self.__position_volume    
    def getPositionCost(self):
        return self.__position_cost
    def getPositionPnl(self):
        return self.__position_pnl 

    def getBuy(self):
        return self.__buy
    def getSell(self):
        return self.__sell
    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()   
        portfolio = self.getResult()
        cash = self.getBroker().getCash() 

        '''mid
  以下两种方法都是为了计算持仓成本
  由于getEquity()返回的是依据当日close价格计算出来的权益
  所以，这个值不能作为持仓成本
  持仓成本需要以onEnterOk时bar的open价格计算
  所以应使用第二种算法
  由于经常有跳开现象，所以依据bar(n-1).close发出的market order，
  在bar(n).open执行时通常会有gap出现，表现在position_cost图上时就是持有成本离计划成本会有跳口，
  '''
        if(False):#mid two methods to cacl cost.
            portfolio_value = self.getBroker().getEquity()
            self.__curPositionCost = portfolio_value - cash  
        else:
            feed = self.getFeed()
            bars = feed.getCurrentBars()
            bar = bars.getBar(self.instrument)
            openPrice = bar.getOpen()   
            closePrice = self.getLastPrice(self.instrument) #mid lastPrice == closePrice
            share = self.getBroker().getShares(self.instrument)
            self.__curPositionCost = openPrice*share

        self.info("onEnterOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))
        if isinstance(position, strategy.position.LongPosition):
            self.info("onEnterOK().ExecutionInfo: %s,OPEN LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice())) 
        elif isinstance(position, strategy.position.ShortPosition):
            self.info("onEnterOK().ExecutionInfo: %s,OPEN SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))     



    def onEnterCanceled(self, position):
        self.info("onEnterCanceled().current available cash: %.2f." % (self.getBroker().getCash()))
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
            self.info("onEnterCanceled().OPEN LONG cancled.")                                
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
            self.info("onEnterCanceled().OPEN SHORT cancled.")
    def onExitOk(self, position):        
        execInfo = position.getExitOrder().getExecutionInfo()     
        portfolio = self.getResult()
        cash = self.getBroker().getCash()
        self.info("onExitOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))

        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))                    
    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition = None
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition = None
    def logInfo(self,bars = None):
        pLong,pShort = 0,0
        if(self.longPosition is not None):
            pLong = self.longPosition.getShares()
        if(self.shortPosition is not None):
            pShort = self.shortPosition.getShares()


        bar = bars[self.instrument]
        pOpen = bar.getOpen()
        pHigh = bar.getHigh()
        pLow = bar.getLow()
        pClose = bar.getClose()
        pPrice = bar.getPrice()

        self.info('logInfo().price:%.3f,open:%.2f,high:%.2f,low:%.2f,close:%.2f'%(pPrice,pOpen,pHigh,pLow,pClose))
        #self.info('long:%.2f#short:%.2f'%(pLong,pShort))        
    def run(self):
        strategy.BacktestingStrategy.run(self)

        sma = self.getSMA()
        lma = self.getLMA()
        buy = self.getBuy()
        sell = self.getSell()

        portfolio_value = self.getPortfolio()

        position_volume = self.getPositionVolume()
        position_cost = self.getPositionCost()
        position_pnl = self.getPositionPnl()

        result = pd.DataFrame({'position_volume':list(position_volume),'position_cost':list(position_cost),'position_pnl':list(position_pnl),
                               'short_ema':list(sma),'long_ema':list(lma),
                               'buy':list(buy),'sell':list(sell),'portfolio_value':list(portfolio_value)},
                              columns=['position_volume','position_cost','position_pnl','short_ema','long_ema','buy','sell','portfolio_value'],
                              index=position_volume.getDateTimes())        
        return result