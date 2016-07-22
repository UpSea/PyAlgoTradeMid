# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib.dates as mpd
import numpy as np

import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'thirdParty','pyqtgraph-0.9.10'))
sys.path.append(xpower)
import pyqtgraph as pg

from PyQt4 import QtGui,QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

class midBaseAnalyzer():
    """"""
    #----------------------------------------------------------------------
    def __init__(self,Globals=None):
        """
        在XPower中执行时，此类的对象是临时的。
        若作为显示窗体的对象调用时，对象内存在show后需要不被释放
        所以，设置此父对象参数，使本对象和父对象一样长寿。
        在展示某个窗口时，为了使某个弹出窗口可以多次并存弹出，被弹出窗口也需要重复定义并全局化
        """
        self.Globals = Globals
        self.Globals.append(self)
    def addText(self,ax,xAxis,yAxis):        #mid add some y value to ax.
        for x,y in zip(xAxis,yAxis):
            text = '('+str(round(y,3))+')'
            ax.annotate(text,xy=(x,y))   
    #----------------------------------------------------------------------
    def positionValuePlot(self,ax,bDrawText=False):
        """"""
        date = np.array([mpd.date2num(date) for date in self.results.index])  
        if 'position_value' in self.results:
            ax.plot(date,self.results.position_value,pen=(255,255,255))
            ax.scatterAddition(date, self.results.position_value) 
    def positionCostPlot(self,ax,bDrawText=False):  
        if 'position_cost' in self.results:
            position_cost = self.results.position_cost
            date = np.array([mpd.date2num(date) for date in self.results.index]) 
        
            if(True):
                '''mid
                绘制所有日期的坐标
                '''
                ax.plot(date, position_cost,pen=(255,255,255), name="Position cost curve")
                ax.scatterAddition(date, position_cost) 
            else:
                '''mid
                不绘制cost为0的日期的坐标
                '''
                indexOfZero = position_cost[:] == 0
                count = len(position_cost[indexOfZero])
                
                #date[0:count] = position_cost[count]
                
                dateOfNoneZero = date[count:]
                position_costOfNoneZero = position_cost[count:]
                
                ax.plot(dateOfNoneZero,position_costOfNoneZero ,pen=(255,255,255), name="Position cost curve")
                ax.scatterAddition(dateOfNoneZero, position_costOfNoneZero)   
            
    def positionVolumePlot(self,ax,bDrawText=False):  
        if 'position_volume' in self.results:
            position_volume = self.results.position_volume
            date = np.array([mpd.date2num(date) for date in self.results.index]) 
        
            ax.plot(date, position_volume,pen=(255,255,255), name="Position curve")
            ax.scatterAddition(date, position_volume)  
            
    def positionPnlPlot(self,ax,bDrawText=False):
        date = np.array([mpd.date2num(date) for date in self.results.index])
        if 'position_pnl' in self.results:
            position_pnl = np.array(self.results.position_pnl)
            ax.plot(date,position_pnl , pen=(255,255,255), name="Red curve")
            ax.scatterAddition(date, position_pnl)    
        
    def instrumentPnlPlot(self,ax,bDrawText=False):
        date = np.array([mpd.date2num(date) for date in self.results.index])
        if 'position_pnl' in self.results:
            position_pnl = np.array(self.results.position_pnl)
            
            
            ax.plot(date,position_pnl , pen=(255,255,255), name="Red curve")
            ax.scatterAddition(date, position_pnl)       
    #----------------------------------------------------------------------
    def pricePlot(self,ax,bDrawText=False):
        """"""
        date = np.array([mpd.date2num(date) for date in self.results.index]) 
        if 'AAPL' in self.results:
            ax.plot(date,self.results.AAPL)
            ax.scatterAddition(date, self.results.AAPL)

    def initDialogSymbol(self,results=None,KData=None,bDrawText=False,InKLine = False):
        # 1) creates layouts
        dialog = QtGui.QDialog()   
        mainLayout = QtGui.QHBoxLayout()
        rightLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(rightLayout)
        dialog.setLayout(mainLayout)        
        dialog.setWindowTitle(('Strategy Results'))

        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdataUI'))
        sys.path.append(xpower)

        from Widgets.pgCandleWidgetCross import pgCandleWidgetCross
        from Widgets.pgCrossAddition import pgCrossAddition
        from pyqtgraph.dockarea import DockArea,Dock 
        area = DockArea()   
        rightLayout.addWidget(area)

        # 2) creates widgets 
        #  2.1)candle        
        pgCandleView = pgCandleWidgetCross(dataForCandle=KData)        
        self.pricePlot(pgCandleView) 
        if(InKLine):
            self.indicatorsPlot(pgCandleView) 
        #self.signalPlot(pgCandleView,yBuy = KData.take([1],axis=1),ySell = KData.take([1],axis=1))
        self.signalPlot(pgCandleView)
        dCandle = Dock("candles",closable=True, size=(200,300))     ## give this dock the minimum possible size
        area.addDock(dCandle, 'bottom') 
        dCandle.addWidget(pgCandleView)        

        #  2.2)position_pnl 当前position_pnl曲线
        if(True):
            PyqtGraphPnl = pgCrossAddition()
            self.positionPnlPlot(PyqtGraphPnl,bDrawText=bDrawText)
            position_pnl = np.array(self.results.position_pnl)
            self.signalPlot(PyqtGraphPnl,yBuy = position_pnl,ySell = position_pnl)
            dPnl = Dock("position_pnl", closable=True, size=(200,100))
            area.addDock(dPnl, 'bottom')    
            dPnl.addWidget(PyqtGraphPnl)           
            PyqtGraphPnl.setXLink(pgCandleView)
        # 2.3)position_cost 
        if(True):
            PyqtGraphPositionCost = pgCrossAddition()
            self.positionCostPlot(PyqtGraphPositionCost)
            dPositionCost = Dock("position_cost",closable=True, size=(200,100))
            area.addDock(dPositionCost, 'bottom')        
            dPositionCost.addWidget(PyqtGraphPositionCost)             
            PyqtGraphPositionCost.setXLink(pgCandleView)         
        #  2.3)position_volume
        if(False):
            PyqtGraphPosition = pgCrossAddition()
            self.positionVolumePlot(PyqtGraphPosition)
            dPosition = Dock("position_volume",closable=True, size=(200,100))
            area.addDock(dPosition, 'bottom')        
            dPosition.addWidget(PyqtGraphPosition)             
            PyqtGraphPosition.setXLink(pgCandleView)
        #  2.4)portfolio  总资产变动曲线 cash + equity
        if(True):
            PyqtGraphPortfolio = pgCrossAddition()
            self.positionValuePlot(PyqtGraphPortfolio)
            dPortfolio = Dock("portfolio", closable=True,size=(200,100))
            area.addDock(dPortfolio, 'bottom')     
            dPortfolio.addWidget(PyqtGraphPortfolio)        
            PyqtGraphPortfolio.setXLink(pgCandleView)
        #  2.5)indicator
        if(True):
            PyqtGraphindicators = pgCrossAddition()
            self.pricePlot(PyqtGraphindicators)    
            self.indicatorsPlot(PyqtGraphindicators)
            
            self.signalPlot(PyqtGraphindicators)
            
            dIndicator = Dock("indicator",closable=True, size=(200,100))
            dIndicator.addWidget(PyqtGraphindicators)
            area.addDock(dIndicator, 'bottom', dCandle)  
            PyqtGraphindicators.setXLink(pgCandleView)
        #  2.2)position_pnl 当前position_pnl曲线
        if(False):
            PyqtGraphPortfolioInstruments = pgCrossAddition()
            self.instrumentPnlPlot(PyqtGraphPortfolioInstruments,bDrawText=bDrawText)
            position_pnl = np.array(self.results.position_pnl)
            self.signalPlot(PyqtGraphPortfolioInstruments,yBuy = position_pnl,ySell = position_pnl)
            dPnl = Dock("instrumentsPNL", closable=True, size=(200,100))
            area.addDock(dPnl, 'bottom',dPositionCost)    
            dPnl.addWidget(PyqtGraphPortfolioInstruments)           
            PyqtGraphPortfolioInstruments.setXLink(pgCandleView)            
        return dialog
    def analyseEachSymbol(self,results=None,KData=None,bDrawText=False,InKLine = False):
        # Plot the symbol data.
        self.results = results    
        dialog = self.initDialogSymbol(results=results, KData=KData,InKLine = InKLine)
        self.Globals.append(dialog)
        dialog.showMaximized()  
        
        
    #----------------------------------------------------------------------
    def portfolioPlot(self,ax,bDrawText=False):
        """"""
        date = np.array([mpd.date2num(date) for date in self.result.index])  
        if 'portfolio_value' in self.result:
            ax.plot(date,self.result.portfolio_value,pen=(255,255,255))
            ax.scatterAddition(date, self.result.portfolio_value)      #----------------------------------------------------------------------
    def availableCashPlot(self,ax,bDrawText=False):
        """"""
        date = np.array([mpd.date2num(date) for date in self.result.index])  
        if 'available_cash' in self.result:
            ax.plot(date,self.result.available_cash,pen=(255,255,255))
            ax.scatterAddition(date, self.result.available_cash)     
    def initDialogSummary(self,result,KData=None):
        # 1) creates layouts
        dialog = QtGui.QDialog()   
        mainLayout = QtGui.QHBoxLayout()
        rightLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(rightLayout)
        dialog.setLayout(mainLayout)        
        dialog.setWindowTitle(('Strategy Results'))

        import os,sys        
        xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,'midProjects','histdataUI'))
        sys.path.append(xpower)

        from Widgets.pgCandleWidgetCross import pgCandleWidgetCross
        from Widgets.pgCrossAddition import pgCrossAddition
        from pyqtgraph.dockarea import DockArea,Dock 
        area = DockArea()   
        rightLayout.addWidget(area)


        # 2) creates widgets 
        #  2.1)candle        
        pgCandleView = pgCandleWidgetCross(dataForCandle=KData)        
        dCandle = Dock("candles",closable=True, size=(200,300))     ## give this dock the minimum possible size
        area.addDock(dCandle, 'bottom') 
        dCandle.addWidget(pgCandleView)       
        # 2) creates widgets 
        # 2.3)position_cost 
        if(True):
            PyqtGraphPositionCost = pgCrossAddition()
            self.availableCashPlot(PyqtGraphPositionCost)
            dAvailableCash = Dock("available_cash",closable=True, size=(200,100))
            area.addDock(dAvailableCash, 'bottom')        
            dAvailableCash.addWidget(PyqtGraphPositionCost)             
            PyqtGraphPositionCost.setXLink(pgCandleView)         
        # 2.3)position_cost 
        if(True):
            PyqtGraphPositionCost = pgCrossAddition()
            self.portfolioPlot(PyqtGraphPositionCost)
            dPortfolioValue = Dock("portfolio_value",closable=True, size=(200,100))
            area.addDock(dPortfolioValue, 'bottom')        
            dPortfolioValue.addWidget(PyqtGraphPositionCost)             
            PyqtGraphPositionCost.setXLink(pgCandleView) 
        return dialog        
    def analyseSummary(self,result,KData=None):
        # Plot the portfolio data.
        self.result = result    
        dialog = self.initDialogSummary(result=result,KData=KData)
        self.Globals.append(dialog)
        dialog.showMaximized()          
        
