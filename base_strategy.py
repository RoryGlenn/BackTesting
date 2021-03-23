from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime # For datetime objects
import backtrader as bt
from os import system
import pandas as pd
from time import time
system("cls")
print()

g_profit_list            = list()
g_loss_list              = list()
g_trade_per_account_list = list()
        


class PivotPoints():

    def __init__(self, data):
        self.closes = data.close
        self.opens = data.open
        self.highs = data.high
        self.lows = data.low
        self.warmup = False

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




class BaseStrategies(bt.Strategy):
    lines = ('macd', 'signal', 'histo', 'k', 'd', 'mystoc',)
    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
        
        ('k_period', 14),   # lookback period for highest/lowest
        ('d_period', 3),    # smoothing period for d with the SMA
    
    
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order         = None
        self.buyprice      = 0
        self.buycomm       = None
        self.price_to_sell = None
        self.total_buys    = 0
        self.total_sells   = 0
        self.profitable_trades = 0
        self.losing_trades     = 0

        self.dataclose = self.datas[0].close
        # print(self.datas[0].close[-1]) # third to the last entry
        # print(self.datas[0].close[0])  # second to the last
        # print(self.datas[0].close[1])  # gets the first data entry
        

        # data = self.datas[0]
        # self.PivotPoints = PivotPoints(data)
        # self.pp_counter = 0

        self.ema_long  = bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)  
        self.ema_short = bt.indicators.ExponentialMovingAverage(self.datas[0], period=12)

        # Manual set-up of the lookback period during __init__ with addminperiod
        self.addminperiod(self.p.k_period + self.p.d_period)
        self.stoc_slow = bt.indicators.StochasticSlow(self.datas[0])
        self.stoc_fast = bt.indicators.StochasticFast(self.datas[0])

        self.macd = bt.indicators.MACD(self.data,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)


        self.rsi = bt.indicators.RSI(self.datas[0])

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
        # g_trade_per_account_list.append(trade_per_accountValue)

        # we profitted or lost
        if trade.pnl > 0:
            self.profitable_trades+=1
            g_profit_list.append("$" + str(round(trade.pnl, 1)) + " %" + str(100 * round(trade.pnl / self.broker.getvalue(), 2)))
        else:
            self.losing_trades+=1
            g_loss_list.append("$" + str(round(trade.pnl, 1)) + " %" + str(100 * round(trade.pnl / self.broker.getvalue(), 2)))

        
    def print_trades(self):
        global g_profit_list
        global g_loss_list

        print("profitable trades: ", self.profitable_trades)
        print("losing trades:     ", self.losing_trades)

        print("profitable trades:")
        for i in g_profit_list:
            print(i)

        print()
        print("losing trades:")
        for i in g_loss_list:
            print(i)


    # region [blue]
    def ppsr(self):
        # self.log('Close, %.2f' % self.dataclose[0])
        
        current_price = self.dataclose[0]

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
                if self.macd_histogram[0] >= 0:
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.01)
            else:
                if self.macd_histogram[0] < 0:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
        
        # self.prev_macd = self.macd.macd[0]

        
    # end region




    # region [blue]
    def rsi_strategy(self):
        # Simply log the closing price of the series from the reference

        current_price = self.dataclose[0]

        if not self.order:
            if not self.position:
                if self.rsi <= 35:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
                    self.price_to_sell = self.buyprice + (self.buyprice * 0.05)
            else:
                if self.rsi >= 65:
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
                if self.macd_histogram[0] >= 4: #and current_price >= self.price_to_sell:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)
    # end region



    # region [blue]
    def buy_and_hold(self):
        if not self.position:
            self.order = self.buy()
            self.buyprice = self.dataclose[0]
    # end region




    # region [blue]
    def exponential_averages(self):
        if not self.order:
            if not self.position:
                if self.ema_short[0] > self.ema_long[0]:
                    self.order         = self.buy()
                    self.buyprice      = self.dataclose[0]
            else:
                if self.ema_short[0] < self.ema_long[0]:
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02) 
    # end region



    def stochastic_fast(self):
        """
        Stochastic Fast
        # %K = (Current Close — Lowest Low (x periods ago))/(Highest High (x periods ago) — Lowest Low (x periods ago)) * 100
        # %D = y-day SMA of %K
        """

        if not self.order:
            if not self.position:
                if self.stoc_fast.percK[0] > self.stoc_fast.percD[0] + (self.stoc_fast.percD[0] * 0.005):
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
            else:
                if self.stoc_fast.percK[0] < self.stoc_fast.percD[0] -  (self.stoc_fast.percD[0] * 0.005):
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)


    def stochastic_slow(self):
        """
        Slow Stochastic Oscillator:
        
        Slow %K = Fast %K smoothed with 3-period SMA
        Slow %D = 3-period SMA of Slow %K
        """


        if not self.order:
            if not self.position:
                if self.stoc_slow.percK[0] > self.stoc_slow.percD[0] + (self.stoc_slow.percD[0] * 0.005):
                    self.order    = self.buy()
                    self.buyprice = self.dataclose[0]
            else:
                if self.stoc_slow.percK[0] < self.stoc_slow.percD[0] -  (self.stoc_slow.percD[0] * 0.005):
                    self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)


def get_total_backtested_years(filename):
    """
    Works with .csv file format only.
    This function is accurate with crypto only because crypto runs 7 days a week.
    Stocks run 5 days and this function does not account for that
    """    
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


def print_time_elapsed(start_time) -> None:
    end_time = time()
    total_time = end_time - start_time
    seconds = int(total_time) % 60
    minutes = int(total_time // 60) % 60
    hours = int(total_time // 3600) % 60
    print(f"Time elapsed {hours} hour {minutes} minutes {seconds} seconds\n")