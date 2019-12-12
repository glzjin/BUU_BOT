# -*- coding: utf-8 -*
import buu_database
import buu_config
import utils
import request_utils
import itchatmp

class class_step(object):

    def __init__(self):
        self.step_dict = [  \
                            (None, None), \
                            (self.list_admin, None), \
                            (self.who_am_i, None), \
                            (self.sys_info, None), \
                            (self.about, None), \
                            (None, None), \
                            (self.test_inner_net_login, None), \
                            (self.baidu_wenku_download, None), \
                        ]
        self.config = buu_config.config
        self.class_database_op = buu_database.class_database_op()

    def list_admin(self, msg, userId):
        self.class_database_op.step_back(userId)
        return "管理员ID:" + str(self.config.admin_id)

    def who_am_i(self, msg, userId):
        self.class_database_op.step_back(userId)
        if userId == self.config.admin_id:
            return "管理员" + msg['FromUserName']
        else:
            return "UID:" + str(userId) + " 普通用户" + msg['FromUserName']

    def sys_info(self, msg, userId):
        self.class_database_op.step_back(userId)
        loadavg = utils.load_stat()
        mem = utils.memory_stat()
        uptime = utils.uptime_stat()
        uptime_str = "Day %s, Hour %s, Minute %s, Second %s" % (uptime['day'], uptime['hour'], uptime['minute'], uptime['second'])
        return "系统负载：%s/%s/%s\n系统内存：%s/%s MB\n系统运行时间：%s" % \
                (loadavg['lavg_1'], loadavg['lavg_5'], loadavg['lavg_15'], \
                mem['MemUsed'], mem['MemTotal'], uptime_str
                )

    def about(self, msg, userId):
        self.class_database_op.step_back(userId)
        return 'Powered by glzjin(zhaoj.in) @ BUU & ExtStars, HangZhou \nMade with Love \n最后更新时间：%s'%(self.config.version)

    def test_inner_net_login(self, msg, userId):
        self.class_database_op.step_back(userId)
        request_utils_ins = request_utils.request_utils()

        print(request_utils_ins.get_login_cookie(1))
        return '测试完毕，请查看终端输出。'

    def baidu_wenku_download(self, msg, userId):

        if not self.class_database_op.get_redis_kv(userId, 'inputing'):
            self.class_database_op.set_redis_kv(userId, 'inputing', 1)
            return '请输入您要下载的百度文库文档地址：'
        else:
            self.class_database_op.delete_redis_kv(userId, 'inputing')
            current_url = msg['Content']

        self.class_database_op.step_back(userId)

        current_url = current_url.replace('wk.baidu.com', 'wenku.baidu.com')
        current_url = current_url.replace('www.baidu.com/sf_edu_wenku', 'wenku.baidu.com')
        current_url = current_url.replace('m.baidu.com/sf_edu_wenku', 'wenku.baidu.com')

        if current_url.find('https://wenku.baidu.com') != 0 and current_url.find('http://wenku.baidu.com') != 0:
            return "非百度文库文档地址，无法下载。"

        itchatmp.send("正在为您下载该文档，请稍候。", msg['FromUserName'])

        request_utils_ins = request_utils.request_utils()

        file_info = request_utils_ins.baidu_wenku_download(current_url)

        file_url = utils.upload_file(file_info[0], file_info[1])
        import os
        os.remove(file_info[0])

        itchatmp.send("请接收文件~由于微信限制，机器人不能给您直接发送文件，请将以下链接复制到外部浏览器下载～", msg['FromUserName'])
        return file_url

    def step_tips(self, msg, userId):
        return  '1 - 列出管理员\n' \
                '2 - 我是谁\n' \
                '3 - 系统信息\n' \
                '4 - 关于\n' \
                '5 - 洗衣机概率测算\n' \
                '6 - 测试内网登录\n' \
                '7 - 百度文库下载\n' \
                '其他输入 - 返回首页'
