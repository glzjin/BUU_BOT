# -*- coding: utf-8 -*

import buu_config, buu_database
import utils
import itchatmp
import buu_step4_menu, buu_step1_menu, buu_step3_menu, buu_step2_menu, buu_step6_menu

class class_command_dict(object):

    def step_0_tips(self, msg, userId):
        return '欢迎使用联大小助手，请输入以下数字来使用相关功能：\n' \
                '1 - 校园卡相关功能\n' \
                '2 - 图书馆相关功能(图书馆系统近期升级，接口对接中)\n' \
                '3 - 教务系统相关功能\n' \
                '4 - 更多功能\n' \
                '5 - 树洞,匿名聊天,表白墙\n' \
                'PS: 您在进行任何操作时都可以用 #返回 来返回到上一级操作~'

    # def step_mig(self, msg, userId):
    #     itchatmp.send('@img@qrcode1.jpg', msg['FromUserName'])
    #     return '此功能，请添加上面这个微信为好友进行体验~'

    def step_process(self, msg, userId, msg_opt):
        loop = utils.init_asyncio()

        try:

            is_back = False
            if msg['Content'] in ['#返回']:
                self.class_database_op.step_back(userId)
                is_back = True

            cur_step = self.class_database_op.get_user_current_step(userId)

            is_head = False
            if not cur_step or cur_step == '0' and not is_back:
                cur_step = str(msg['Content'])
                next_step = int(msg['Content'])
                is_head = True

            steps = cur_step.split('-')
            cur_step_action = self.command_dict
            for step in steps:
                next_step = int(step)
                cur_step_action = (cur_step_action[0])[int(step)]

            if type(cur_step_action[0]) is not type(self.step_process):
                if not is_head and not is_back:
                    next_step = int(msg['Content'])

                    if next_step == 0:
                        self.class_database_op.step_back(userId)
                        return self.get_current_step_tips(userId)

                    if cur_step == '0':
                        cur_step = str(next_step)
                    else:
                        cur_step = cur_step + "-" + str(next_step)

                    cur_step_action = (cur_step_action[0])[next_step]

                self.class_database_op.set_user_current_step(userId, cur_step)

            if type(cur_step_action[0]) == type([]):
                # 菜单处理
                self.class_database_op.delete_redis_kv(userId, 'inputing')
                return cur_step_action[1](msg, userId)
            else:
                #动作处理
                if msg_opt:
                    return cur_step_action[0](msg, userId, msg_opt)
                else:
                    if not cur_step_action[0]:
                        self.class_database_op.step_back(userId)
                        return self.get_current_step_tips(userId)

                    return cur_step_action[0](msg, userId)

        except (ValueError, IndexError):
            import traceback
            traceback.print_exc()
            self.class_database_op.step_back(userId)
            return self.get_current_step_tips(userId)
        except Exception:
            import traceback
            traceback.print_exc()
            self.class_database_op.set_user_current_step(userId, '0')
            for single_key in self.config.fail_clean:
                self.class_database_op.delete_redis_kv(userId, single_key)
            r = itchatmp.send("似乎。。。出现了一个错误。。。\n这一般是因为：\n[1]您的输入有误\n[2]系统在处理时发生了一个错误\n[3]您在系统中输入的校园卡信息不正确，mybuu 账号无法登陆。\n\n综上，已返回到首级菜单。", msg['FromUserName'])
            return self.step_0_tips(msg, userId)

        utils.close_asyncio(loop)

    def get_current_step_tips(self, userId):
        cur_step = self.class_database_op.get_user_current_step(userId)

        steps = cur_step.split('-')
        cur_step_action = self.command_dict
        for step in steps:
            next_step = int(step)
            cur_step_action = (cur_step_action[0])[int(step)]

        if cur_step == '0':
            return self.step_0_tips('', userId)

        if type(cur_step_action[0]) == type([]):
            # 菜单处理
            self.class_database_op.delete_redis_kv(userId, 'inputing')
            return cur_step_action[1]('', userId)
        else:
            return '已返回上级菜单'

    def under_constuct_tips(self, msg, userId):
        self.class_database_op.step_back(userId)
        return "功能开发中。。。"

    def __init__(self):
        self.buu_step4_menu = buu_step4_menu.class_step()
        self.buu_step1_menu = buu_step1_menu.class_step()
        self.buu_step3_menu = buu_step3_menu.class_step()
        self.buu_step2_menu = buu_step2_menu.class_step()
        self.buu_step6_menu = buu_step6_menu.class_step()

        self.command_dict = [  \
                                (self.step_0_tips, None), \
                                (self.buu_step1_menu.step_dict, self.buu_step1_menu.step_tips), \
                                (self.buu_step2_menu.step_dict, self.buu_step2_menu.step_tips), \
                                (self.buu_step3_menu.step_dict, self.buu_step3_menu.step_tips), \
                                (self.buu_step4_menu.step_dict, self.buu_step4_menu.step_tips), \
                                (self.under_constuct_tips, None), \
                            ]

        self.command_dict = (self.command_dict, self.command_dict)

        self.config = buu_config.config
        self.class_database_op = buu_database.class_database_op()
