from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import argparse
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.utils.flushfile
import datetime
import backtrader as bt
from matplotlib.pyplot import axis
import pandas as pd
from os import system
system("cls")

g_profit_list            = list()
g_loss_list              = list()
g_trade_per_account_list = list()
g_count = 0

#####################################
class PPSR():
    def __init__(self) -> None:
        self.warmup     = False
        self.df         = pd.read_csv(get_default_filename())
        self.ppsr_lines = pd.DataFrame()
        self.df_counter = 0

    def calc_ppsr_lines(self) -> None:
        global g_count 

        pp_list = list()
        s1_list = list()
        s2_list = list()
        r1_list = list()
        r2_list = list()

        for i in range(0, len(self.df['High'])):

            h = self.df['High'][i].item()
            l = self.df['Low'][i].item()
            c = self.df['Close'][i].item()

            p = (h + l + c) / 3.0
            pp_list.append((h + l + c) / 3.0)

            p2 = p * 2.0
            s1_list.append(p2 - h)  # (p x 2) - high
            r1_list.append(p2 - l)  # (p x 2) - low

            hilo = h - l
            
            s2_list.append(p - hilo)  # p - (high - low)
            r2_list.append(p + hilo)  # p + (high - low)

        self.ppsr_lines = pd.DataFrame( {'s1':s1_list, 's2':s2_list, 'pp':pp_list, 'r1':r1_list, 'r2':r2_list})

#####################################


class St(bt.SignalStrategy):

    params = (('usepp1', False), ('plot_on_daily', False))

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        self.order    = None
        self.buyprice = None
        self.buycomm  = None
        self.price_to_sell = None
        self.biggest_win   = None
        self.biggest_lose  = None        
        
        self.dataclose = self.datas[0].close
        self.pp = bt.ind.PivotPoint(self.data0)
        self.PPSR = PPSR()
        self.PPSR.calc_ppsr_lines()


    def next(self):
        txt = ','.join(
            ['%04d' % len(self),
             '%04d' % len(self.data0),
             '%04d' % len(self.data1),
             self.data.datetime.date(0).isoformat(),
             '%04d' % len(self.pp),
             '%.2f' % self.pp[0]])
        print(txt)


        self.log('Close, %.2f' % self.dataclose[0])
        current_price = self.dataclose[0]
        i = self.PPSR.df_counter - 1 

        if self.PPSR.warmup: 

            print("self.PPSR.ppsr_lines['pp'][i]: ", self.PPSR.ppsr_lines['pp'][i] )


            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if not self.order:

                # Check if we are in the market
                if not self.position:
                    if current_price <= self.PPSR.ppsr_lines['s1'][i]:
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        self.order = self.buy()
                        self.buyprice = self.dataclose[0]

                        # sell at least 10% higher than bought price
                        self.price_to_sell = self.buyprice + (self.buyprice * 0.10)
                else:
                    if current_price >= self.price_to_sell:
                        self.log('SELL CREATE, %.2f' % self.dataclose[0])
                        self.order = self.sell(exectype=bt.Order.StopTrail, trailamount=0.02)

        self.PPSR.warmup = True
        self.PPSR.df_counter += 1


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


def get_default_filename():
    return "ETH-USD.csv"


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



def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Sample for pivot point and cross plotting')
    parser.add_argument('--data', required=False, default=get_default_filename(), help='Data to be read in')
    parser.add_argument('--plot', required=False, action='store_true', default=True, help=('Plot the result'))
    parser.add_argument('--plot-on-daily', required=False,action='store_true', help=('Plot the indicator on the daily data'))
    return parser.parse_args()


def runstrat():

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
            dataname=get_default_filename(),
            fromdate=datetime.datetime(2015, 8, 7),
            todate=datetime.datetime(2021, 3, 13),
            reverse=False)


    cerebro = bt.Cerebro()
    # data = btfeeds.BacktraderCSVData(dataname=args.data)


    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Months)

    starting_cash = 1000.0
    cerebro.broker.setcash(starting_cash)
    # cerebro.signal_accumulate(True)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.AllInSizer)
    cerebro.broker.setcommission(commission=0.0)
    cerebro.addstrategy(St, plot_on_daily=True)

    # Print out the starting conditions
    cerebro.run(runonce=False)

    percent_gained           = (cerebro.broker.getvalue() / starting_cash)
    average_percent_per_year = percent_gained / get_total_backtested_years(get_default_filename())

    # Print out the final result
    print()
    print('Starting Portfolio Value:    ${:,.2f}'.format(starting_cash))
    print('Final Portfolio Value:       ${:,.2f}'.format(cerebro.broker.getvalue()))
    print("Total Percent gained:        %{:,.2f}".format(round(percent_gained, 2)))
    print("Average Percent Per Year:    %{:,.2f}".format(average_percent_per_year))
    print("Time span " + str(get_total_backtested_years(get_default_filename())) + " years")

    cerebro.plot(style='bar')



if __name__ == '__main__':
    runstrat()
