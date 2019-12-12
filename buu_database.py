# -*- coding: utf-8 -*
import redis
import buu_config, buu_model
from buu_model import class_model
import aes

class class_database_op(object):

    def __init__(self):
        self.config = buu_config.config
        self.redis_ins = redis.Redis(host = self.config.redis_addr, port = self.config.redir_port,  \
                                    db = self.config.redis_db, password = self.config.redis_password)
        self.encryptor = aes.AESCipher(self.config.aes_key)

    def flush_redis(self):
        self.redis_ins.flushdb()

    def put_user(self, userName):
        exist_userId = self.redis_ins.get('user-username-id-' + userName)
        if not exist_userId:
            try:
                exist_user = class_model.User.select(class_model.User.q.userName == userName).limit(1).getOne()
                userId = exist_user.id
                self.redis_ins.set('user-id-username-' + str(userId), userName)
                self.redis_ins.set('user-username-id-' + userName, userId)
                return int(userId)
            except Exception:
                exist_user = class_model.User(userName = userName)
                userId = exist_user.id
                self.redis_ins.set('user-id-username-' + str(userId), userName)
                self.redis_ins.set('user-username-id-' + userName, userId)
                return int(userId)
        else:
            return int(exist_userId)

    def get_username_by_id(self, userId):
        userId = int(userId)
        exist_userName = self.redis_ins.get('user-id-username-' + str(userId))
        if exist_userName:
            return exist_userName.decode('utf-8')

        try:
            exist_user = class_model.User.select(class_model.User.q.id == int(userId)).limit(1).getOne()
            self.redis_ins.set('user-id-username-' + str(userId), exist_user.userName)
            self.redis_ins.set('user-username-id-' + exist_user.userName, userId)
            return exist_user.userName
        except Exception:
            return None

    def get_user_by_id(self, userId):
        try:
            exist_user = class_model.User.select(class_model.User.q.id == int(userId)).limit(1).getOne()
            return exist_user
        except Exception:
            return None


    def get_id_by_username(self, userName):
        exist_userId = self.redis_ins.get('user-username-id-' + userName)
        if exist_userId:
            return exist_userId

        try:
            exist_user = class_model.User.select(class_model.User.q.userName == userName).limit(1).getOne()
            userId = exist_user.id
            self.redis_ins.set('user-id-username-' + str(userId), userName)
            self.redis_ins.set('user-username-id-' + userName, userId)
            return userId
        except Exception:
            return None

    def get_user_current_step(self, userId):
        step = self.redis_ins.get('step-' + str(userId))
        if step:
            return step.decode('utf-8')

        return '0'

    def set_user_current_step(self, userId, step):
        self.redis_ins.set('step-' + str(userId), step)

    def step_back(self, userId):
        for single_key in self.config.fail_clean:
            self.delete_redis_kv(userId, single_key)
        cur_step = self.get_user_current_step(userId)
        stop_pos = cur_step.rfind('-')
        if stop_pos != -1:
            cur_step = cur_step[:stop_pos]
        else:
            cur_step = '0'
        self.set_user_current_step(userId, cur_step)

    def set_redis_kv(self, userId, key, value, ttl = 0):
        self.redis_ins.set('custom-' + str(userId) + '-' + str(key), value)

        if ttl != 0:
            self.redis_ins.expire('custom-' + str(userId) + '-' + str(key), ttl)

    def get_redis_kv(self, userId, key):
        return self.redis_ins.get('custom-' + str(userId) + '-' + str(key))

    def delete_redis_kv(self, userId, key):
        self.redis_ins.delete('custom-' + str(userId) + '-' + str(key))

    def delete_redis_prefix_kv(self, userId, prefix):
        for key in self.redis_ins.scan_iter('custom-' + str(userId) + '-' + str(prefix) + '*'):
            # delete the key
            self.redis_ins.delete(key)

    def save_card_info(self, userId, user_name, password):
        password = self.encryptor.encrypt(password)
        try:
            exist_card = class_model.Card.select(class_model.Card.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            exist_card.set(user_name = user_name, password = password)
            exist_card.sync()
        except Exception:
            class_model.Card(user_name = user_name, password = password, user = self.get_user_by_id(userId))

    def get_card_info(self, userId):
        try:
            exist_card = class_model.Card.select(class_model.Card.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            return exist_card
        except Exception:
            return None

    def delete_card_info(self, userId):
        try:
            exist_card = class_model.Card.select(class_model.Card.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            class_model.Card.delete(exist_card.id)
        except Exception:
            return False

    def get_card_info_password(self, savedPassword):
        return self.encryptor.decrypt(savedPassword)

    def get_function_info(self, userId, function_name):
        result = {}

        enable = self.redis_ins.get('function-' + str(userId) + '-' + function_name + '-enable')
        option = self.redis_ins.get('function-' + str(userId) + '-' + function_name + '-option')
        if enable is not None:
            result['enable'] = int(enable)
            result['option'] = option
            return result
        else:
            result['enable'] = 0
            result['option'] = ''

        try:
            function = class_model.Switch.select((class_model.Switch.q.user == self.get_user_by_id(userId)) & (class_model.Switch.q.function_name == function_name)).limit(1).getOne()
            result['enable'] = int(function.function_enable)
            result['option'] = function.function_option
            return result
        except Exception:
            return result

    def set_function_info(self, userId, function_name, enable, option):
        try:
            exist_function = class_model.Switch.select((class_model.Switch.q.user == self.get_user_by_id(userId)) & (class_model.Switch.q.function_name == function_name)).limit(1).getOne()
            exist_function.set(function_enable = enable, function_option = option)
            self.redis_ins.set('function-' + str(userId) + '-' + function_name + '-enable', int(enable))
            self.redis_ins.set('function-' + str(userId) + '-' + function_name + '-option', option)
        except Exception:
            class_model.Switch(function_enable = enable, function_option = option, function_name = function_name, user = self.get_user_by_id(userId))
            self.redis_ins.set('function-' + str(userId) + '-' + function_name + '-enable', int(enable))
            self.redis_ins.set('function-' + str(userId) + '-' + function_name + '-option', option)

    def add_printer_info(self, userId, printer_name, printer_type, printer_value):
        try:
            class_model.Printer(printer_type = printer_type, printer_name = printer_name, printer_value = printer_value, user = self.get_user_by_id(userId))
        except Exception:
            pass

    def get_my_printers(self, userId):
        try:
            exist_printers = class_model.Printer.select(class_model.Printer.q.user == self.get_user_by_id(userId))
            return exist_printers
        except Exception:
            return None

    def delete_my_printer(self, userId, printerId):
        try:
            exist_printer = class_model.Printer.select((class_model.Printer.q.user == self.get_user_by_id(userId)) & (class_model.Printer.q.id == printerId)).limit(1).getOne()
            class_model.Printer.delete(exist_printer.id)
            return True
        except Exception:
            return False

    def get_all_printers(self, userId):
        try:
            exist_printers = class_model.Printer.select()
            return exist_printers
        except Exception:
            return None

    def get_printer(self, printerId):
        try:
            exist_printer = class_model.Printer.select(class_model.Printer.q.id == printerId).limit(1).getOne()
            return exist_printer
        except Exception:
            return None

    def add_print_job(self, page_num, file_name, user, printer):
        try:
            job = class_model.PrintJob(page_num = page_num, file_name = file_name, user = user, printer = printer)
            return job.id
        except Exception:
            return None

    def save_lib_info(self, userId, user_name, password):
        password = self.encryptor.encrypt(password)
        try:
            exist_lib = class_model.Lib.select(class_model.Lib.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            exist_lib.set(user_name = user_name, password = password)
            exist_lib.sync()
        except Exception:
            class_model.Lib(user_name = user_name, password = password, user = self.get_user_by_id(userId))

    def get_lib_info(self, userId):
        try:
            exist_lib = class_model.Lib.select(class_model.Lib.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            return exist_lib
        except Exception:
            return None

    def delete_lib_info(self, userId):
        try:
            exist_lib = class_model.Lib.select(class_model.Lib.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            class_model.Lib.delete(exist_lib.id)
        except Exception:
            return False

    def get_lib_info_password(self, savedPassword):
        return self.encryptor.decrypt(savedPassword)

    def save_jwxt_info(self, userId, user_name, password):
        password = self.encryptor.encrypt(password)
        try:
            exist_jwxt = class_model.Jwxt.select(class_model.Jwxt.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            exist_jwxt.set(user_name = user_name, password = password)
            exist_jwxt.sync()
        except Exception:
            class_model.Jwxt(user_name = user_name, password = password, user = self.get_user_by_id(userId))

    def get_jwxt_info(self, userId):
        try:
            exist_jwxt = class_model.Jwxt.select(class_model.Jwxt.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            return exist_jwxt
        except Exception:
            return None

    def delete_jwxt_info(self, userId):
        try:
            exist_jwxt = class_model.Jwxt.select(class_model.Jwxt.q.user == self.get_user_by_id(userId)).limit(1).getOne()
            class_model.Jwxt.delete(exist_jwxt.id)
        except Exception:
            return False

    def get_jwxt_info_password(self, savedPassword):
        return self.encryptor.decrypt(savedPassword)
