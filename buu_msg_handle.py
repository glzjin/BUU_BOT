# -*- coding: utf-8 -*
import buu_config, buu_command_dict, buu_database
import itchatmp
from concurrent.futures import ThreadPoolExecutor
import buu_config

class class_msg_handle(object):

    def msg_handle(self, msg, msg_opt = None):
        self.thread_pool.submit(self.msg_handle_task, msg, msg_opt)
        return

    def __init__(self):
        self.class_database_op = buu_database.class_database_op()

        self.config = buu_config.config
        self.command_dict_class = buu_command_dict.class_command_dict()
        self.command_dict = self.command_dict_class.command_dict

        self.thread_pool = ThreadPoolExecutor(max_workers = 10)

    def msg_handle_task(self, msg, msg_opt):
        user_id = self.class_database_op.put_user(msg['FromUserName'])

        if buu_config.config.verbose:
            print('%s: %s' % (msg['FromUserName'], msg['Content']))
        return_str = self.command_dict_class.step_process(msg, user_id, msg_opt)
        if return_str:
            itchatmp.send(return_str, msg['FromUserName'])
