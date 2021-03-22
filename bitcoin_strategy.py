from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime
import sys      # To find out the script name (in argv[0])
import os
from os import system
import os.path  # To manage paths
import sys
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
        self.buyprice      = 0
        self.buycomm       = None
        self.price_to_sell = None
        self.biggest_win   = None
        self.biggest_lose  = None
        self.total_buys    = 0
        self.total_sells   = 0
        self.prev_macd = 0

        self.dataclose = self.datas[0].close

        # Indicators for the plotting show
        # self.ema_red_line = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25) # Red
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True         # Blue
        # self.wma_blue_line = bt.indicators.WeightedMovingAverage(self.datas[0], period=25)


        self.ema_long = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)  
        self.ema_short = bt.indicators.ExponentialMovingAverage(self.datas[0], period=12) 

        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)

        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)

        # self.rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.ATR(self.datas[0]).plot = False

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
                        self.order    = self.buy()
                        self.buyprice = self.dataclose[0]
                        self.total_buys += 1

                        # sell at least 10% higher than bought price
                        self.price_to_sell = self.buyprice + (self.buyprice * 0.01)
                else:
                    if current_price > self.PivotPoints.ppsr_df['r2'][self.pp_counter] and current_price > self.price_to_sell:
                        self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
                        self.total_sells += 1
        
            self.pp_counter += 1
        self.PivotPoints.warmup = True
    # end region        




    # region [blue]
    def macd_strategy(self):
        current_price = self.dataclose[0]

        #account for trading cost
        potential_profit = current_price - self.buyprice
        trade_fee        = current_price * 0.001

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if not self.order:
            # Check if we are in the market
            if not self.position:
                if self.macd_histogram[0] >= 0.10:
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.01)
            else:
                if self.macd_histogram[0] < 0.10:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
        
        # self.prev_macd = self.macd.macd[0]

        
    # end region




    # region [blue]
    def rsi_strategy(self):
        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                if self.rsi <= 64:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.rsi >= 70 and current_price >= self.price_to_sell:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region



    """
    Keep track of sell price when you put a stop loss in
    If the price dipped by 2% which triggered the sell, but then the price rose immediately after the sell, buy again immediately

    """

    # region [blue]
    def hybrid_strategy(self):
        # Simply log the closing price of the series from the reference

        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                if self.rsi <= 51:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.macd_histogram[0] >= 4 and current_price >= self.price_to_sell:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region



    # region [blue]
    def buy_and_hold(self):
        if not self.position:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy()
            self.buyprice = self.dataclose[0]
    # end region





    # region [blue]
    def moving_averages(self):
        # self.ema_red_line  # Red
        # self.wma_blue_line # Blue

        if not self.order:
            if not self.position:
                if self.wma_blue_line[0] > self.ema_red_line[0]:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
            else:
                if self.wma_blue_line[0] < self.ema_red_line[0]:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02) 
    # end region



    # region [blue]
    def exponential_averages(self):

        line = self.ema_long[0] + (self.ema_long[0] * 0.0008)

        if not self.order:
            if not self.position:
                # if self.ema_short[0] > self.ema_long[0]:
                if self.ema_short[0] > line:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
            else:
                if self.ema_short[0] < self.ema_long[0]:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02) 
    # end region





    # region [red]
    def next(self):
        # self.buy_and_hold()
        self.macd_strategy()
        # self.rsi_strategy()
        # self.ppsr()
        # self.hybrid_strategy()
        # self.moving_averages()
        # self.exponential_averages()
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
    # cerebro.broker.setcommission(commission=0)
    binance_trade_fee = 0.00075
    relative_trade_fee = cerebro.broker.getvalue() * binance_trade_fee
    cerebro.broker.setcommission(commission=relative_trade_fee, margin=True)

    # Run over everything
    cerebro.run()

    percent_gained           = (cerebro.broker.getvalue() / starting_cash) * 10
    average_percent_per_year = percent_gained / get_total_backtested_years(filename)

    # Print out the final result
    print()
    print(Color.WARNING + "Starting Portfolio Value:    ${:,.2f}".format(starting_cash) + Color.ENDC)
    print(Color.OKGREEN + Color.UNDERLINE + 'Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()) + Color.ENDC)
    print("Total Backtested Years:      " + str(get_total_backtested_years(filename)))


    cerebro.plot()


# Starting Portfolio Value:    $1,000.00
# Final Portfolio Value:       $133,752.44
# Total Percent gained:        %13,375.24
# Average Percent Per Year:    %2,057.73
# Total Backtested Years:      6.5