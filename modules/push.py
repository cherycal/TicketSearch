__author__ = 'chance'

import inspect
import logging
import os
import smtplib
import sqlite3
import time
from datetime import datetime
from email.mime.text import MIMEText

import colorlog
# import dataframe_image as dfi
# import pandas as pd
# import tweepy
# from pushbullet import PushBullet
from pyfcm import FCMNotification
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_api_token = os.environ["SLACK_BOT_TOKEN"]
slack_alerts_channel = os.environ["SLACK_ALERTS_CHANNEL"]
slack_requests_channel = os.environ["SLACK_CHANNEL"]
slack_scoreboard_channel = os.environ["SLACK_SCOREBOARD_CHANNEL"]
slack_client = WebClient(token=slack_api_token)

# TWITTER KEYS
APIKEY = os.environ.get('APIKEY')
APISECRETKEY = os.environ.get('APISECRETKEY')
ACCESSTOKEN = os.environ.get('ACCESSTOKEN')
ACCESSTOKENSECRET = os.environ.get('ACCESSTOKENSECRET')
SE = f"{os.environ.get('GMA')}@gmail.com"
SP = os.environ.get('GMPY')
SN = f"{str(int(os.environ.get('PN')) - 4)}@vtext.com"

# PUSHBUCKET
PBTOKEN = os.environ.get('PBTOKEN')

# SLACK ( DECOMMISSIONED 20230416 )
SLACK_URL_SUFFIX = os.environ.get('slack_url_suffix')

########################################################################################################################
REG_ID = os.environ.get('reg_id')
API_KEY = os.environ.get('api_key')


########################################################################################################################

def ordinal(n):
    if 10 <= n % 100 < 20:
        return str(n) + 'th'
    else:
        return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, "th")


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
        'INFO': 'green',
        'WARNING': 'yellow',
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
    # print(str(inspect.stack()[1].filename) + ", " + str(inspect.stack()[1].function) +
    #       ", " + str(inspect.stack()[1].lineno))
    print(inspect.stack())
    # print(str(inspect.stack()[-1].filename) + ", " + str(inspect.stack()[-1].function) +
    #      ", " + str(inspect.stack()[-1].lineno))
    print("#############################")
    return


def print_stack():
    stack = list()
    inspect_stack = inspect.stack().copy()
    for item in inspect_stack:
        if item.function != 'execfile':
            stack.insert(0, f"{item.filename}:{item.lineno}:{item.function}")
    return stack


def push_attachment(attachment, channel="None", body="None"):
    res = False
    use_channel = slack_alerts_channel
    if channel:
        use_channel = channel
    try:
        file_response = slack_client.files_upload_v2(
            channel=use_channel,
            initial_comment=body,
            file=attachment,
            title=body
        )
        view_response = True
        if view_response:
            print(f"Response: {file_response}")
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert f"Upload error {e.response['error']}"
    return res


# def set_tweepy(self):
#     api = tweepy.API(self.auth)
#     return api


class Process(object):

    def __init__(self, logger_instance=None, calling_function="General"):
        self.db = f'C:\\Ubuntu\\Shared\\data\\Process.db'
        self.conn = sqlite3.connect(self.db, timeout=15)
        self.cursor = self.conn.cursor()
        self.name = "process_instance"
        if logger_instance is None:
            logname = './logs/pushlog.log'
            self.logger_instance = get_logger(logfilename=logname)
        else:
            self.logger_instance = logger_instance
        self._calling_function = calling_function
        if calling_function == "General":
            calling_script = str(inspect.stack()[2].filename).split(sep='\\')[-1]
            self._calling_function = calling_script
            self.logger_instance.warning(f"A calling_function was not provided\n\t"
                                         f"Best practice is to set a calling function with a name "
                                         f"when instantiating a Push process\n\t"
                                         f"Using the default calling script name {calling_script} instead")
            print(inspect.stack())
            time.sleep(2)

    @property
    def calling_function(self):
        return self._calling_function

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

    def set_process_status(self, flag_):
        cmd = f"update ProcessStatus set ProcessStatus = {flag_}, " \
              f"UpdateDate = {datetime.now().strftime('%Y%m%d')}, " \
              f"UpdateTime = {datetime.now().strftime('%Y%m%d%H%M%S')} " \
              f"where ProcessName = '{self.calling_function}'"
        self.logger_instance.info(cmd)
        self.execute(cmd)
        self.logger_instance.info(f"Successfully ProcessStatus to {flag_} for {self.calling_function}")
        # self.push(title="ProcessStatus",
        #           body=f"Successfully ProcessStatus to {flag_} for {calling_function}")

        return

    def get_process_status(self):
        cmd = f"select ProcessStatus from ProcessStatus where ProcessName = '{self.calling_function}'"
        self.logger_instance.info(cmd)
        d = self.select(cmd)
        status_flag = d[0][0]
        return status_flag

    def get_process_date(self):
        cmd = f"select UpdateDate from ProcessStatus where ProcessName = '{self.calling_function}'"
        self.logger_instance.info(cmd)
        d = self.select(cmd)
        status_flag = d[0][0]
        return status_flag

    def set_slack_timestamp(self, timestamp):
        cmd = f"update Slack set " \
              f"TimeStamp = {timestamp} " \
              f"where ProcessName = '{self.calling_function}'"
        # self.logger_instance.info(cmd)
        self.execute(cmd)
        # self.logger_instance.info(f"Successfully set Time Stamp to {timestamp} for {self.calling_function}")
        return

    def get_slack_timestamp(self):
        timestamp = 0
        cmd = f"select TimeStamp from Slack where ProcessName = '{self.calling_function}'"
        # self.logger_instance.warning(cmd)
        d = self.select(cmd)
        if len(d) == 0:
            self.logger_instance.warning(f"Inserting row in Slack table for newly found process {self.calling_function}")
            insert_cmd = f"insert into Slack values ('{self.calling_function}',0)"
            self.execute(insert_cmd)
            time.sleep(1)
            d = self.select(cmd)
            try:
                timestamp = d[0][0]
            except Exception as ex:
                self.logger_instance.error(f"Your read_slack service ({self.calling_function}) needs to be registered "
                                           f"in the Slack table "
                                           f"of the Process database: {ex}")
                exit(-1)
        else:
            timestamp = d[0][0]
        return timestamp


class Push(object):
    MAX_MSG_LENGTH: int

    def __init__(self, logger_instance=None, calling_function="General"):
        api_key = API_KEY
        reg_id = REG_ID
        self.push_service = FCMNotification(api_key=api_key)
        self.registration_id = reg_id
        self.message_title = "Python test 1"
        self.message_body = "Hello python test 1"
        self.res = {}
        self.interval = 0
        self.title = None
        self.body = None
        self.MAX_MSG_LENGTH = 225
        self.str = ""
        # self.auth = tweepy.OAuthHandler(APIKEY, APISECRETKEY)
        # self.auth.set_access_token(ACCESSTOKEN, ACCESSTOKENSECRET)
        if logger_instance is None:
            logname = 'C:\\Ubuntu\\Shared\\FFB\\logs\\pushlog.log'
            self.logger_instance = get_logger(logfilename=logname)
        else:
            self.logger_instance = logger_instance

        # Create API object
        # self.api = set_tweepy(self)
        self.tweet_count = 0
        # self.pb = PushBullet(PBTOKEN)
        self.slack_url = f"https://hooks.slack.com/services/{SLACK_URL_SUFFIX}"
        self.EMAIL_FROM = f"{os.environ.get('GMA')}@gmail.com"
        self.EMAIL_PASSWORD = os.environ.get('GMPY')
        self.EMAIL_TO = f"{str(int(os.environ.get('PN')) - 4)}@vtext.com"
        self.DEFAULT_SMS = f"{str(int(os.environ.get('PN')) - 4)}@vtext.com"
        self.send_message_flag = False
        self.db = f'C:\\Ubuntu\\Shared\\data\\Push.db'
        self.conn = sqlite3.connect(self.db, timeout=15)
        self.cursor = self.conn.cursor()
        self.slack_channel_types = {
            "info": slack_alerts_channel,
            "scoreboard": slack_scoreboard_channel
        }
        self.calling_function = calling_function
        # print_calling_function()
        # self.logger_instance.warning(f"Calling function: {self.calling_function}")
        self.process_instance = Process(calling_function=self.calling_function)
        self.slack_api_token = os.environ["SLACK_BOT_TOKEN"]
        self.slack_alerts_channel = os.environ["SLACK_ALERTS_CHANNEL"]
        self.slack_requests_channel = os.environ["SLACK_CHANNEL"]
        self.slack_client = WebClient(token=self.slack_api_token)

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

    def incr_tweet_count(self):
        self.tweet_count += 1
        return self.tweet_count

    def get_tweet_count(self):
        return self.tweet_count

    def push(self, body, title=None, channel=None):
        res = 0
        use_channel = slack_alerts_channel
        if channel:
            use_channel = self.slack_channel_types[channel]
        SUPPRESS_FLAG = False
        if title is None:
            title = body[0:20]
        # To make this work, in Slack, go to channel, channel details, integrations tab, Add App "Alerts Baseball"
        if not SUPPRESS_FLAG:
            message = f"{body}\r\n\r\n"
            try:
                response = slack_client.chat_postMessage(
                    channel=use_channel,
                    text=message)
                view_response = False
                if view_response:
                    print(f"Response: {response}")
            except SlackApiError as e:
                # You will get a SlackApiError if "ok" is False
                assert e.response["error"]

            ANDROID = False
            if ANDROID:
                res = self.push_service.notify_single_device(registration_id=self.registration_id,
                                                             message_title=title,
                                                             message_body=body, sound="whisper.mp3",
                                                             badge="Test2")
        time.sleep(.5)
        return res

    def set_send_message_flag(self, flag_):
        self.send_message_flag = flag_
        cmd = f"update SMSflag set flag = {flag_} where Function = '{self.calling_function}'"
        self.logger_instance.info(cmd)
        self.execute(cmd)
        self.logger_instance.info(f"Successfully set_send_message_flag to {flag_} for {self.calling_function}")
        self.push(title="set_send_message_flag",
                  body=f"Successfully set_send_message_flag to {flag_} for {self.calling_function}")
        return self.send_message_flag

    def get_send_message_flag(self):
        cmd = f"select flag from SMSflag where Function = '{self.calling_function}'"
        self.logger_instance.info(cmd)
        send_message_flag = False
        d = self.select(cmd)
        if d:
            send_message_flag = d[0][0]
        return "On" if send_message_flag else "Off"

    def send_message(self, message, subject="No subject given", recipients=None):
        if not recipients:
            recipients = self.EMAIL_TO
        on_flag = self.get_send_message_flag()
        print(f"send_message is set to {on_flag}")
        if on_flag == "On":
            try:
                EMAIL_FROM = f"{os.environ.get('GMA')}@gmail.com"
                PASSWORD = os.environ.get('GMPY')
                EMAIL_TO = recipients
                auth = (EMAIL_FROM, PASSWORD)

                AMPM_flag = datetime.now().strftime('%p')
                if AMPM_flag == "AM":
                    AMPM_flag = "A M"
                else:
                    AMPM_flag = "P M"
                # ordinal_day = ordinal(int(datetime.now().strftime('%#d')))
                msg = MIMEText(f"{message}, "
                               f"{datetime.now().strftime('%#I:%M')} {AMPM_flag}")
                ## f" on {datetime.now().strftime('%B')} {ordinal_day} ")
                msg['Subject'] = subject
                msg['From'] = EMAIL_FROM
                msg['To'] = EMAIL_TO

                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(auth[0], auth[1])
                    server.set_debuglevel(2)
                    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
                    server.quit()
            except Exception as ex:
                print(f"Exception in push.send_message: {ex}")
        if self.calling_function == "GameData":
            time.sleep(2)
        else:
            time.sleep(.1)
        return

    def login_sms_server(self):
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(self.EMAIL_TO, self.EMAIL_PASSWORD)
            server.set_debuglevel(1)

    def push_list(self, push_list, title="None"):
        max_msg_len = self.MAX_MSG_LENGTH
        msg_len = 0
        full_msg = ""
        for msg in push_list:
            msg_len += len(msg)
            # print("Msg: "+ msg)
            # print(msg_len)
            if msg_len > max_msg_len:
                print("Message part:\n" + full_msg)
                self.logger_instance.info(full_msg)
                self.push(title, full_msg)
                self.send_message(full_msg)
                # self.tweet(full_msg)
                time.sleep(1)
                full_msg = msg
                msg_len = len(full_msg)
            else:
                full_msg += str(msg)
        # Push the remainder out
        # full_msg += "\n\n-------\n\n"
        print("Message remainder:\n" + full_msg)
        self.logger_instance.info(full_msg)
        self.push(title, full_msg)
        self.send_message(full_msg)
        # self.tweet(full_msg)
        return

    def set_msg(self, title, body):
        self.title = title
        self.body = body

    def set_interval(self, interval):
        self.interval = interval

    def push_number(self, number):
        for i in range(0, number):
            self.push(self.title, self.body)
            time.sleep(4)

    def push_change(self, number, title="None", body="None"):
        self.title = title
        self.body = body
        if number < 0:
            self.push_number(1)
        elif number > 0:
            self.push_number(2)

        time.sleep(10)

        if abs(number) < 6000:
            self.push_number(int((abs(number) + 1) / 2))

    def string_from_list(self, in_list):
        s = ""
        for i in in_list:
            s += str(i)
            s += " "

        s = s[:-1]
        s += '\n'
        self.str = s
        return self.str

    def read_slack(self):
        # self.logger_instance.info(f"read_slack Call stack:{print_stack()}\n")
        last_msg_time_db = self.process_instance.get_slack_timestamp()
        history = self.slack_client.conversations_history(channel=self.slack_requests_channel,
                                                          tokem=self.slack_api_token, limit=5)
        msgs = history['messages']
        return_text = ""
        if len(msgs) > 0:
            for msg in msgs:
                ts = float(msg['ts'])
                msg_age = ts - last_msg_time_db
                # print(f"Msg time ({ts}) for msg {msg['text']} is {msg_age} seconds "
                #       f"older than last recorded message time ({last_msg_time_db})")
                time.sleep(.25)
                if msg_age > 0:
                    try:
                        text = msg['text']
                        # slack_process_text(text)
                        return_text = text
                        self.process_instance.set_slack_timestamp(ts)
                        time.sleep(.05)
                    except Exception as ex:
                        self.push(body=f"Error in push_instance, Error: {str(ex)}")
                else:
                    pass
                    # print(f"Skipping most recent post: {text}"
        if return_text != "":
            self.push(title=f"Received slack text: {return_text}",
                      body=f"push::read_slack: received slack text: {return_text}")
        return return_text
