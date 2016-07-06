import numpy as np
import matplotlib.dates as mpd
import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,os.pardir,os.pardir,'thirdParty','pyqtgraph-0.9.10'))
sys.path.append(xpower)
import pyqtgraph as pg

xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'BaseClass'))
sys.path.append(xpower)
from midBaseAnalyzer import midBaseAnalyzer as midBaseAnalyzer

class Analyzer(midBaseAnalyzer):
    #----------------------------------------------------------------------
    def indicatorsPlot(self,ax):
        """"""
        date = np.array([mpd.date2num(date) for date in self.results.index]) 
        if 'upper' in self.results and 'lower' in self.results and 'middle' in self.results:
            ax.plot(date,self.results.upper)
            ax.plot(date,self.results['lower'])                  
            ax.plot(date,self.results['middle'])      
    def signalPlot(self,ax):
        date = np.array([mpd.date2num(date) for date in self.results.index]) 
        if 'buy' in self.results and 'sell' in self.results:     
            xBuy = np.array([mpd.date2num(date) for date in self.results.ix[self.results.buy].index])         
            yBuy = np.array(self.results['lower'][self.results.buy])            
            for x1,y1 in zip(xBuy,yBuy):
                a1 = pg.ArrowItem(angle=90, tipAngle=60, headLen=5, tailLen=0, tailWidth=5, pen={'color': 'r', 'width': 1})
                ax.addItem(a1)
                a1.setPos(x1,y1)        
                
            xSell = np.array([mpd.date2num(date) for date in self.results.ix[self.results.sell].index])         
            ySell = np.array(self.results['upper'][self.results.sell])            
            for x1,y1 in zip(xSell,ySell):
                a1 = pg.ArrowItem(angle=-90, tipAngle=60, headLen=5, tailLen=0, tailWidth=5, pen={'color': 'g', 'width': 1})
                ax.addItem(a1)
                a1.setPos(x1,y1)                  