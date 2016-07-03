import numpy as np
import matplotlib.dates as mpd
import sys,os
xpower = os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'BaseClass'))
sys.path.append(xpower)
from midBaseAnalyzer import midBaseAnalyzer as midBaseAnalyzer

class Analyzer(midBaseAnalyzer):
    #----------------------------------------------------------------------
    def indicatorsPlot(self,ax):
        """"""
        date = np.array([mpd.date2num(date) for date in self.results.index]) 
        if 'short_ema' in self.results and 'long_ema' in self.results:
            ax.plot(date,self.results.short_ema)
            ax.plot(date,self.results['long_ema'])      