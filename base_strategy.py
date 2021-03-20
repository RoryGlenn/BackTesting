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
import pandas as pd

system("cls")
print()

g_profit_list            = list()
g_loss_list              = list()
g_trade_per_account_list = list()
        

class Color:
    HEADER    = '\033[95m'
    OKBLUE    = '\033[94m'
    OKCYAN    = '\033[96m'
    OKGREEN   = '\033[92m'
    WARNING   = '\033[93m'
    FAIL      = '\033[91m'
    ENDC      = '\033[0m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'


class PivotPoints():
    # params = (('usepp1', False), ('plot_on_daily', False))

    # def log(self, txt, dt=None):
    #     ''' Logging function for this strategy'''
    #     dt = dt or self.datas[0].datetime.date(0)
    #     print('%s, %s' % (dt.isoformat(), txt))    

    def __init__(self, data):
        self.closes = data.close
        self.opens = data.open
        self.highs = data.high
        self.lows = data.low
        self.warmup = False
        # self.dates = data.datetime.date(-2369)

        date_list  = list()
        open_list  = list()
        high_list  = list()
        close_list = list()
        low_list   = list()

        for i in range(-2369, 0):
            date_list.append(str(data.datetime.date(i)))

        # even though there are 2377 entries in the excel, it will only print up to 2371 and will not read the very last entry
        # we also start with 1 and not 0, i know, its weird...
        for i in range(1, 2370):
            close_list.append(self.closes[i])
            open_list.append(self.opens[i])
            high_list.append(self.highs[i])
            low_list.append(self.lows[i])

        dohlc_dict = { 'Date': date_list, 'Open': open_list, 'High': high_list, 'Low': low_list, 'Close': close_list }

        self.s2 = list()
        self.s1 = list()
        self.pp = list()
        self.r1 = list()
        self.r2 = list()
        date_list = list()

        for i in range(0, len(dohlc_dict['High'])-1):
            date_list.append(dohlc_dict['Date'][i+1])
            p = (dohlc_dict['High'][i] + dohlc_dict['Low'][i] + dohlc_dict['Close'][i]) / 3.0
            self.pp.append(p)

            p2 = p * 2.0
            self.s1.append(p2 - dohlc_dict['High'][i])
            self.r1.append(p2 - dohlc_dict['Low'][i])

            hilo = dohlc_dict['High'][i] - dohlc_dict['Low'][i]
            
            self.s2.append(p - hilo)
            self.r2.append(p + hilo)

        self.ppsr_df = pd.DataFrame({'Date':date_list, 's2':self.s2, 's1':self.s1, 'pp':self.pp, 'r1':self.r1, 'r2':self.r2 })
        print(self.ppsr_df)


        




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
        self.total_buys    = 0
        self.total_sells   = 0

        self.dataclose = self.datas[0].close
        # print(self.datas[0].close[-1]) # third to the last entry
        # print(self.datas[0].close[0])  # second to the last
        # print(self.datas[0].close[1])  # gets the first data entry
        

        data = self.datas[0]
        self.PivotPoints = PivotPoints(data)
        self.pp_counter = 0
        

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
                # self.log(
                #         'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #         (order.executed.price,
                #         order.executed.value,
                #         order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            # else:  # Sell
                # self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #          (order.executed.price,
                #           order.executed.value,
                #           order.executed.comm))

            self.bar_executed = len(self)

        # elif order.status in [order.Canceled, order.Margin, order.Rejected]:
        #     self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        global g_profit_list
        global g_loss_list
        global g_trade_per_account_list

        if not trade.isclosed:
            return

        # self.log( 'OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm) )

        trade_per_accountValue = "$" + str(round(trade.pnl, 1)) + " %" + str(100 * round(trade.pnl / self.broker.getvalue(), 2))
        g_trade_per_account_list.append(trade_per_accountValue)

        # we profitted or lost
        if trade.pnl > 0:
            g_profit_list.append(trade.pnl)
        else:
            g_loss_list.append(trade.pnl)



    # region [blue]
    def ppsr(self):
        # self.log('Close, %.2f' % self.dataclose[0])
        
        current_price = self.dataclose[0]

        print("current_price: ", current_price)
        print("Date: ", self.PivotPoints.ppsr_df['Date'][self.pp_counter])
        print("s1: ", self.PivotPoints.ppsr_df['s1'][self.pp_counter])
        print("r1: ", self.PivotPoints.ppsr_df['r1'][self.pp_counter])
        
        print("total buys: ", self.total_buys)
        print("total sells", self.total_sells)
        print()

        if self.PivotPoints.warmup:

            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if not self.order:

                # Check if we are in the market
                if not self.position:

                    if current_price < self.PivotPoints.ppsr_df['s2'][self.pp_counter]:
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
                        self.total_buys += 1

                        # sell at least 10% higher than bought price
                        self.price_to_sell = self.buyprice + (self.buyprice * 0.01)
                else:
                    if current_price > self.PivotPoints.ppsr_df['r2'][self.pp_counter] and current_price > self.price_to_sell:
                        self.log('SELL CREATE, %.2f' % self.dataclose[0])
                        self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
                        self.total_sells += 1
        
            self.pp_counter += 1
        self.PivotPoints.warmup = True
    # end region        



    """
    In our macd strategy, if we could take the slope of the MACD line and 
    sell when once the slope becomes negative for MRNA, then we would profit much more
    """

    # region [blue]
    def macd_strategy(self):
        # self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]
        ten_percent   = 0.10

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:
            # Check if we are in the market
            if not self.position:
                if self.macd_histogram[0] >= 0.01:
                    # self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]

                    # sell at least 10% higher than bought price
                    self.price_to_sell = self.buyprice + (self.buyprice * ten_percent)
            else:
                if self.macd_histogram[0] < ten_percent or current_price >= self.price_to_sell:
                    # self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region




    # region [blue]
    def rsi_strategy(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                if self.rsi <= 35:
                    # self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.rsi >= 65 and current_price >= self.price_to_sell:
                    # self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region





    """
    Keep track of sell price when you put a stop loss in
    If the price dipped by 2% which triggered the sell, but then the price rose immediately after the sell, buy again immediately

    """

    # region [blue]
    def hybrid_strategy(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        current_price = self.dataclose[0]

        print("self.macd_histogram[0]:", self.macd_histogram[0])

        if not self.order:
            if not self.position:
                if self.rsi <= 51:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.macd_histogram[0] >= 4: #and current_price >= self.price_to_sell:
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region



    # region [blue]
    def buy_and_hold(self):
        if not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
            self.buyprice = self.dataclose[0]
    # end region


    # region [red]
    def next(self):
        # self.buy_and_hold()
        self.macd_strategy()
        # self.rsi_strategy()
        # self.ppsr()
        # self.hybrid_strategy()
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
    filename = 'C:\\Users\\Rory Glenn\\Documents\\python_repos\\Stocks\\BackTesting\\BTC-USD.csv'
    
    modpath  = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, filename)

    start_year  = 2011
    start_month = 2
    start_day   = 14

    end_year  = 2021
    end_month = 3
    end_day   = 19

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(start_year, start_month, start_day),
            todate=datetime.datetime(end_year, end_month, end_day),
            reverse=False)

    # First add the original data - smaller timeframe
    cerebro.adddata(data)

    # Set our desired cash start
    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Run over everything
    cerebro.run()

    percent_gained           = (cerebro.broker.getvalue() / starting_cash) * 10
    average_percent_per_year = percent_gained / get_total_backtested_years(filename)

    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.WARNING + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)

    if cerebro.broker.getvalue() < starting_cash:
        print(Color.OKGREEN + Color.BOLD + Color.UNDERLINE + "Total Percent gained:        %-{:,.2f}".format(round(percent_gained, 3)) + Color.ENDC)
        print("Average Percent Per Year:    %-{:,.2f}".format(average_percent_per_year))
    else:
        print(Color.OKGREEN + Color.BOLD + Color.UNDERLINE + "Total Percent gained:        %{:,.2f}".format(round(percent_gained, 3)) + Color.ENDC)
        print("Average Percent Per Year:    %{:,.2f}".format(average_percent_per_year))
    print("Total Backtested Years:      " + str(get_total_backtested_years(filename)))


    cerebro.plot()


# Starting Portfolio Value:    $1,000.00
# Final Portfolio Value:       $133,752.44
# Total Percent gained:        %13,375.24
# Average Percent Per Year:    %2,057.73
# Total Backtested Years:      6.5