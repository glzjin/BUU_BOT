# -*- coding: utf-8 -*
import buu_database
import buu_config
import request_utils
import itchatmp

class class_step(object):

    def __init__(self):
        self.step_dict = [  \
                            (None, None), \
                            (self.input_card_info, None), \
                            (self.get_card_info, None), \
                            (self.balance_check, None), \
                            (self.card_consume_notice_enable, None), \
                            (self.card_balance_notice_enable, None), \
                            (self.card_get_log, None), \
                            (self.card_get_today_log, None) \
                        ]
        self.config = buu_config.config
        self.class_database_op = buu_database.class_database_op()

    def input_card_info(self, msg, userId):
        current_user_name = self.class_database_op.get_redis_kv(userId, 'card_user_name')
        if not current_user_name:
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                return '请输入您的学号：'
            else:
                self.class_database_op.set_redis_kv(userId, 'card_user_name', msg['Content'])
                return '学号已保存，接下来请输入您在 my.buu.edu.cn 的密码：\n' \
                        '注意：密码会被加密储存，但由于技术限制，在使用时会被解密为明文，请您知悉。\n' \
                        '同时本系统会只访问实现功能所需要的数据，其他数据一概不访问。'

        current_password = msg['Content']

        current_user_name = current_user_name.decode('utf-8')
        self.class_database_op.save_card_info(userId, current_user_name, current_password)

        self.class_database_op.delete_redis_kv(userId, 'card_user_name')
        self.class_database_op.delete_redis_kv(userId, 'inputing')

        self.class_database_op.step_back(userId)

        request_utils_ins = request_utils.request_utils()
        if request_utils_ins.login_check(userId):
            return '密码已保存，系统已经保存您所输入的数据。'
        else:
            self.class_database_op.delete_card_info(userId)
            return '您所输入的信息无法登录，请按 1 重新输入。'

    def get_card_info(self, msg, userId):
        self.class_database_op.step_back(userId)
        card = self.class_database_op.get_card_info(userId)
        if card:
            return "您的登录信息：\n学号：%s\n密码已隐藏，不给你看~" % (card.user_name)
        else:
            return "您还没有保存您的信息，选1来输入登录信息吧~"

    def step_tips(self, msg, userId):
        return  '1 - 输入登录信息\n' \
                '2 - 登录信息查看\n' \
                '3 - 校园卡余额查询\n' \
                '4 - 消费提醒开关\n' \
                '5 - 余额提醒设置\n' \
                '6 - 历史消费分析\n' \
                '7 - 今日消费分析\n' \
                '其他输入 - 返回首页'

    def balance_check(self, msg, userId):
        self.class_database_op.step_back(userId)
        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return "您还没有保存您的信息，选1来输入登录信息吧~"
        request_utils_ins = request_utils.request_utils()
        balance = request_utils_ins.card_balance_check(userId)
        return "当前余额：%.2f 元\n当前过渡余额：%.2f 元\n上次过渡余额：%.2f 元" % (balance['current'], balance['current_pending'], balance['pre_pending'])

    def card_get_log(self, msg, userId):
        if not self.class_database_op.get_redis_kv(userId, 'inputing'):
            self.class_database_op.set_redis_kv(userId, 'inputing', 1)
            return '请输入您要查询的月份，比如2017年8月则输入 201708：'
        else:
            self.class_database_op.delete_redis_kv(userId, 'inputing')
            month = msg['Content']

        self.class_database_op.step_back(userId)
        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return "您还没有保存您的信息，选1来输入登录信息吧~"
        request_utils_ins = request_utils.request_utils()
        ret_list = request_utils_ins.card_get_history_log(userId, month + '01', month + '30')
        consume_amount = request_utils_ins.card_get_total_consume(userId, month + '01', month + '30')
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
        return "查询完毕, 您的消费状况如下：\n" \
                "共洗了 %d 次澡，花了 %.2f 元。\n" \
                "共吃了 %d 次饭，花了 %.2f 元。\n" \
                "共买了 %d 次东西，花了 %.2f 元。\n" \
                "其他共花了 %.2f 元。\n" \
                "总共共花了 %.2f 元。\n" \
                % (bash_count, bash_amount, \
                    eat_count, eat_amount, \
                    buy_count, buy_amount,
                    rest_amount, abs(consume_amount))

    def card_get_today_log(self, msg, userId):

        self.class_database_op.step_back(userId)
        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return "您还没有保存您的信息，选1来输入登录信息吧~"
        request_utils_ins = request_utils.request_utils()
        ret_list = request_utils_ins.card_get_today_log(userId)
        consume_amount = request_utils_ins.card_get_today_total_consume(userId)
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
        return "查询完毕, 您的今天消费状况如下：\n" \
                "共洗了 %d 次澡，花了 %.2f 元。\n" \
                "共吃了 %d 次饭，花了 %.2f 元。\n" \
                "共买了 %d 次东西，花了 %.2f 元。\n" \
                "其他共花了 %.2f 元。\n" \
                "总共共花了 %.2f 元。\n" \
                % (bash_count, bash_amount, \
                    eat_count, eat_amount, \
                    buy_count, buy_amount,
                    rest_amount, abs(consume_amount))

    def card_consume_notice_enable(self, msg, userId):
        if not self.class_database_op.get_redis_kv(userId, 'inputing'):
            self.class_database_op.set_redis_kv(userId, 'inputing', 1)
            result = self.class_database_op.get_function_info(userId, 'consume_notice')
            if result['enable'] == 1:
                enable = '开启'
            else:
                enable = '关闭'
            return '您当前此功能的状态：%s\n' \
                    '开启后，您每次消费我都会提醒您，而且在每天晚上十一点我会给您发送当天的消费总结~\n' \
                    '回复 1 开启， 0关闭' % \
                    (enable)
        else:
            enable = int(msg['Content'])

        self.class_database_op.step_back(userId)

        self.class_database_op.set_function_info(userId, 'consume_notice', enable, msg['Content'])

        self.class_database_op.delete_redis_kv(userId, 'inputing')
        return '设置成功！'

    def card_balance_notice_enable(self, msg, userId):
        balance_notice_enable = self.class_database_op.get_redis_kv(userId, 'balance_notice_enable')
        if not balance_notice_enable:
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                result = self.class_database_op.get_function_info(userId, 'balance_notice')
                if result['enable'] == 1:
                    enable = '开启，金额为 %.2f 元' % (float(result['option']))
                else:
                    enable = '关闭'
                return '您当前此功能的状态：%s\n' \
                        '开启后，当余额少于您设定的数值时，我会提醒您去充值的，免得因为学校系统的 bug 搞得卡都刷不了了~\n' \
                        '回复 1 开启， 0关闭' % \
                        (enable)
            else:
                if int(msg['Content']) == 1:
                    self.class_database_op.set_redis_kv(userId, 'balance_notice_enable', int(msg['Content']))
                    return '请输入您所需要的提醒值，低于这个数值我就会提醒您该充值了~'
                else:
                    self.class_database_op.set_function_info(userId, 'balance_notice', 0, '0.0')
                    self.class_database_op.step_back(userId)
                    self.class_database_op.delete_redis_kv(userId, 'inputing')
                    return '设置成功!'

        self.class_database_op.step_back(userId)

        enable = self.class_database_op.get_redis_kv(userId, 'balance_notice_enable')
        self.class_database_op.set_function_info(userId, 'balance_notice', int(enable), str(float(msg['Content'])))

        self.class_database_op.delete_redis_kv(userId, 'balance_notice_enable')
        self.class_database_op.delete_redis_kv(userId, 'inputing')

        return '设置成功！'
