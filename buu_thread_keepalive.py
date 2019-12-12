# -*- coding: utf-8 -*
import threading
import itchatmp
import buu_model, buu_database, request_utils, buu_config
from concurrent.futures import ThreadPoolExecutor
import time
import utils

class MainThread(threading.Thread):
    def __init__(self, thread_pool):
        threading.Thread.__init__(self)
        self.class_database_op = buu_database.class_database_op()
        self.thread_pool = thread_pool

    def run(self):
        while True:
            self.thread_pool.submit(self.keep_alive)

            time.sleep(60)

    def keep_alive(self, is_retry = False):
        loop = utils.init_asyncio()
        try:
            request_utils_ins = request_utils.request_utils()
            try:
                request_utils_ins.www_keepalive()
            except Exception:
                import traceback
                traceback.print_exc()


                userName = self.class_database_op.get_username_by_id(self.config.admin_id)

                itchatmp.send("网络掉线，请检查~", userName)

        except Exception:
            if not is_retry:
                self.thread_pool.submit(self.keep_alive, True)

        utils.close_asyncio(loop)


class class_init_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.thread_pool = ThreadPoolExecutor(max_workers = 1)
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
