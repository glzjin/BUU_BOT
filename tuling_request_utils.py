# -*- coding: utf-8 -*
import requests
import re
import buu_config, buu_database
import utils

class class_tuling_request_utils(object):
    def __init__(self):
        self.config = buu_config.config
        self.session = requests.Session()

    def tuling_msg_handle(self, text, userId):
        apiUrl = 'http://www.tuling123.com/openapi/api'
        payload = {
            'key'    : self.config.tuling_key, # 如果这个Tuling Key不能用，那就换一个
            'info'   : text, # 这是我们发出去的消息
            'userid' : userId, # 这里你想改什么都可以
        }

        r = self.session.post(apiUrl, data = payload).json()
        return r['text']
