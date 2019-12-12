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
                                                        (class_model.Switch.q.function_name == 'book_back_notice') | \
                                                         (class_model.Switch.q.function_name == 'book_auto_renew') \
                                                     ) \
                                                 )
            for task in results:
                try:
                    if task.function_name == 'book_back_notice':
                        self.thread_pool.submit(self.book_check, task.user.id, task)
                    elif task.function_name == 'book_auto_renew':
                        self.thread_pool.submit(self.book_renew, task.user.id, task)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    pass

            time.sleep(86400)

    def book_check(self, userId, task, is_retry = False):
        loop = utils.init_asyncio()
        try:

            userName = self.class_database_op.get_username_by_id(userId)
            lib = self.class_database_op.get_lib_info(userId)
            if not lib:
                return
            request_utils_ins = request_utils.request_utils()
            books = request_utils_ins.lib_lend_book_list(userId)

            value = int(task.function_option)
            for book in books:
                if book['remain_days'] <= value:
                    itchatmp.send( \
                                    "您的这本书该还了哦～\n" \
                                    "书名: %s:\n" \
                                    "图书条码: %s\n" \
                                    "流通部门: %s\n" \
                                    "流通状态: %s\n" \
                                    "归还日期: %s\n" \
                                    "剩余天数: %d\n" \
                                    % (book['name'], book['barcode'], book['department'], book['state'], book['back_date'], book['remain_days']), userName)
        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.book_check, task.user.id, task, True)

        utils.close_asyncio(loop)

    def book_renew(self, userId, task, is_retry = False):
        utils.init_asyncio()

        try:

            userName = self.class_database_op.get_username_by_id(userId)
            lib = self.class_database_op.get_lib_info(userId)
            if not lib:
                return
            request_utils_ins = request_utils.request_utils()
            books = request_utils_ins.lib_lend_book_list(userId)

            i = 0
            for book in books:
                i = i + 1

                if book['remain_days'] <= 1:
                    if request_utils_ins.lib_lend_book_renew(userId, i):
                        itchatmp.send("续借成功，请在十天之后还书哦～", userName)
                    else:
                        itchatmp.send("续借失败，您的输入有误或者您可能已经续借过这本书了。", userName)
                    itchatmp.send( \
                                    "书名: %s:\n" \
                                    "图书条码: %s\n" \
                                    "流通部门: %s\n" \
                                    "流通状态: %s\n" \
                                    "归还日期: %s\n" \
                                    "剩余天数: %d\n" \
                                    % (book['name'], book['barcode'], book['department'], book['state'], book['back_date'], book['remain_days']), userName)
        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.book_renew, task.user.id, task, True)

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
