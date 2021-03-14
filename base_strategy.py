from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import argparse
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.utils.flushfile
import datetime
import backtrader as bt
import datetime # For datetime objects
import sys      # To find out the script name (in argv[0])
import backtrader as bt
import os
import sys
import os.path  # To manage paths
from os import system
system("cls")
print()
g_profit_list            = list()
g_loss_list              = list()
g_trade_per_account_list = list()
        

class PivotPoints(bt.SignalStrategy):
    params = (('usepp1', False), ('plot_on_daily', False))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))    

    def __init__(self):
        self.pp = bt.ind.PivotPoint(self.data1)



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


        # To keep track of pending orders and buy price/commission
        self.order         = None
        self.buyprice      = None
        self.buycomm       = None
        self.price_to_sell = None
        self.biggest_win   = None
        self.biggest_lose  = None

        self.dataclose = self.datas[0].close
        # self.pp = bt.ind.PivotPoint(self.data1)
        self.pp = PivotPoints()

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
        # bt.indicators.StochasticSlow(self.datas[0])

        self.macd = bt.indicators.MACD(self.data, 
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)

        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)

        self.rsi = bt.indicators.RSI(self.datas[0])
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
        global g_profit_list
        global g_loss_list
        global g_trade_per_account_list

        if not trade.isclosed:
            return

        self.log( 'OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm) )

        trade_per_accountValue = "$" + str(round(trade.pnl, 1)) + " %" + str(100 * round(trade.pnl / self.broker.getvalue(), 2))
        g_trade_per_account_list.append(trade_per_accountValue)

        # we profitted or lost
        # percentage of our profit or loss compared to total cash
        if trade.pnl > 0:
            g_profit_list.append(trade.pnl)
        elif trade.pnl <= 0:
            g_loss_list.append(trade.pnl)
        else:
            pass # should never happen




    # region [blue]
    def ppsr(self):
        self.log('Close, %.2f' % self.dataclose[0])
        current_price = self.dataclose[0]

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:

            # Check if we are in the market
            if not self.position:

                if current_price < self.pp.s1:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy()
                    self.buyprice = self.dataclose[0]

                    # sell at least 10% higher than bought price
                    # self.price_to_sell = self.buyprice + (self.buyprice *ten_percent)
            else:
                if current_price > self.pp.r1:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(
                        exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region        



    # region [blue]
    def macd_strategy(self):
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]
        ten_percent   = 0.10

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:

            # Check if we are in the market
            if not self.position:
            
                if self.macd_histogram[0] >= 0.01:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]

                    # sell at least 10% higher than bought price
                    self.price_to_sell = self.buyprice + (self.buyprice *ten_percent)
            
            else:
                if self.macd_histogram[0] < ten_percent or current_price >= self.price_to_sell:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region


    def rsi_strategy(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:
            # Check if we are in the market
            if not self.position:
                if self.rsi <= 35:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.10)
            else:
                if self.rsi >= 60:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
        

    def buy_and_hold(self):
        if not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
            self.buyprice = self.dataclose[0]
            

    # region [red]
    def next(self):
        # self.buy_and_hold()
        self.ppsr()
        # self.macd_strategy()
        # self.rsi_strategy()
    # end region


"""
Works with .csv file format only.
This function is accurate with crypto only because crypto runs 7 days a week.
Stocks run 5 days and this function does not account for that
"""
def get_total_backtested_years(filename):
    second_line = ""
    last_line   = ""
    with open(filename, "r") as file:
        lines = file.readlines()
        second_line = lines[1].replace("-", "")
        last_line = lines[-1].replace("-", "")

    time_start_year  = int(second_line[:4])
    time_start_month = int(second_line[4:6])
    time_start_day   = int(second_line[6:8])

    time_end_year  = int(last_line[:4])
    time_end_month = int(last_line[4:6])
    time_end_day   = int(last_line[6:8])

    time_start = datetime.datetime(time_start_year, time_start_month, time_start_day)
    time_end   = datetime.datetime(time_end_year, time_end_month, time_end_day)

    days_total  = time_end - time_start
    years_total = days_total.days / 365
    return round(years_total, 1)


if __name__ == '__main__':
    
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    filename = 'ETH-USD.csv'
    modpath  = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, filename)

    start_year  = 2011
    start_month = 2
    start_day   = 14

    end_year  = 2021
    end_month = 3
    end_day   = 8

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(start_year, start_month, start_day),
            todate=datetime.datetime(end_year, end_month, end_day),
            reverse=False)


    # First add the original data - smaller timeframe
    cerebro.adddata(data)

    # tframes = dict(daily=bt.TimeFrame.Days, weekly=bt.TimeFrame.Weeks, monthly=bt.TimeFrame.Months)

    # data2 = bt.feeds.BacktraderCSVData(dataname=datapath)
    
    # And then the large timeframe
    # cerebro.adddata(data2)

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

    percent_gained           = (cerebro.broker.getvalue() / starting_cash) * 100
    average_percent_per_year = percent_gained / get_total_backtested_years(filename)

    # Print out the final result
    print()
    print('Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()))
    print("Total Percent gained:        %{:,.2f}".format(round(percent_gained, 1)))
    print("Average Percent Per Year:    %{:,.2f}".format(average_percent_per_year))
    print("Time span " + str(get_total_backtested_years(filename)) + " years")

    cerebro.plot()
