# -*- coding: utf-8 -*-
from pyalgotrade import strategy

from pyalgotrade.broker import backtesting
from pyalgotrade.broker import fillstrategy

from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.dataseries import SequenceDataSeries
from pyalgotrade.dataseries import DEFAULT_MAX_LEN
import pandas as pd
import datetime as dt

class midBaseStrategy(strategy.BacktestingStrategy):
    def getFeeds(self,timeFrom=None,timeTo=None):
        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
        sys.path.append(xpower)
        
        import dataCenter as dataCenter            
        self.dataCenter = dataCenter.dataCenter()           
        feeds = self.dataCenter.getFeedsForPAT(dataProvider = self.dataProvider,storageType = self.storageType,instruments = self.instruments,
                                               period=self.period,timeTo = timeTo,timeFrom=timeFrom)        
        return feeds    
    
    def getFeedNew(self,timeFrom=None,timeTo=None):
        '''mid should not be named the same with base class'''
        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdata'))
        sys.path.append(xpower)
        
        import dataCenter as dataCenter            
        self.dataCenter = dataCenter.dataCenter()           
        feed = self.dataCenter.getFeedForPAT(dataProvider = self.dataProvider,storageType = self.storageType,instruments = self.instruments,
                                               period=self.period,timeTo = timeTo,timeFrom=timeFrom)        
        return feed      
    
    
    
    def initEa(self,timeFrom=None,timeTo=None):
        self.results = {}
        feed = self.getFeedNew(timeFrom = timeFrom,timeTo = timeTo)
        self.mid_DEFAULT_MAX_LEN = 10 * DEFAULT_MAX_LEN
        mid_DEFAULT_MAX_LEN = self.mid_DEFAULT_MAX_LEN
        
        #mid set init cash
        cash_or_brk = 1000000
        volumeLimit = 0.5       #mid used to calculate available volume for an order: availableVolume = volumeLeft * volumeLimit
        #mid set fillstrategy
        fillStrategy = fillstrategy.DefaultStrategy(volumeLimit = volumeLimit)
        
        broker = backtesting.Broker(cash_or_brk, feed)
        broker.setFillStrategy(fillStrategy)
        #mid init base
        strategy.BacktestingStrategy.__init__(self, feed,broker)
        
        #mid 计算ma将使用当天的收盘价格计算
        #mid 1)
        self.closePrices = {}
        self.longPosition = {}
        self.shortPosition = {}
        self.buySignal = {}
        self.sellSignal = {}        
        self.timeFrom = timeFrom
        self.timeTo = timeTo        
        #mid follow vars will be used only this class
        self.__portfolio_value = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)   #mid 记录资产组合(cash + 各个持仓证券的价值和)的合计价值变化
        self.__available_cash  = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)   #mid 记录资产组合的现金变化
            
            
        self.__long_exitBar_pnl = {}                    #mid 多头平仓bar产生的pnl
        self.__long_position_volume = {}                #mid 当前多头数量
        self.__long_position_cost = {}                  #mid 当前持有多头开仓成本
        self.__long_position_currentBar_pnl = {}        #mid 当前持有多头当前bar产生的pnl  
        self.__long_position_pnl = {}                   #mid 当前多头累计产生的pnl
        
        self.__short_exitBar_pnl = {}
        self.__short_position_volume = {}               #mid 当前持有头寸数量
        self.__short_position_cost = {}                 #mid 当前持有头寸开仓成本
        self.__short_position_currentBar_pnl = {}       #mid 当前持有头寸价值
        self.__short_position_pnl = {}
        
        self.__position_cumulativePNL = {}              #mid 当前 symbol 持有头寸cumulative pnl 价值(包括该symbol多头和空头的所有开仓平仓产生的pnl)
        self.__buy = {}
        self.__sell = {}    
        
        for instrument in self.instruments:
            dataSeries = feed[instrument]
            
            
            dataSeries.setMaxLen(mid_DEFAULT_MAX_LEN)       
            closeSeries = dataSeries.getCloseDataSeries()
            #mid 2)
            prices = closeSeries
            prices.setMaxLen(mid_DEFAULT_MAX_LEN)        
            
            #mid follow vars will be used in subclass
            self.closePrices[instrument] = prices
            self.longPosition[instrument] = None
            self.shortPosition[instrument] = None
            self.buySignal[instrument] = False
            self.sellSignal[instrument] = False

            #mid follow vars will be used only this class
            self.__long_exitBar_pnl[instrument] = None
            self.__short_exitBar_pnl[instrument] = None
            self.__long_position_volume[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)       #mid 当前持有头寸数量
            self.__short_position_volume[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)       #mid 当前持有头寸数量
            self.__long_position_cost[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)         #mid 当前持有头寸开仓成本
            self.__short_position_cost[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)         #mid 当前持有头寸开仓成本
            self.__long_position_currentBar_pnl[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)          #mid 当前持有头寸价值
            self.__short_position_currentBar_pnl[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)          #mid 当前持有头寸价值
            self.__short_position_pnl[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN) 
            self.__long_position_pnl[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN) 
            self.__position_cumulativePNL[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
            self.__buy[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN)
            self.__sell[instrument] = SequenceDataSeries(maxLen = mid_DEFAULT_MAX_LEN) 
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
    def sampleSub01(self,instrument):
        """mid not called anywhere
        because of open price gap,method below is not right.
        """
        broker = self.getBroker()
        a = broker.getEquity()
        b = self.getResult()
        
        lastOpenPrice  = None
        lastClosePrice = None
        bar = self.getFeed().getLastBar(instrument)
        if bar is not None:
            lastOpenPrice = bar.getOpen()
            lastClosePrice = bar.getClose() 
             #lastPrice = self.getLastPrice(instrument)  
           
            pnl = (lastClosePrice - lastOpenPrice) * share
        else:
            pnl = 0 #mid instrument is dislisted.
        if(len(self.__position_cumulativePNL[instrument])>0):
            lastCumulativePNL = self.__position_cumulativePNL[instrument][-1]
        else:
            lastCumulativePNL = 0        
            
    def recordAccount(self):
        # record position      
        #######################################################################
        broker = self.getBroker()
        curTime = self.getCurrentDateTime()
        currentTime = self.getCurrentDateTime()
        cash = broker.getCash(includeShort=False)
        portfolio_value = broker.getEquity()               #mid 按close价格计算的权益
        
        print 
        self.info("onBars().recordAccount().Current time:%s"%(str(currentTime)))
        self.info("onBars().recordAccount().----portfolio value: %.2f" % (portfolio_value))
        self.info("onBars().recordAccount().----cash in portfolio: %.2f" % (cash))
        
        self.__portfolio_value.appendWithDateTime(currentTime,portfolio_value) 
        self.__available_cash.appendWithDateTime(currentTime,cash) 
        totalCumulativePNL = 0
        
        
        time = self.getCurrentDateTime()
        if(time == dt.datetime(2010,12,22,0,0)):
            a = 8   
          
        for instrument in self.instruments:
            lastClosePrice = self.getLastPrice(instrument)  
            if(lastClosePrice is None):
                continue
            #position_value = lastClosePrice*share
            longPosition = self.longPosition[instrument]    
            longQuantity = 0
            longPnl = 0     
            longStandingCurBarPnl = 0
            longValue = 0
            longCost = 0
            
            shortPosition = self.shortPosition[instrument]
            shortQuantity = 0
            shortPnl = 0        
            shortStandingCurBarPnl= 0
            shortValue = 0
            shortCost = 0
            
            if(longPosition):
                entryInfo = longPosition.getEntryOrder()
                execInfo = entryInfo.getExecutionInfo()
                if(execInfo):                
                    longPnl = longPosition.getPnL()
                    longStandingCurBarPnl = longPnl - self.__lastLongPnl
                    
                    longQuantity = longPosition.getQuantity()
                    longCostPrice = execInfo.getPrice()
                    longCost = longQuantity * longCostPrice

                    self.__lastLongPnl = longPnl
            if(shortPosition):
                entryInfo = shortPosition.getEntryOrder()
                execInfo = entryInfo.getExecutionInfo()   
                if(execInfo):
                    shortPnl = shortPosition.getPnL()
                    shortStandingCurBarPnl = shortPnl - self.__lastShortPnl
                    
                    shortQuantity = shortPosition.getQuantity()
                    shortCostPrice = execInfo.getPrice()
                    shortCost = shortQuantity * shortCostPrice

                    self.__lastShortPnl = shortPnl
                    
            if(self.__long_exitBar_pnl[instrument]):
                self.__long_position_currentBar_pnl[instrument].appendWithDateTime(currentTime,self.__long_exitBar_pnl[instrument])  
                self.__long_exitBar_pnl[instrument] = None
            else:
                self.__long_position_currentBar_pnl[instrument].appendWithDateTime(currentTime,longStandingCurBarPnl)  
                
            if(self.__short_exitBar_pnl[instrument]):
                self.__short_position_currentBar_pnl[instrument].appendWithDateTime(currentTime,self.__short_exitBar_pnl[instrument])  
                self.__short_exitBar_pnl[instrument] = None
            else:
                self.__short_position_currentBar_pnl[instrument].appendWithDateTime(currentTime,shortStandingCurBarPnl)   
                
                
            #self.__short_position_pnl[instrument].appendWithDateTime(currentTime,shortCurBarPnl)            
                
                
            self.__long_position_pnl[instrument].appendWithDateTime(currentTime,longPnl)
            self.__short_position_pnl[instrument].appendWithDateTime(currentTime,shortPnl)
            
            self.__long_position_cost[instrument].appendWithDateTime(currentTime,longCost)
            self.__short_position_cost[instrument].appendWithDateTime(currentTime,shortCost)
            
            self.__long_position_volume[instrument].appendWithDateTime(currentTime,longQuantity)  
            self.__short_position_volume[instrument].appendWithDateTime(currentTime,shortQuantity)  
            self.__buy[instrument].appendWithDateTime(currentTime,self.buySignal[instrument])              
            self.__sell[instrument].appendWithDateTime(currentTime,self.sellSignal[instrument])        
            
            cumulativePNL = 0
            longCurBarPnl = self.__long_position_currentBar_pnl[instrument][-1]
            shortCurBarPnl = self.__short_position_currentBar_pnl[instrument][-1]
            currentBarPnl = longCurBarPnl + shortCurBarPnl
            
            if(len(self.__position_cumulativePNL[instrument])>0):
                lastCumulativePNL = self.__position_cumulativePNL[instrument][-1]
                cumulativePNL = lastCumulativePNL + currentBarPnl
            else:
                cumulativePNL = currentBarPnl   

            self.__position_cumulativePNL[instrument].appendWithDateTime(currentTime,cumulativePNL)              
            
            """mid
            如果当前bar有某个position在open price被closed掉，则当前bar的position_pnl是0.
            在当前bar的openprice和上一bar的closeprice之间没有gap时，这个算法是合理的，但是，gap往往是存在的，
            所以，据此计算的barPnl在exitbar上会有gap导致的误差
            在此特别处理exitbar                
            """            
            """
            if(self.__exitBar_position_pnl[instrument] is not None):

                currentExitedPositionPnl = self.__exitBar_position_pnl[instrument]
                lastPositionPnl = self.__position_pnl[instrument][-2]
                currentBarExitedPnl = currentExitedPositionPnl - lastPositionPnl                
                self.__exitBar_position_pnl[instrument] = None   
                currentBarPnl = currentBarPnl + currentBarExitedPnl
            if(len(self.__position_cumulativePNL[instrument])>0):
                lastCumulativePNL = self.__position_cumulativePNL[instrument][-1]
                cumulativePNL = lastCumulativePNL + currentBarPnl
            else:
                cumulativePNL = currentBarPnl   

            self.__position_cumulativePNL[instrument].appendWithDateTime(currentTime,cumulativePNL)  
        """

            if(True):
                self.info("onBars().recordAccount().--------%s" % (instrument))
                
                self.info("onBars().recordAccount().--------mid current bar longPNL: %.3f" %(longCurBarPnl))
                self.info("onBars().recordAccount().--------mid current bar longQuantity:%.3f" % (longQuantity))
                self.info("onBars().recordAccount().--------mid current bar longValue: %.3f" %(longValue))
                self.info("onBars().recordAccount().--------mid current bar longCost: %.3f" %(longCost))

                
                self.info("onBars().recordAccount().--------mid current bar shortPNL: %.3f" %(shortPnl))
                self.info("onBars().recordAccount().--------mid current bar shortQuantity:%.3f" % (shortQuantity))
                self.info("onBars().recordAccount().--------mid calculated position value: %.3f" %(shortValue))                
                self.info("onBars().recordAccount().--------mid calculated shortPnl: %.3f" %(shortCost))

                self.info("onBars().recordAccount().--------mid CumulativePNL: %.3f" %(cumulativePNL))
            totalCumulativePNL = totalCumulativePNL + cumulativePNL

        if(abs(1000000 - (portfolio_value - totalCumulativePNL))>0.00000001):
            self.info("onBars().recordAccount().--------mid initCash: %.3f" %(portfolio_value - totalCumulativePNL))
            a = 8            
            
        
        
    def getPortfolioValue(self):
        return self.__portfolio_value
    def getAvailableCash(self):
        return self.__available_cash
    def getCurInstrument(self):
        return self.curInstrument
    def getPositionValue(self,instrument):
        return self.__position_cumulativePNL[instrument]
    def getLongVolume(self,instrument):
        return self.__long_position_volume[instrument]     
    def getShortVolume(self,instrument):
        return self.__short_position_volume[instrument] 
    def getLongCost(self,instrument):
        return self.__long_position_cost[instrument]    
    def getShortCost(self,instrument):
        return self.__short_position_cost[instrument]
    def getLongPnl(self,instrument):
        return self.__long_position_pnl[instrument]
    def getShortPnl(self,instrument):
        return self.__short_position_pnl[instrument]
    def getBuy(self,instrument):
        return self.__buy[instrument]
    def getSell(self,instrument):
        return self.__sell[instrument]
    def onEnterOk(self, position):
        '''mid
        由于getEquity()返回的是依据当日close价格计算出来的权益
        所以，这个值不能作为持仓成本
        持仓成本需要以onEnterOk时bar的open价格计算
        由于经常有跳开现象，所以依据bar(n-1).close发出的market order，
        在bar(n).open执行时通常会有gap出现，表现在position_cost图上时就是持有成本离计划成本会有跳口，
        '''
        print 
        currentTime = self.getCurrentDateTime()
        execInfo = position.getEntryOrder().getExecutionInfo()   
        self.info("onEnterOK().ExecutionInfo.Current time: %s"%(execInfo.getDateTime()))
        
        #mid 1)record the position cost
        instrument = position.getInstrument()
        feed = self.getFeed()
        bars = feed.getCurrentBars()
        bar = bars.getBar(instrument)
        openPrice = bar.getOpen()   
        closePrice = self.getLastPrice(instrument) #mid lastPrice == closePrice
        
        #mid 2)log account info after enterOKed.
        execInfo = position.getEntryOrder().getExecutionInfo()   
        portfolio = self.getResult()
        cash = self.getBroker().getCash()     
        self.info("onEnterOk().symbol:%s" % (instrument))        
        self.info("onEnterOk().current available cash: %.2f,portfolio: %.2f." % (cash,portfolio))
        if isinstance(position, strategy.position.LongPosition):
            self.__lastLongPnl = 0
            self.info("onEnterOK().ExecutionInfo: %s,OPEN LONG %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice())) 
        elif isinstance(position, strategy.position.ShortPosition):
            self.__lastShortPnl = 0
            self.info("onEnterOK().ExecutionInfo: %s,OPEN SHORT %.2f at $%.2f" 
                      % (execInfo.getDateTime(),execInfo.getQuantity(),execInfo.getPrice()))     

    def onEnterCanceled(self, position):
        instrument = position.getInstrument()
        
        self.info("onEnterCanceled().current available cash: %.2f." % (self.getBroker().getCash()))
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition[instrument] = None
            self.info("onEnterCanceled().OPEN LONG cancled.")                                
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition[instrument] = None
            self.info("onEnterCanceled().OPEN SHORT cancled.")
    def onExitOk(self, position):        
        exitInfo = position.getExitOrder().getExecutionInfo()   
        entryInfo = position.getEntryOrder().getExecutionInfo()
        instrument = position.getInstrument()
        
        print 
        currentTime = self.getCurrentDateTime()
        self.info("onExitOk().ExecutionInfo.Current time: %s"%(exitInfo.getDateTime()))
        self.info("onExitOk().instrument:%s." % (instrument))        

        
        
        exitQuantity  = exitInfo.getQuantity()
        exitPrice     = exitInfo.getPrice()  
        exitAmount    = exitQuantity * exitPrice
        
        entryQuantity = entryInfo.getQuantity()
        entryPrice    = entryInfo.getPrice()
        entryCost     = entryQuantity * entryPrice
        #self.sampleSub01(instrument)
        if isinstance(position, strategy.position.LongPosition):
            positionCost = entryCost
            
            
            longPnl = position.getPnL()
            longCurBarPnl = longPnl - self.__lastLongPnl
            #self.__long_position_pnl[instrument].appendWithDateTime(currentTime,longCurBarPnl)
            self.__long_exitBar_pnl[instrument] = longCurBarPnl
            self.longPosition[instrument] = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE LONG %.2f at $%.2f" % (exitInfo.getDateTime(),exitQuantity,exitPrice))                    
        elif isinstance(position, strategy.position.ShortPosition):
            positionCost = entryCost
            
            
            shortPnl = position.getPnL()
            shortCurBarPnl = shortPnl - self.__lastShortPnl
            #self.__long_position_pnl[instrument].appendWithDateTime(currentTime,longCurBarPnl)
            self.__short_exitBar_pnl[instrument] = shortCurBarPnl
            self.shortPosition[instrument] = None
            self.info("onExitOk().ExecutionInfo: %s,CLOSE LONG %.2f at $%.2f" % (exitInfo.getDateTime(),exitQuantity,exitPrice))               
                             
    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        if isinstance(position, strategy.position.LongPosition):
            self.longPosition[instrument] = None
        elif isinstance(position, strategy.position.ShortPosition):
            self.shortPosition[instrument] = None
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
    def closePosition(self):        
        for instrument in self.instruments:
            if(self.longPosition[instrument] is not None and self.sellSignal[instrument] == True
               and not self.longPosition[instrument].exitActive()):
                print
                self.info("onBars().closePosition(), instrument:%s"  % (instrument))                                                    
                self.info("onBars().closePosition(), LONG POSITION to close %.2f"  % (self.longPosition[instrument].getShares()))                                    
                self.longPosition[instrument].exitMarket()
            if(self.shortPosition[instrument] is not None and self.buySignal[instrument] == True
               and not self.shortPosition[instrument].exitActive()):
                print
                self.info("onBars().closePosition(), instrument:%s"  % (instrument))                                                                    
                self.info("onBars().closePosition(), SHORT POSITION to close %.2f"  % (self.shortPosition[instrument].getShares()))  
                self.shortPosition[instrument].exitMarket()          
    def openPosition(self):
        '''mid
        此处是onBars，这个和zipline的概念完全不同
        zipline中，需要覆写的是handle_data，这个东西是个tick概念，所以没有OHLC的，只是个price
        PAT中，每次onBars，都会传入一个newbar的OHLC，此时，要如何按这个OHLC决策，全由你
        依据OHLC做完决策后，可以发送交易指令：
        * Order.Type.MARKET
        * Order.Type.LIMIT
        * Order.Type.STOP
        * Order.Type.STOP_LIMIT
        1.市价单，依据下一个bar的openPrice执行命令：
            self.enterLong()
        2.限价单
        3.止损单市价单
        4.止损限价单

        当前似乎没有止盈单

        在均线策略中，应该在每个newbar到来时，按closePrice的均线计算指标值，然后发送市价单
        1.每个newbar按close价格计算指标，并在下一个bar按open成交
        2.每个newbar按open价格计算指标，并在此newbar按open成交
        以上1,2的计算逻辑是一致的。如果当前bar的close和下一个bar的open相差无几时，两种算法的回测结果也应相差无几
        '''         
        # mid 2)open
        if(self.shortAllowed):
            for instrument in self.instruments:
                self.curInstrument = instrument
                if(self.sellSignal[instrument] == True):
                    # Enter a buy market order. The order is good till canceled.
                    bar = self.getFeed().getLastBar(instrument)
                    volume = 0
                    lastClose = 0
                    if bar is not None:
                        volume = bar.getVolume() 
                        lastClose = bar.getClose()
                    shares = self.money.getShares(strat = self)
                    print
                    self.info("onBars().openPosition(), instrument %s" % (instrument))   
                    self.info("onBars().openPosition(), SHORT POSITION to open %.2f" % (shares))   
                    self.info("onBars().openPosition(), lastClose: %.2f,%.2f" % (self.getLastPrice(instrument),lastClose))  
                    self.info("onBars().openPosition(), need amount: %.2f" % (shares*self.getLastPrice(instrument)))  
                    self.info("onBars().openPosition(), available amount: %.2f." % (self.getBroker().getCash() ))                  
                    self.info("onBars().openPosition(), available volume: %.2f." % (volume))                  
                    self.shortPosition[instrument] = self.enterShort(instrument, shares, True)            
            
        if(self.longAllowed):
            for instrument in self.instruments:
                self.curInstrument = instrument
                if(self.buySignal[instrument] == True):
                    shares = self.money.getShares(strat = self)              
                    print
                    self.info("onBars().openPosition(), instrument %s" % (instrument))   
                    self.info("onBars().openPosition(), LONG POSITION to open %.2f" % (shares) )                
                    self.info("onBars().openPosition(), need amount: %.2f." % (shares*self.getLastPrice(instrument)))                  
                    self.info("onBars().openPosition(), available amount: %.2f." % (self.getBroker().getCash() ))                                    
                    self.longPosition[instrument] = self.enterLong(instrument, shares, True)
    def __analiseEachSymbol(self,instrument):
        dataForCandle = self.dataCenter.getCandleData(dataProvider = self.dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)     
        self.analyzer.analyseEachSymbol(self.results[instrument],dataForCandle,InKLine = self.InKLine)
        
    def __analiseSummary(self):
        dataProvider = self.benchDataProvider
        instrument = self.benchSymbol
        dataForCandle = self.dataCenter.getCandleData(dataProvider = dataProvider,dataStorage = self.storageType,dataPeriod = self.period,
                                                 symbol = instrument,dateStart=self.timeFrom,dateEnd = self.timeTo)          
        self.analyzer.analyseSummary(self.result,dataForCandle)
    def run(self,timeFrom = None,timeTo = None):
        self.initEa(timeFrom = timeFrom,timeTo = timeTo)
        
        self.initIndicators()
        #self.strat.setUseAdjustedValues(False)
        
        self.initAnalyzer()      
        
        strategy.BacktestingStrategy.run(self)
        
        
        for instrument in self.instruments:
            buy = self.getBuy(instrument)
            sell = self.getSell(instrument)

            position_value = self.getPositionValue(instrument)
            long_volume = self.getLongVolume(instrument)
            short_volume = self.getShortVolume(instrument)
            long_cost = self.getLongCost(instrument)
            long_pnl = self.getLongPnl(instrument)
            short_cost = self.getShortCost(instrument)
            short_pnl = self.getShortPnl(instrument)
            
            self.results[instrument] = pd.DataFrame({'long_volume':list(long_volume),
                                'long_cost':list(long_cost),'long_pnl':list(long_pnl),
                                'short_cost':list(short_cost),'short_pnl':list(short_pnl),
                               'buy':list(buy),'sell':list(sell),'position_value':list(position_value)},
                              columns=['long_volume','long_cost','long_pnl','short_cost','short_pnl','buy','sell','position_value'],
                              index=long_volume.getDateTimes())
            self.addIndicators(instrument)
            #------------------------------------
    
            if(self.toPlotEachSymbol):
                self.__analiseEachSymbol(instrument)
            
        if(self.toPlotSummary):
            portfolio_value = self.getPortfolioValue()
            available_cash = self.getAvailableCash()
            
            self.result = pd.DataFrame({'available_cash':list(available_cash),'portfolio_value':list(portfolio_value)},
                              columns=['available_cash','portfolio_value'],
                              index=portfolio_value.getDateTimes())
            self.__analiseSummary()
        return self.results            
    #mid from ea
    #----------------------------------------------------------------------
    def summary(self):
        return "from %s to %s:returns:%.2f%%,sharpe:%.2f,MaxDrawdown:%.2f%%,Longest drawdown duration:(%s)" % (str(self.timeFrom),str(self.timeTo),
                                                                                                               self.returnsAnalyzer.getCumulativeReturns()[-1] * 100,
                                                                                                               self.sharpeRatioAnalyzer.getSharpeRatio(0.05),
                                                                                                               self.drawdownAnalyzer.getMaxDrawDown() * 100,
                                                                                                               self.drawdownAnalyzer.getLongestDrawDownDuration())
    def detail(self):
        """"""        
        print "-------------------------------------------------------------------------"
        print "Final portfolio value: $%.2f" % self.getResult()
        print "Cumulative returns: %.2f %%" % (self.returnsAnalyzer.getCumulativeReturns()[-1] * 100)
        print "Sharpe ratio: %.2f" % (self.sharpeRatioAnalyzer.getSharpeRatio(0.05))
        print "Max. drawdown: %.2f %%" % (self.drawdownAnalyzer.getMaxDrawDown() * 100)
        print "Longest drawdown duration: (%s)" % (self.drawdownAnalyzer.getLongestDrawDownDuration())

        print
        print "Total trades: %d" % (self.tradesAnalyzer.getCount())
        if self.tradesAnalyzer.getCount() > 0:
            profits = self.tradesAnalyzer.getAll()
            print "Avg. profit: $%2.f" % (profits.mean())
            print "Profits std. dev.: $%2.f" % (profits.std())
            print "Max. profit: $%2.f" % (profits.max())
            print "Min. profit: $%2.f" % (profits.min())
            returns = self.tradesAnalyzer.getAllReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)

        print
        print "Profitable trades: %d" % (self.tradesAnalyzer.getProfitableCount())
        if self.tradesAnalyzer.getProfitableCount() > 0:
            profits = self.tradesAnalyzer.getProfits()
            print "Avg. profit: $%2.f" % (profits.mean())
            print "Profits std. dev.: $%2.f" % (profits.std())
            print "Max. profit: $%2.f" % (profits.max())
            print "Min. profit: $%2.f" % (profits.min())
            returns = self.tradesAnalyzer.getPositiveReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)

        print
        print "Unprofitable trades: %d" % (self.tradesAnalyzer.getUnprofitableCount())
        if self.tradesAnalyzer.getUnprofitableCount() > 0:
            losses = self.tradesAnalyzer.getLosses()
            print "Avg. loss: $%2.f" % (losses.mean())
            print "Losses std. dev.: $%2.f" % (losses.std())
            print "Max. loss: $%2.f" % (losses.min())
            print "Min. loss: $%2.f" % (losses.max())
            returns = self.tradesAnalyzer.getNegativeReturns()
            print "Avg. return: %2.f %%" % (returns.mean() * 100)
            print "Returns std. dev.: %2.f %%" % (returns.std() * 100)
            print "Max. return: %2.f %%" % (returns.max() * 100)
            print "Min. return: %2.f %%" % (returns.min() * 100)    
        print "-------------------------------------------------------------------------"
    def initAnalyzer(self):
        from pyalgotrade.stratanalyzer import sharpe
        from pyalgotrade.stratanalyzer import returns
        from pyalgotrade.stratanalyzer import drawdown
        from pyalgotrade.stratanalyzer import trades        
        # 1.0) 策略结果
        self.returnsAnalyzer = returns.Returns()
        # 1.1) 夏普比率 
        self.sharpeRatioAnalyzer = sharpe.SharpeRatio()
        # 1.2) 
        self.drawdownAnalyzer = drawdown.DrawDown()
        # 1.3)
        self.tradesAnalyzer = trades.Trades()     
        
        self.attachAnalyzer(self.sharpeRatioAnalyzer)
        self.attachAnalyzer(self.returnsAnalyzer)    
        self.attachAnalyzer(self.tradesAnalyzer)   
        self.attachAnalyzer(self.drawdownAnalyzer)    