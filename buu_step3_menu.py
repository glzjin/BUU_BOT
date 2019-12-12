# -*- coding: utf-8 -*
import buu_database
import buu_config
import request_utils
import itchatmp
import utils
import re
import utils

class class_step(object):

    def __init__(self):
        self.step_dict = [  \
                            (None, None), \
                            (self.test, None), \
                            (self.export_to_ical, None), \
                            (self.input_jwxt_info, None), \
                            (self.get_jwxt_info, None), \
                            (self.get_exam_list, None), \
                            (self.get_exam_cal, None), \
                            (self.auto_rank_lesson, None), \
                        ]
        self.config = buu_config.config
        self.class_database_op = buu_database.class_database_op()


    def step_tips(self, msg, userId):
        return  '1 - 列出所有安排了上课时间的课程\n' \
                '2 - 将课程表导出为 ical 文件\n' \
                '3 - 输入教务系统登录信息\n' \
                '4 - 查看教务系统登录信息\n' \
                '5 - 获取考试列表\n' \
                '6 - 将考试安排导出为 ical 文件\n' \
                '7 - 一键评教\n' \
                '其他输入 - 返回首页'

    def test(self, msg, userId):
        self.class_database_op.step_back(userId)
        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return "您还没有保存您的信息，请到校园卡菜单来输入登录信息吧~"
        request_utils_ins = request_utils.request_utils()
        results = request_utils_ins.jwxt_total_login(userId)

        if not results[0]:
            return "登录教务系统失败!"

        lessons = request_utils_ins.jwxt_get_lesson_table(userId)
        for key in lessons:
            lesson = lessons[key]
            if lesson['time'] != '':
                itchatmp.send( \
                                "课程 %s:\n" \
                                "教师: %s\n" \
                                "教室: %s\n" \
                                "上课时间: %s" \
                                % (lesson['name'], lesson['teacher_name'], lesson['room'], lesson['time']), msg['FromUserName'])

    def export_to_ical(self, msg, userId):
        self.class_database_op.step_back(userId)
        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return "您还没有保存您的信息，请到校园卡菜单来输入登录信息吧~"
        request_utils_ins = request_utils.request_utils()
        results = request_utils_ins.jwxt_total_login(userId)

        if not results[0]:
            return "登录教务系统失败!"

        lessons = request_utils_ins.jwxt_get_lesson_table(userId)
        lessons_list = []
        for key in lessons:
            lesson = lessons[key]
            if lesson['time'] != '':
                time_list = lesson['time'].split(';')
                room_list = lesson['room'].split(';')

                for i in range(0, len(time_list)):
                    ret_dict = {}
                    ret_dict['name'] = lesson['name']
                    ret_dict['teacher'] = lesson['teacher_name']
                    key_list = re.compile(r"(.*){(.*)}", flags = re.M).findall(time_list[i])
                    ret_dict['time'] = key_list[0][0]
                    ret_dict['week'] = key_list[0][1]
                    ret_dict['room'] = room_list[i]
                    lessons_list.append(ret_dict)

        cal = utils.lessons_list_to_cal(lessons_list)

        file_name = 'cache/' + str(userId) + '.ics'
        file_show_name = utils.random_string(32) + '.ics'
        with open(file_name, 'wb') as f:
            f.write(cal.to_ical())
            f.close()
        file_url = utils.upload_file(file_name, file_show_name)
        import os
        os.remove(file_name)
        itchatmp.send("请接收文件~由于微信限制，机器人不能给您直接发送文件，请将以下链接复制到外部浏览器下载～", msg['FromUserName'])
        return file_url

    def input_jwxt_info(self, msg, userId):
        current_user_name = self.class_database_op.get_redis_kv(userId, 'jwxt_user_name')
        if not current_user_name:
            if not self.class_database_op.get_redis_kv(userId, 'inputing'):
                self.class_database_op.set_redis_kv(userId, 'inputing', 1)
                return '请输入您的学号：'
            else:
                self.class_database_op.set_redis_kv(userId, 'jwxt_user_name', msg['Content'])
                return '学号已保存，接下来请输入您在 jwxt.buu.edu.cn 的密码：\n' \
                        '注意：密码会被加密储存，但由于技术限制，在使用时会被解密为明文，请您知悉。\n' \
                        '同时本系统会只访问实现功能所需要的数据，其他数据一概不访问。'

        current_password = msg['Content']

        current_user_name = current_user_name.decode('utf-8')
        self.class_database_op.save_jwxt_info(userId, current_user_name, current_password)

        self.class_database_op.delete_redis_kv(userId, 'jwxt_user_name')
        self.class_database_op.delete_redis_kv(userId, 'inputing')

        self.class_database_op.step_back(userId)

        request_utils_ins = request_utils.request_utils()
        if request_utils_ins.jwxt_stu_login_check(userId)[0]:
            return '密码已保存，系统已经保存您所输入的数据。'
        else:
            self.class_database_op.delete_jwxt_info(userId)
            return '您所输入的信息无法登录，请按 3 重新输入。'

    def get_jwxt_info(self, msg, userId):
        self.class_database_op.step_back(userId)
        jwxt = self.class_database_op.get_jwxt_info(userId)
        if jwxt:
            return "您的教务系统信息：\n学号：%s\n密码已隐藏，不给你看~" % (jwxt.user_name)
        else:
            return "您还没有保存您的信息，选 3 来输入登录信息吧~"

    def get_exam_list(self, msg, userId):
        self.class_database_op.step_back(userId)

        jwxt = self.class_database_op.get_jwxt_info(userId)
        if not jwxt:
            return "您还没有保存您的信息，选 3 来输入登录信息吧~"

        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])

        request_utils_ins = request_utils.request_utils()
        exams = request_utils_ins.jwxt_get_exam_list(userId)

        for exam in exams:
            itchatmp.send( \
                            "考试号: %s\n" \
                            "考试名: %s\n" \
                            "时间: %s\n" \
                            "考场: %s\n" \
                            "座位号: %s\n" \
                            "校区: %s\n" \
                            % (exam['exam_no'], exam['exam_name'], exam['datetime'], exam['exam_room'], exam['exam_sit_no'], exam['room_area']), msg['FromUserName'])

        itchatmp.send("考试信息输出完毕！", msg['FromUserName'])

    def get_exam_cal(self, msg, userId):
        self.class_database_op.step_back(userId)

        jwxt = self.class_database_op.get_jwxt_info(userId)
        if not jwxt:
            return "您还没有保存您的信息，选3来输入登录信息吧~"

        itchatmp.send("正在查询，请稍候。。。", msg['FromUserName'])

        request_utils_ins = request_utils.request_utils()
        exams = request_utils_ins.jwxt_get_exam_list(userId)
        print(exams)

        cal = utils.exams_list_to_cal(exams)

        file_name = 'cache/' + str(userId) + '.ics'
        file_show_name = utils.random_string(32) + '.ics'
        with open(file_name, 'wb') as f:
            f.write(cal.to_ical())
            f.close()
        file_url = utils.upload_file(file_name, file_show_name)
        import os
        os.remove(file_name)
        itchatmp.send("请接收文件~由于微信限制，机器人不能给您直接发送文件，请将以下链接复制到外部浏览器下载～", msg['FromUserName'])
        return file_url

    def auto_rank_lesson(self, msg, userId):
        self.class_database_op.step_back(userId)

        jwxt = self.class_database_op.get_jwxt_info(userId)
        if not jwxt:
            return "您还没有保存您的信息，选 3 来输入登录信息吧~"

        itchatmp.send("正在操作，请稍候。。。", msg['FromUserName'])

        request_utils_ins = request_utils.request_utils()
        lessons = request_utils_ins.jwxt_get_rank_list(userId)

        for lesson in lessons:
            itchatmp.send("正在评价" + lesson['lesson_name'], msg['FromUserName'])
            request_utils_ins.jwxt_rank_lesson(userId, lesson['lesson_url'])

        if len(lessons) > 1:
            request_utils_ins.jwxt_rank_lessons_submit(userId, lessons[-1]['lesson_url'])

        itchatmp.send("评价完毕！", msg['FromUserName'])
