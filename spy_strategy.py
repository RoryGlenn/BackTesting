from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime # For datetime objects
import os.path  # To manage paths
import sys      # To find out the script name (in argv[0])
import backtrader as bt

from os import system
system("cls")


class PivotPoint(bt.Indicator):
    lines = ('p', 's1', 's2', 'r1', 'r2',)

    def __init__(self, datas):
        # h = self.data.high(-1)  # previous high
        # l = self.data.low(-1)  # previous low
        # c = self.data.close(-1)  # previous close
        h = datas[0].high
        l = data[0].low
        c = data[0].close


        # self.lines.p = p = (h + l + c) / 3.0

        # p2 = p * 2.0
        # self.lines.s1 = p2 - h  # (p x 2) - high
        # self.lines.r1 = p2 - l  # (p x 2) - low

        # hilo = h - l
        # self.lines.s2 = p - hilo  # p - (high - low)
        # self.lines.r2 = p + hilo  # p + (high - low)

        ##############################
        self.p = p = (h + l + c) / 3.0

        p2 = p * 2.0
        self.s1 = p2 - h  # (p x 2) - high
        self.r1 = p2 - l  # (p x 2) - low

        hilo = h - l
        self.s2 = p - hilo  # p - (high - low)
        self.r2 = p + hilo  # p + (high - low)        
        ##############################



class TestStrategy(bt.Strategy):
    lines = ('macd', 'signal', 'histo',)
    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )

              

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order    = None
        self.buyprice = None
        self.buycomm  = None
        self.price_to_sell = None
        self.minimize_loss_price = None
        self.pp = PivotPoint(datas=self.datas)
        


        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
        # bt.indicators.StochasticSlow(self.datas[0])
        

        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)


        rsi = bt.indicators.RSI(self.datas[0])
        self.rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0]).plot = False

        self.macd_histogram = self.macd.macd - self.macd.signal



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


    # region [blue]
    def ppsr(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:

            # Check if we are in the market
            if not self.position:
                if current_price < self.pp.s1:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.15)
            else:
                if current_price >= self.price_to_sell:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region        




    # region [blue]
    def macd_strategy(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]


        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            if (self.macd_histogram[0] < 1):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order    = self.buy()
                self.buyprice = self.dataclose[0]

                # sell at least 15% higher than bought price
                self.price_to_sell = self.buyprice + (self.buyprice * 0.15)
        else:
            if (current_price >= self.price_to_sell):# or (self.rsi[0] > 70):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
            


    # end region



    def rsi_strategy(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            if self.rsi <= 40:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order    = self.buy()
                self.buyprice = self.dataclose[0]

                # sell at least 15% higher than bought price
                self.price_to_sell = self.buyprice + (self.buyprice * 0.15)
        else:
            if (self.rsi >= 60) and (current_price >= self.price_to_sell):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                
                # stop loss
                self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)


    def buy_and_hold(self):
        if not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
            self.buyprice = self.dataclose[0]

    # region [red]
    def next(self):
        self.buy_and_hold()
        # self.ppsr()
        # self.macd_strategy()
        # self.rsi_strategy()
    # end region


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath, 'SPY.csv')
    datapath = os.path.join(modpath, 'ACRX.csv')


    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(1993, 1, 29),
            todate=datetime.datetime(2021, 3, 5),
            reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()


    percent_gained = ( cerebro.broker.getvalue() / starting_cash) * 100

    # Print out the final result
    print('Final Portfolio Value: ${:,.2f}'.format(cerebro.broker.getvalue()))
    print("Percent gained:        %{:,.2f}".format(round(percent_gained, 1)))

    # Plot the result
    cerebro.plot()



#SPY
# highest percent with rounding: %1,590.20
# Final Portfolio Value:         $15,902.41
# Percent gained:                %1,590.20
