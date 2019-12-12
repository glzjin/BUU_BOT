# -*- coding: utf-8 -*
import threading
import itchatmp
import time
from buu_model import class_model
from concurrent.futures import ThreadPoolExecutor
import request_utils
import buu_database
import datetime
import utils

class MainThread(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.class_database_op = buu_database.class_database_op()
        self.thread_pool = thread_pool

    def run(self):
        time.sleep(1800)
        while True:
            results = class_model.Switch.select( \
                                                    (class_model.Switch.q.function_enable == 1) & \
                                                    ( \
                                                        (class_model.Switch.q.function_name == 'balance_notice') | \
                                                         (class_model.Switch.q.function_name == 'consume_notice') \
                                                     ) \
                                                 )
            hour = int(time.strftime('%H',time.localtime(time.time())))
            today = datetime.date.today().strftime('%Y%m%d')

            for task in results:
                try:
                    if task.function_name == 'balance_notice':
                        self.thread_pool.submit(self.balance_check, task.user.id, task)
                    elif task.function_name == 'consume_notice':
                        self.thread_pool.submit(self.consume_check, task.user.id, task)

                        if hour >= 23:
                            sent_date = self.class_database_op.get_redis_kv(task.user.id, 'daily-consume-notice-sent')
                            if not sent_date:
                                self.class_database_op.set_redis_kv(task.user.id, 'daily-consume-notice-sent', today)
                                self.thread_pool.submit(self.daily_consume_notice, task.user.id, task)
                            else:
                                sent_date = sent_date.decode('utf-8')
                                if sent_date != today:
                                    self.class_database_op.set_redis_kv(task.user.id, 'daily-consume-notice-sent', today)
                                    self.thread_pool.submit(self.daily_consume_notice, task.user.id, task)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    pass

            time.sleep(1800)

    def balance_check(self, userId, task, is_retry = False):
        loop = utils.init_asyncio()
        try:

            userName = self.class_database_op.get_username_by_id(userId)
            card = self.class_database_op.get_card_info(userId)
            if not card:
                return
            request_utils_ins = request_utils.request_utils()
            balance = request_utils_ins.card_balance_check(userId)['current']

            value = float(task.function_option)
            if value > balance:
                if not self.class_database_op.get_redis_kv(userId, 'balance-notice-sent'):
                    itchatmp.send("您的校园卡余额不足，目前是 %.2f 元，请及时充值。" % balance, userName)
                    self.class_database_op.set_redis_kv(userId, 'balance-notice-sent', 1)
            else:
                self.class_database_op.delete_redis_kv(userId, 'balance-notice-sent')
        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.balance_check, task.user.id, task, True)

        utils.close_asyncio(loop)

    def consume_check(self, userId, task, is_retry = False):
        loop = utils.init_asyncio()
        try:

            userName = self.class_database_op.get_username_by_id(userId)
            card = self.class_database_op.get_card_info(userId)
            if not card:
                return

            request_utils_ins = request_utils.request_utils()
            ret_list = request_utils_ins.card_get_today_log(userId)
            last_order = self.class_database_op.get_redis_kv(userId, 'consume-notice-count')
            if last_order:
                last_order = int(last_order)
            put_order_count = 0
            for item in ret_list:
                if last_order:
                    if item['count'] > last_order:
                        # 开始提醒
                        intent = '其他'
                        if item['sub_system_name'] == '本部水控':
                            intent = '洗澡'
                        elif item['sub_system_name'] == '本部商贸硬网关':
                            intent = '购物'
                        elif item['sub_system_name'] == '本部北院硬网关' or item['sub_system_name'] == '本部南院硬网关':
                            intent = '吃饭'
                        itchatmp.send("校园卡消费提醒：\n" \
                                        "时间：%s\n" \
                                        "金额：%.2f 元\n" \
                                        "余额：%.2f 元\n" \
                                        "消费用途：%s" \
                                        % (item['time'], abs(item['amount']), item['current_balance'], intent) \
                                        , userName)
                if put_order_count < item['count']:
                    put_order_count = item['count']
            if put_order_count:
                self.class_database_op.set_redis_kv(userId, 'consume-notice-count', put_order_count)
        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.consume_check, task.user.id, task, True)

        utils.close_asyncio(loop)

    def daily_consume_notice(self, userId, task, is_retry = False):
        loop = utils.init_asyncio()
        try:

            userName = self.class_database_op.get_username_by_id(userId)
            card = self.class_database_op.get_card_info(userId)
            if not card:
                return

            today = datetime.date.today().strftime('%Y%m%d')
            month = datetime.date.today().strftime('%Y%m')

            request_utils_ins = request_utils.request_utils()
            ret_list = request_utils_ins.card_get_today_log(userId)
            consume_amount = request_utils_ins.card_get_total_consume(userId, month + '01', month + '30')
            today_consume_amount = request_utils_ins.card_get_today_total_consume(userId)

            bash_count = 0
            bash_amount = 0.0

            rest_amount = 0.0

            buy_count = 0
            buy_amount = 0.0

            eat_count = 0
            eat_amount = 0.0
            for item in ret_list:
                if item['sub_system_name'] == '本部水控':
                    bash_count += 1
                    bash_amount += abs(item['amount'])
                elif item['sub_system_name'] == '本部商贸硬网关':
                    buy_count += 1
                    buy_amount += abs(item['amount'])
                elif item['sub_system_name'] == '本部北院硬网关' or item['sub_system_name'] == '本部南院硬网关':
                    eat_count += 1
                    eat_amount += abs(item['amount'])
                else:
                    rest_amount += abs(item['amount'])
            itchatmp.send("晚上好，您的今天消费状况如下：\n" \
                            "共洗了 %d 次澡，花了 %.2f 元。\n" \
                            "共吃了 %d 次饭，花了 %.2f 元。\n" \
                            "共买了 %d 次东西，花了 %.2f 元。\n" \
                            "其他共花了 %.2f 元。\n" \
                            "本月总共共花了 %.2f 元。\n" \
                            % (bash_count, bash_amount, \
                                eat_count, eat_amount, \
                                buy_count, buy_amount,
                                rest_amount, abs(consume_amount + today_consume_amount)), userName)
        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.daily_consume_notice, task.user.id, task, True)

        utils.close_asyncio(loop)

class class_init_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.thread_pool = ThreadPoolExecutor(max_workers = 5)
        self.t = MainThread(self.thread_pool)
        self.t.start()

    def run(self):
        while True:
            if not self.t.is_alive():
                self.t.start()
            time.sleep(60)

class class_init_thread_supervisor(object):
    def __init__(self):
        thread_supervisor = class_init_thread()
        thread_supervisor.start()
