# -*- coding: utf-8 -*
import buu_database
import buu_config
import request_utils
import itchatmp
import utils
import re

class class_step(object):

    def __init__(self):
        self.step_dict = [  \
                            (None, None), \
                            (self.test, None), \
                            (self.input_lib_info, None), \
                            (self.get_lib_info, None), \
                            (self.get_lend_book_info, None), \
                            (self.book_back_notice_enable, None), \
                            (self.renew_lend_book, None), \
                            (self.book_auto_renew_enable, None), \
                        ]
        self.config = buu_config.config
        self.class_database_op = buu_database.class_database_op()


    def step_tips(self, msg, userId):
        return  '1 - 关键字搜书\n' \
                '2 - 输入图书馆帐号信息\n' \
                '3 - 查看图书馆帐号信息\n' \
                '4 - 获取我的借书信息\n' \
                '5 - 还书提醒设置\n' \
                '6 - 续借图书\n' \
                '7 - 自动续借图书设置\n' \
                '其他输入 - 返回首页'

    def back(self, msg, userId):
        self.class_database_op.step_back(userId)
        return self.step_tips(msg, userId)

    def test(self, msg, userId):
        word = None
        if not self.class_database_op.get_redis_kv(userId, 'operating'):
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                return '请输入您要搜索的关键字~'
            else:
                self.class_database_op.delete_redis_kv(userId, 'inputing')
                word = msg['Content']
                self.class_database_op.set_redis_kv(userId, 'word', word)

        self.class_database_op.set_redis_kv(userId, 'operating', 1)


        if msg['Content'] == '0' and not word:
            return self.back(msg, userId)
        elif msg['Content'] == '1' and not word:
            itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
            total_page = int(self.class_database_op.get_redis_kv(userId, 'total_page'))
            current_page = int(self.class_database_op.get_redis_kv(userId, 'current_page')) + 1
            word = self.class_database_op.get_redis_kv(userId, 'word').decode('utf-8')

            if total_page + 1 > current_page:
                self.class_database_op.set_redis_kv(userId, 'current_page', current_page)
            else:
                #翻页到头
                return self.back(msg, userId)
        else:
            if not self.class_database_op.get_redis_kv(userId, 'current_page'):
                itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
                self.class_database_op.set_redis_kv(userId, 'current_page', 1)
                current_page = 1
            else:
                #异常输入
                return self.back(msg, userId)

        request_utils_ins = request_utils.request_utils()
        books = request_utils_ins.lib_search_books(word, current_page)
        total_page = books[1]
        if not self.class_database_op.get_redis_kv(userId, 'total_page'):
            if total_page == 0:
                return self.back(msg, userId)
            self.class_database_op.set_redis_kv(userId, 'total_page', total_page)
        books = books[0]

        i = 0
        while len(books) < 5 and total_page >= current_page + i:
            i += 1
            books += request_utils_ins.lib_search_books(word, current_page + i)[0]

        if i > 0:
            current_page += i
            self.class_database_op.set_redis_kv(userId, 'current_page', current_page)


        for book in books:
            if book['publisher'] != '' and book['author'] != '':
                itchatmp.send( \
                                "书名：%s\n" \
                                "作者：%s\n" \
                                "出版社：%s\n" \
                                "ISBN：%s\n" \
                                "出版年份：%s\n" \
                                "索书号：%s\n" \
                                "可借/总数：%d/%d" \
                                % \
                                ( \
                                    book['name'], \
                                    book['author'], \
                                    book['publisher'], \
                                    book['isbn'], \
                                    book['publish_year'], \
                                    book['search_book_no'], \
                                    book['av_number'], book['have_number'], \
                                ) \
                                , msg['FromUserName'])

        if current_page == total_page:
            itchatmp.send("页面到头，已返回上级菜单。\n当前第 %d 页，总共 %d 页。" % (current_page, total_page), msg['FromUserName'])
            itchatmp.send(self.back(msg, userId), msg['FromUserName'])
        else:
            itchatmp.send("输入0退回到上级菜单，输入1翻页。\n当前第 %d 页，总共 %d 页。" % (current_page, total_page), msg['FromUserName'])

    def input_lib_info(self, msg, userId):
        current_user_name = self.class_database_op.get_redis_kv(userId, 'lib_user_name')
        if not current_user_name:
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                return '请输入您的学号：'
            else:
                self.class_database_op.set_redis_kv(userId, 'lib_user_name', msg['Content'])
                return '学号已保存，接下来请输入您在 opac.buu.edu.cn 的密码：\n' \
                        '注意：密码会被加密储存，但由于技术限制，在使用时会被解密为明文，请您知悉。\n' \
                        '同时本系统会只访问实现功能所需要的数据，其他数据一概不访问。'

        current_password = msg['Content']

        current_user_name = current_user_name.decode('utf-8')
        self.class_database_op.save_lib_info(userId, current_user_name, current_password)

        self.class_database_op.delete_redis_kv(userId, 'lib_user_name')
        self.class_database_op.delete_redis_kv(userId, 'inputing')

        self.class_database_op.step_back(userId)

        request_utils_ins = request_utils.request_utils()
        if request_utils_ins.lib_login_check(userId):
            return '密码已保存，系统已经保存您所输入的数据。'
        else:
            self.class_database_op.delete_lib_info(userId)
            return '您所输入的信息无法登录，请按 2 重新输入。'

    def get_lib_info(self, msg, userId):
        self.class_database_op.step_back(userId)
        lib = self.class_database_op.get_lib_info(userId)
        if lib:
            return "您的图书馆信息：\n学号：%s\n密码已隐藏，不给你看~" % (lib.user_name)
        else:
            return "您还没有保存您的信息，选2来输入登录信息吧~"

    def get_lend_book_info(self, msg, userId):
        self.class_database_op.step_back(userId)

        lib = self.class_database_op.get_lib_info(userId)
        if not lib:
            return "您还没有保存您的信息，选2来输入登录信息吧~"

        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])

        request_utils_ins = request_utils.request_utils()

        books = request_utils_ins.lib_lend_book_list(userId)

        for book in books:
            itchatmp.send( \
                            "书名: %s\n" \
                            "图书条码: %s\n" \
                            "流通部门: %s\n" \
                            "流通状态: %s\n" \
                            "归还日期: %s\n" \
                            "剩余天数: %d\n" \
                            % (book['name'], book['barcode'], book['department'], book['state'], book['back_date'], book['remain_days']), msg['FromUserName'])

        itchatmp.send("借阅信息输出完毕！", msg['FromUserName'])

    def book_back_notice_enable(self, msg, userId):
        balance_notice_enable = self.class_database_op.get_redis_kv(userId, 'book_back_notice_enable')
        if not balance_notice_enable:
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                result = self.class_database_op.get_function_info(userId, 'book_back_notice')
                if result['enable'] == 1:
                    enable = '开启，天数为 %.2f 天' % (float(result['option']))
                else:
                    enable = '关闭'
                return '您当前此功能的状态：%s\n' \
                        '开启后，当您借的某一本书的剩余天数少于您设定的剩余天数，我就会提醒您该还书了~\n' \
                        '回复 1 开启， 0关闭' % \
                        (enable)
            else:
                if int(msg['Content']) == 1:
                    self.class_database_op.set_redis_kv(userId, 'book_back_notice_enable', int(msg['Content']))
                    return '请输入您所需要的提醒值，当图书剩余天数低于这个数值我就会提醒您该还书了~'
                else:
                    self.class_database_op.set_function_info(userId, 'book_back_notice', 0, '0')
                    self.class_database_op.step_back(userId)
                    self.class_database_op.delete_redis_kv(userId, 'inputing')
                    return '设置成功!'

        self.class_database_op.step_back(userId)

        enable = self.class_database_op.get_redis_kv(userId, 'book_back_notice_enable')
        self.class_database_op.set_function_info(userId, 'book_back_notice', int(enable), str(int(msg['Content'])))

        self.class_database_op.delete_redis_kv(userId, 'book_back_notice')
        self.class_database_op.delete_redis_kv(userId, 'inputing')

        return '设置成功！'

    def renew_lend_book(self, msg, userId):

        lib = self.class_database_op.get_lib_info(userId)
        if not lib:
            self.class_database_op.step_back(userId)
            return "您还没有保存您的信息，选2来输入登录信息吧~"

        request_utils_ins = request_utils.request_utils()

        if not self.class_database_op.get_redis_kv(userId, 'inputing'):
            itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])

            books = request_utils_ins.lib_lend_book_list(userId)

            i = 0

            for book in books:
                i = i + 1

                remark = ''
                if book['remain_days'] < 0 :
                    remark = '-已超期，无法续借'

                itchatmp.send( \
                                "[%d%s]书名: %s\n" \
                                "图书条码: %s\n" \
                                "流通部门: %s\n" \
                                "流通状态: %s\n" \
                                "归还日期: %s\n" \
                                "剩余天数: %d\n" \
                                % (i, remark, book['name'], book['barcode'], book['department'], book['state'], book['back_date'], book['remain_days']), msg['FromUserName'])


            itchatmp.send("输入书名前括号内数字则续借这本书(请注意续借是将还书时间重置为从当前日期起往后十天，并不是在原先的日期上加十天)，输入0则返回上一级菜单", msg['FromUserName'])

            self.class_database_op.set_redis_kv(userId, 'inputing', 1)
        else:
            self.class_database_op.delete_redis_kv(userId, 'inputing')

            if msg['Content'] == '0':
                self.class_database_op.step_back(userId)
                return "已经返回上级菜单。"
            else:
                if request_utils_ins.lib_lend_book_renew(userId, int(msg['Content'])):
                    itchatmp.send("续借成功，请在十天之后还书哦～", msg['FromUserName'])
                else:
                    itchatmp.send("续借失败，您的输入有误或者您可能已经续借过这本书了。", msg['FromUserName'])
                self.class_database_op.step_back(userId)

    def book_auto_renew_enable(self, msg, userId):
        if not self.class_database_op.get_redis_kv(userId, 'inputing'):
            self.class_database_op.set_redis_kv(userId, 'inputing', 1)
            result = self.class_database_op.get_function_info(userId, 'book_auto_renew')
            if result['enable'] == 1:
                enable = '开启'
            else:
                enable = '关闭'
            return '您当前此功能的状态：%s\n' \
                    '开启后，您所借的图书在到期前一天我就会自动帮您尝试续借了～\n' \
                    '回复 1 开启， 0关闭' % \
                    (enable)
        else:
            enable = int(msg['Content'])

        self.class_database_op.step_back(userId)

        self.class_database_op.set_function_info(userId, 'book_auto_renew', enable, msg['Content'])

        self.class_database_op.delete_redis_kv(userId, 'inputing')
        return '设置成功！'
