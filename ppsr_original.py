from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import argparse
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.utils.flushfile
from pivotpoint import PivotPoint, PivotPoint1
print("\n\n\n")

class PivotPoint1(bt.Indicator):
    lines = ('p', 's1', 's2', 'r1', 'r2',)

    def __init__(self):
        h = self.data.high(-1)  # previous high
        l = self.data.low(-1)  # previous low
        c = self.data.close(-1)  # previous close

        self.lines.p = p = (h + l + c) / 3.0

        p2 = p * 2.0
        self.lines.s1 = p2 - h  # (p x 2) - high
        self.lines.r1 = p2 - l  # (p x 2) - low

        hilo = h - l
        self.lines.s2 = p - hilo  # p - (high - low)
        self.lines.r2 = p + hilo  # p + (high - low)


class PivotPoint(bt.Indicator):
    lines = ('p', 's1', 's2', 'r1', 'r2',)
    plotinfo = dict(subplot=False)

    def __init__(self):
        h = self.data.high  # current high
        l = self.data.low  # current high
        c = self.data.close  # current high

        self.lines.p = p = (h + l + c) / 3.0

        p2 = p * 2.0
        self.lines.s1 = p2 - h  # (p x 2) - high
        self.lines.r1 = p2 - l  # (p x 2) - low

        hilo = h - l
        self.lines.s2 = p - hilo  # p - (high - low)
        self.lines.r2 = p + hilo  # p + (high - low)



class St(bt.Strategy):
    params = (('usepp1', False),
              ('plot_on_daily', False))

    def __init__(self):

        if self.p.usepp1:
            self.pp = PivotPoint1(self.data1)
        else:
            self.pp = PivotPoint(self.data1)

        if self.p.plot_on_daily:
            self.pp.plotinfo.plotmaster = self.data0


    def next(self):
        # self = current day we are calculating
        # self.data0 = yesterday
        # self.data1 = month
        # self.pp[0] = the current pivot point for today

        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%.2f' % self.pp[0]])

        print(txt)


def runstrat():
    args = parse_args()

    cerebro = bt.Cerebro()
    data = btfeeds.BacktraderCSVData(dataname=args.data)
    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    cerebro.addstrategy(St,
                        usepp1=args.usepp1,
                        plot_on_daily=args.plot_on_daily)
    cerebro.run()
    
    cerebro.plot(style='bar')


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Sample for pivot point and cross plotting')

    parser.add_argument('--data', required=False,
                        default='ETH-USD.csv',
                        help='Data to be read in')

    parser.add_argument('--usepp1', required=False, action='store_true',
                        help='Have PivotPoint look 1 period backwards')

    parser.add_argument('--plot', required=False, action='store_true',
                        help=('Plot the result'))

    parser.add_argument('--plot-on-daily', required=False, action='store_true',
                        help=('Plot the indicator on the daily data'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()        