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
        if 'long_ema' in self.results and 'short_ema' in self.results:
            ax.plot(date,self.results['long_ema'])                  
            ax.plot(date,self.results['short_ema'])      

    def signalPlot(self,ax,yBuy = None,ySell = None):
        date = np.array([mpd.date2num(date) for date in self.results.index]) 
        if 'buy' in self.results and 'sell' in self.results:   

            if(yBuy == None or ySell == None):
                if 'long_ema' in self.results and 'long_ema' in self.results:   
                    yBuy = np.array(self.results['long_ema'][self.results.buy])        
                    ySell = np.array(self.results['long_ema'][self.results.sell])            
                               
                #yBuy = np.array(self.results.long_ema)
                #ySell = np.array(self.results.long_ema)
                
            if(yBuy is not None or ySell is not None):
                if 'long_ema' in self.results and 'long_ema' in self.results:   
                    xBuy = np.array([mpd.date2num(date) for date in self.results.ix[self.results.buy].index])    
                    for x1,y1 in zip(xBuy,yBuy):
                        a1 = pg.ArrowItem(angle=90, tipAngle=60, headLen=5, tailLen=0, tailWidth=5, pen={'color': 'r', 'width': 1})
                        ax.addItem(a1)
                        a1.setPos(x1,y1)        
                    xSell = np.array([mpd.date2num(date) for date in self.results.ix[self.results.sell].index])         
                    for x1,y1 in zip(xSell,ySell):
                        a1 = pg.ArrowItem(angle=-90, tipAngle=60, headLen=5, tailLen=0, tailWidth=5, pen={'color': 'g', 'width': 1})
                        ax.addItem(a1)
                        a1.setPos(x1,y1)                  
