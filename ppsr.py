from __future__ import (absolute_import, division, print_function, unicode_literals)
import argparse
import backtrader as bt
import datetime
import os
import sys
from os import system
system('cls')
print("\n\n\n\n")
print('#'*40)


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

        ##############################
        self.p = p = (h + l + c) / 3.0

        p2 = p * 2.0
        self.s1 = p2 - h  # (p x 2) - high
        self.r1 = p2 - l  # (p x 2) - low

        hilo = h - l
        self.s2 = p - hilo  # p - (high - low)
        self.r2 = p + hilo  # p + (high - low)        
        ##############################


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

        ##############################
        self.p = p = (h + l + c) / 3.0

        p2 = p * 2.0
        self.s1 = p2 - h  # (p x 2) - high
        self.r1 = p2 - l  # (p x 2) - low

        hilo = h - l
        self.s2 = p - hilo  # p - (high - low)
        self.r2 = p + hilo  # p + (high - low)      
        ##############################        



class St(bt.Strategy):
    params = (('usepp1', False), ('plot_on_daily', False))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))


    def __init__(self):
        # if self.p.usepp1:
        #     self.pp = PivotPoint1(self.data1)
        # else:
        #     self.pp = PivotPoint(self.data1)
        

        # To keep track of pending orders and buy price/commission
        self.order    = None
        self.buyprice = None
        self.buycomm  = None
        self.price_to_sell = None

        self.pp = PivotPoint1(self.data1)
        
        self.dataclose = self.datas[0].close

        if self.p.plot_on_daily:
            self.pp.plotinfo.plotmaster = self.data0



    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.executed.price,
                        order.executed.value,
                        order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def next(self):
        txt = ','.join(
                    ['%04d' % len(self),
                    '%04d' % len(self.data0),
                    '%04d' % len(self.data1),
                    self.data.datetime.date(0).isoformat(),
                    '%.2f' % self.pp[0]])

        self.log('Close, %.2f' % self.dataclose[0])
        print("Account value:", cerebro.broker.getvalue())
        current_price = self.dataclose

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:

            # Check if we are in the market
            if not self.position:

                # if current price is below s1, buy
                if current_price < self.pp.s1:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]

                    # sell at least 10% higher than bought price
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.10)
                
            else:
                if current_price > self.pp.r1:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)                



def parse_args():
    parser = argparse.ArgumentParser( formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Sample for pivot point and cross plotting')
    parser.add_argument('--data', required=False, default='SPY.CSV', help='Data to be read in')
    parser.add_argument('--usepp1', required=False, action='store_true', help='Have PivotPoint look 1 period backwards')
    parser.add_argument('--plot', required=False, action='store_true', help=('Plot the result'))
    parser.add_argument('--plot-on-daily', required=False, action='store_true', help=('Plot the indicator on the daily data'))
    return parser.parse_args()



if __name__ == '__main__':
    args = parse_args()
    cerebro = bt.Cerebro()
    # data    = btfeeds.BacktraderCSVData(dataname=args.data)

   # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath =  os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'ACRX.csv')


    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(2011, 2, 14),
            todate=datetime.datetime(2021, 3, 8),
            reverse=False)



    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    cerebro.addstrategy(St, usepp1=args.usepp1, plot_on_daily=args.plot_on_daily)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)
    cerebro.broker.setcommission(commission=0.0)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    percent_gained = ( cerebro.broker.getvalue() / starting_cash) * 100
    ten_years = 10
    average_percent_per_year = percent_gained / ten_years

    # Print out the final result
    print('Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()))
    print("Total Percent gained:        %{:,.2f}".format(round(percent_gained, 1)))
    print("Average Percent Per Year:    %{:,.2f}".format(average_percent_per_year))


    if args.plot:
        cerebro.plot(style='bar')