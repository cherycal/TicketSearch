import datetime
import inspect
import logging
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timedelta

import colorlog
import pytz
# from selenium import webdriver

import push

# DEBUG: Detailed information, typically of interest only when diagnosing problems.

# INFO: Confirmation that things are working as expected.

# WARNING: An indication that something unexpected happened,
# or indicative of some problem in the near future (e.g. ‘disk space low’).
# The software is still working as expected.

# ERROR: Due to a more serious problem, the software has not been able
# to perform some function.

# CRITICAL: A serious error, indicating that the program itself may be
# unable to continue running.

# for webscraping
# try:
# except Exception as ex:
#      print(str(ex))

push_instance = push.Push(calling_function="tools.py")




def get_logger(logfilename='./logs/pushlog.log',
               logformat='\npush.py logger: time=%(asctime)s level=%(levelname)s '
                         'calling_function=%(funcName)s lineno=%(lineno)d\nmsg=%(message)s\n'
                         'calling process path=%(pathname)s\n\n'):
    bold_seq = '\033[1m'
    colorlog_format = (
        f'{bold_seq} '
        '%(log_color)s '
        f'{logformat}'
    )
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'grey',
        'WARNING': 'brown',
        'ERROR': 'red',
        'CRITICAL': 'black,bg_red',
    }
    colorlog.basicConfig(format=colorlog_format, log_colors=log_colors)
    #logfilename = './logs/pushlog.log'
    logger_instance = logging.getLogger(__name__)
    logger_instance.setLevel(logging.DEBUG)

    formatter = logging.Formatter(logformat)
    file_handler = logging.FileHandler(logfilename)
    file_handler.setFormatter(formatter)
    logger_instance.addHandler(file_handler)

    return logger_instance

def print_calling_function():
    print('\n')
    print("Printing calling information (fantasy.py)")
    print("#############################")
    # print(str(inspect.stack()[-2].filename) + ", " + str(inspect.stack()[-2].function) +
    #      ", " + str(inspect.stack()[-2].lineno))
    print(str(inspect.stack()[1].filename) + ", " + str(inspect.stack()[1].function) +
          ", " + str(inspect.stack()[1].lineno))
    # print(str(inspect.stack()[-1].filename) + ", " + str(inspect.stack()[-1].function) +
    #      ", " + str(inspect.stack()[-1].lineno))
    print("#############################")
    return

def get_platform():
    platforms = {
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform

    return f"{platforms[sys.platform]}"


# def get_driver(mode=""):
#     platform = get_platform()
#     options = webdriver.ChromeOptions()
#     driver = ""
#     if mode == "headless":
#         options.add_argument('--headless')
#     if platform == "Windows":
#         driver = webdriver.Chrome('C:/Users/chery/chromedriver.exe', options=options)
#     elif (platform == "linux") or (platform == "Linux"):
#         driver = webdriver.Chrome('/usr/bin/chromedriver', options=options)
#     else:
#         print("Platform " + platform + " not recognized. Exiting.")
#         exit(-1)
#     return driver


def string_from_list(in_list):
    out_string = ""
    for i in in_list:
        if i[-2:] == ": ":
            out_string += i
        else:
            out_string += i + ", "
    out_string = out_string[:-2]
    out_string += '\n'
    return out_string


def tryfunc(func):
    tries = 0
    max_tries = 4
    incomplete = True
    while incomplete and tries < max_tries:
        try:
            func()
            incomplete = False
        except Exception as ex:
            print(str(ex))
            tries += 1
            time.sleep(.5)
            if tries == max_tries:
                print("Process failed: ")
                print("Exception in user code:")
                print("-" * 60)
                traceback.print_exc(file=sys.stdout)
                print("-" * 60)
                push_instance.push("Process failed:", f'Error: {ex}\nFunction: {func}')


def try_wrap(func):
    def tryfunction(*args, **kwargs):
        tries = 0
        max_tries = 3
        while tries < max_tries:
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                print(str(ex))
                # push_instance.push("Attempt failed", str(ex))
                tries += 1
                time.sleep(2)
        if tries == max_tries:
            print("Process failed: ")
            print("Exception in user code:")
            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)

    return tryfunction


def time_diff(start_time, end_time):
    t1 = datetime.strptime(str(start_time), "%H%M%S")
    #print('Start time:', t1.time())

    t2 = datetime.strptime(str(end_time), "%H%M%S")
    #print('End time:', t2.time())

    # get difference
    delta = t2 - t1
    return delta

def unixtime_from_mlb_format(mlbtimestr):
    return datetime.strptime(mlbtimestr, "%Y-%m-%dT%H:%M:%SZ").timestamp()

def unix_gmt():
    nowtime = int(datetime.now().timestamp())
    tzoffset = 3600 * (int(datetime.now(pytz.timezone('America/Tijuana')).strftime("%z")) / -100)
    #print(f'now: {nowtime} txoffset: {tzoffset}')
    return nowtime + tzoffset

def local_time_from_mlb_format(mlbtimestr):
    gmt_game_time = datetime.strptime(mlbtimestr, "%Y-%m-%dT%H:%M:%SZ")
    tzoffset = (int(datetime.now(pytz.timezone('America/Tijuana')).strftime("%z")) / -100)
    game_time = gmt_game_time - timedelta(hours=tzoffset)
    return game_time

def local_hhmmss_from_mlb_format(mlbtimestr):
    gmt_game_time = datetime.strptime(mlbtimestr, "%Y-%m-%dT%H:%M:%SZ")
    tzoffset = (int(datetime.now(pytz.timezone('America/Tijuana')).strftime("%z")) / -100)
    game_time = gmt_game_time - timedelta(hours=tzoffset)
    return game_time.strftime("%H%M%S")


def test_print():
    print("Hello world")
def sleep_phase(sleep_total=60, sleep_interval=5):
    time.sleep(1)
    sleep_remaining = sleep_total
    print("sleep_remaining ", end="", flush=True)
    while sleep_remaining > 0:
        print(f"{str(sleep_remaining)} ", end="", flush=True)
        sleep_remaining -= sleep_interval
        time.sleep(sleep_interval)
    return
class Process(object):

    def __init__(self, logger_instance=None):
        self.db = f'C:\\Ubuntu\\Shared\\data\\Process.db'
        self.conn = sqlite3.connect(self.db, timeout=15)
        self.cursor = self.conn.cursor()
        self.name = "process_instance"
        if logger_instance is None:
            logname = './logs/pushlog.log'
            self.logger_instance = get_logger(logfilename=logname)
        else:
            self.logger_instance = logger_instance

    def execute(self, cmd, verbose=0):
        if verbose:
            print_calling_function()
        self.cursor.execute(cmd)
        self.conn.commit()

    def select(self, query, verbose=0):
        if verbose:
            print_calling_function()
        self.cursor.execute(query)
        self.conn.commit()
        return self.cursor.fetchall()

    def get_process(self):
        return self.name

    def set_process_status(self, calling_function, flag_):
        if calling_function:
            cmd = f"update ProcessStatus set ProcessStatus = {flag_}, " \
                  f"UpdateDate = {datetime.now().strftime('%Y%m%d')}, " \
                  f"UpdateTime = {datetime.now().strftime('%Y%m%d%H%M%S')} " \
                  f"where ProcessName = '{calling_function}'"
            self.logger_instance.info(cmd)
            self.execute(cmd)
            self.logger_instance.info(f"Successfully ProcessStatus to {flag_} for {calling_function}")
            # self.push(title="ProcessStatus",
            #           body=f"Successfully ProcessStatus to {flag_} for {calling_function}")

        return

    def get_process_status(self, calling_function=None):
        status_flag = None
        if calling_function:
            cmd = f"select ProcessStatus from ProcessStatus where ProcessName = '{calling_function}'"
            self.logger_instance.info(cmd)
            d = self.select(cmd)
            status_flag = d[0][0]
        return status_flag

    def get_process_date(self, calling_function=None):
        status_flag = None
        if calling_function:
            cmd = f"select UpdateDate from ProcessStatus where ProcessName = '{calling_function}'"
            self.logger_instance.info(cmd)
            d = self.select(cmd)
            status_flag = d[0][0]
        return status_flag

    def set_slack_timestamp(self, calling_function, timestamp):
        cmd = f"update Slack set " \
              f"TimeStamp = {timestamp} " \
              f"where ProcessName = '{calling_function}'"
        self.logger_instance.info(cmd)
        self.execute(cmd)
        self.logger_instance.info(f"Successfully TimeStamp to {timestamp} for {calling_function}")
        return

    def get_slack_timestamp(self, calling_function):
        cmd = f"select TimeStamp from Slack where ProcessName = '{calling_function}'"
        self.logger_instance.info(cmd)
        d = self.select(cmd)
        timestamp = d[0][0]
        return timestamp
