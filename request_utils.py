# -*- coding: utf-8 -*
import requests
import re
import buu_config, buu_database
import utils
from PIL import Image
import pytesseract
import io
import time
import json
import urllib

class request_utils(object):
    def __init__(self):
        self.config = buu_config.config
        requests.packages.urllib3.disable_warnings()
        self.session = requests.Session()
        self.has_login_vpn = False
        self.has_login_mybuu = False
        self.has_login_card = False
        self.has_login_jwxt = False
        self.stu_jwxt_url = ''
        self.has_login_lib = False
        self.class_database_op = buu_database.class_database_op()

    def __del__(self):
        self.session.close()

    # def webvpn_login(self, userId):
    #     card = self.class_database_op.get_card_info(userId)
    #     if not card:
    #         return False
    #
    #     r = self.session.get('https://webvpn.buu.edu.cn/users/sign_in')
    #     csrf_token = re.compile('<meta name="csrf-token" content="(.*)" />').findall(r.text)[0]
    #
    #     password = self.class_database_op.get_card_info_password(card.password)
    #     payload = {'utf8': '✓', 'authenticity_token': csrf_token, \
    #                 'user[login]': card.user_name, 'user[password]': password, \
    #                 'commit': '登            录'}
    #     r = self.session.post("https://webvpn.buu.edu.cn/users/sign_in", data = payload)
    #
    #     try:
    #         re.compile('<li><a rel="nofollow" data-method="delete" href="/users/sign_out">(.*)</a></li>').findall(r.text)[0]
    #         return True
    #     except Exception:
    #         raise

    def webvpn_login(self, userId):
        self.session.verify = False
        self.session.proxies = self.config.vpn_proxies
        self.session.timeout = 10
        self.session.headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}

        #self.get_login_cookie(self.config.admin_id)

        # while True:
        #     r = self.session.get(self.get_real_domain("www"))
        #     print(r.text)
        #     if r.text.find("Not Found") == -1:
        #         continue


        # self.has_login_vpn = True
        return True


    def get_real_domain(self, domain_prefix, suffix = "", is_https = False):
        if utils.is_ip(domain_prefix):
            if is_https:
                return "https://" + domain_prefix + "/" + suffix
            else:
                return "http://" + domain_prefix + "/" + suffix
        else:
            if is_https:
                return "https://" + domain_prefix + ".buu.edu.cn" + "/" + suffix
            else:
                return "http://" + domain_prefix + ".buu.edu.cn" + "/" + suffix

        # if self.config.need_vpn:
        #     # if utils.is_ip(domain_prefix):
        #     #     domain_prefix = domain_prefix.replace('.', '-')
        #     # return "https://" + domain_prefix + ".webvpn.buu.edu.cn" + suffix
        #
        #     if utils.is_ip(domain_prefix):
        #         return "https://vpn.buu.edu.cn/web/1/http/2/" + domain_prefix + suffix
        #     else:
        #         return "https://vpn.buu.edu.cn/web/1/http/2/" + domain_prefix + ".buu.edu.cn" +  suffix
        # else:
        #     if utils.is_ip(domain_prefix):
        #         return "http://" + domain_prefix + suffix
        #     else:
        #         return "http://" + domain_prefix + ".buu.edu.cn" + suffix

    def get_real_domain_encoded(self, domain_prefix, suffix = ""):
        # import urllib
        # if self.config.need_vpn:
        #     if utils.is_ip(domain_prefix):
        #         domain_prefix = domain_prefix.replace('.', '-')
        #     return urllib.parse.quote_plus("https://" + domain_prefix + ".webvpn.buu.edu.cn" + suffix)
        # else:
        if utils.is_ip(domain_prefix):
            return urllib.parse.quote_plus("http://" + domain_prefix + "/" + suffix)
        else:
            return urllib.parse.quote_plus("http://" + domain_prefix + ".buu.edu.cn/" + suffix)

    def www_keepalive(self):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(1):
                return

        try:
            self.session.get(self.get_real_domain("jwc"))
        except Exception:
            pass

        try:
            self.session.get(self.get_real_domain("my"))
        except Exception:
            return (True, None, None)

        try:
            self.session.get(self.get_real_domain("10.11.7.20"))
        except Exception:
            return (True, None, None)



    def login_check(self, userId):
        card = self.class_database_op.get_card_info(userId)
        if not card:
            return False

        password = self.class_database_op.get_card_info_password(card.password)
        payload = {'mitm_result': '', 'svpn_name': card.user_name, 'svpn_password': password, 'svpn_rand_code': ''}
        r = self.session.post('https://vpn.buu.edu.cn/por/login_psw.csp?encrypt=0', data = payload, verify = False)

        try:
            re.compile('\u6ce8\u9500').findall(r.text)[0]
            return True
        except Exception:
            return False

    # def get_login_cookie(self, userId):
    #     card = self.class_database_op.get_card_info(userId)
    #     if not card:
    #         return False
    #
    #     password = self.class_database_op.get_card_info_password(card.password)
    #     payload = {'mitm_result': '', 'svpn_name': card.user_name, 'svpn_password': password, 'svpn_rand_code': ''}
    #     r = self.session.post('https://vpn.buu.edu.cn/por/login_psw.csp?encrypt=0', data = payload, verify = False)
    #
    #     try:
    #         return self.session.cookies.get_dict()
    #     except Exception:
    #         return False

    def mybuu_get_code(self):
        #https://ids.webvpn.buu.edu.cn/authserver/captcha.html
        with self.session.get(self.get_real_domain("ids") + "authserver/captcha.html", stream=True) as r:
            imageStorage = io.BytesIO()
            for block in r.iter_content(1024):
                imageStorage.write(block)
            imageStorage.seek(0)
            image = Image.open(imageStorage)
            return image

        return None

    def is_code(self, code):
        #^(\w?){4}$
        try:
            if len(code) != 4:
                return False
            re.compile(r'^(\w?){4}$').findall(code)[0]
            return True
        except Exception:
            return False

    def mybuu_code_solve(self):
        image = self.mybuu_get_code()

        code = pytesseract.image_to_string(image, lang = 'eng', config = '-psm 8 -oem 3')

        while not self.is_code(code):
            image = self.mybuu_get_code()
            code = pytesseract.image_to_string(image, lang = 'eng', config = '-psm 8 -oem 3')

        return code

    def mybuu_login_with_code(self, userId, execution, lt):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        card = self.class_database_op.get_card_info(userId)
        password = self.class_database_op.get_card_info_password(card.password)

        payload = {'username': card.user_name, 'password': password, \
                    'lt': lt, 'execution': execution, \
                    '_eventId': 'submit', 'rmShown': 1, \
                    'captchaResponse': self.mybuu_code_solve()}
        r = self.session.post(self.get_real_domain("ids") + "authserver/login?service=" + self.get_real_domain_encoded("my"), data = payload)
        #\u57f9\u517b\u5c42\u6b21

        try:
            #登陆成功
            re.compile('\u57f9\u517b\u5c42\u6b21').findall(r.text)[0]
        except Exception:
            try:
                #密码错误
                re.compile('\u5bc6\u7801\u9519\u8bef').findall(r.text)[0]
                return (False, None, None)
            except Exception:
                try:
                    #验证码
                    re.compile('\u9a8c\u8bc1\u7801').findall(r.text)[0]
                    execution = re.compile('<input type="hidden" name="execution" value="(.*?)" />').findall(r.text)[0]
                    lt = re.compile('<input type="hidden" name="lt" value="(.*?)" />').findall(r.text)[0]
                    return (False, execution, lt)
                except Exception:
                    return (True, None, None)
        self.has_login_mybuu = True
        return (True, None, None)

    def mybuu_login(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        r = self.session.get(self.get_real_domain("ids") + "authserver/login?service=" + self.get_real_domain_encoded("my"))

        card = self.class_database_op.get_card_info(userId)
        if card:
            password = self.class_database_op.get_card_info_password(card.password)
            lt = re.compile('<input type="hidden" name="lt" value="(.*?)" />').findall(r.text)[0]

            payload = {'username': card.user_name, 'password': password, \
                        'lt': lt, 'execution': 'e1s1', \
                        '_eventId': 'submit', 'rmShown': 1}
            r = self.session.post(self.get_real_domain("ids") + "authserver/login?service=" + self.get_real_domain_encoded("my"), data = payload)
            #\u57f9\u517b\u5c42\u6b21
            try:
                re.compile('\u57f9\u517b\u5c42\u6b21').findall(r.text)[0]
            except Exception:
                try:
                    re.compile('\u9a8c\u8bc1\u7801').findall(r.text)[0]
                    userName = self.class_database_op.get_username_by_id(userId)
                    execution = re.compile('<input type="hidden" name="execution" value="(.*?)" />').findall(r.text)[0]
                    lt = re.compile('<input type="hidden" name="lt" value="(.*?)" />').findall(r.text)[0]
                    result = self.mybuu_login_with_code(userId, execution, lt)

                    while not result[0] and result[1] and result[2]:
                        result = self.mybuu_login_with_code(userId, result[1], result[2])

                    return self.has_login_mybuu
                except Exception:
                    import traceback
                    traceback.print_exc()
                    pass
                return False
            self.has_login_mybuu = True
            return True
        else:
            return False

    def card_login(self, userId):
        if not self.has_login_mybuu:
            self.mybuu_login(userId)

        r = self.session.get(self.get_real_domain("ids") + "authserver/login?service=" + self.get_real_domain_encoded("10.11.10.13", "lhdxPortalHome.action"))
        self.has_login_card = True

    def card_balance_check(self, userId):
        if not self.has_login_card:
            self.card_login(userId)

        # https://10-11-10-13.webvpn.buu.edu.cn/pages/card/cardMain.jsp
        # https://10-11-10-13.webvpn.buu.edu.cn/accountcardUser.action
        # payload = {'imageField.x': 30, 'imageField.y': 12}
        # r = self.session.post(self.get_real_domain("10.11.10.13") + "pages/card/cardMain.jsp", data = payload)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        try:
            balance = {}
            # <td class="neiwen">67.60元（卡余额）0.00元(当前过渡余额)0.00元(上次过渡余额)</td>
            balance['current'] = round(float(re.compile(r"<td class=\"neiwen\">(.*)\u5143\uff08\u5361\u4f59\u989d\uff09").findall(r.text)[0]), 2)
            balance['current_pending'] = round(float(re.compile(r"\u5143\uff08\u5361\u4f59\u989d\uff09(.*)\u5143\u0028\u5f53\u524d\u8fc7\u6e21\u4f59\u989d\u0029").findall(r.text)[0]), 2)
            balance['pre_pending'] = round(float(re.compile(r"\u5143\u0028\u5f53\u524d\u8fc7\u6e21\u4f59\u989d\u0029(.*)\u5143\u0028\u4e0a\u6b21\u8fc7\u6e21\u4f59\u989d\u0029").findall(r.text)[0]), 2)
            return balance
        except Exception:
            import traceback
            traceback.print_exc()
            return None

    def card_get_today_total(self, userId):
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        user_account_id = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)[1]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounttodatTrjnObject.action", data = payload)

        today_total = round(float(re.compile(r"\u603b\u4ea4\u6613\u989d\u4e3a\u003a(.*)\uff08\u5143\uff09").findall(r.text)[0]), 2)
        return today_total

    def card_get_history_log(self, userId, begindate, enddate):
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        user_account_id = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)[1]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounthisTrjn.action", data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + next_url, data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        payload = {'inputStartDate': begindate, 'inputEndDate': enddate}

        r = self.session.post(self.get_real_domain("10.11.10.13") + next_url, data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounthisTrjn.action" + next_url)

        pagenum = int(re.compile(r"\u5171(.*)\u9875\u0026\u006e\u0062\u0073\u0070\u003b\u0026\u006e\u0062\u0073\u0070\u003b\u5f53\u524d\u7b2c").findall(r.text)[0])

        ret_list = []
        try:
            for current_page in range(1, pagenum + 1):
                payload = {'inputStartDate': begindate, 'inputEndDate': enddate, 'pageNum': current_page}
                r = self.session.post(self.get_real_domain("10.11.10.13") + "accountconsubBrows.action", data = payload)
                temp_list = re.compile(r"<tr class=\"listbg", flags = re.DOTALL).findall(r.text)

                key_list = re.compile(r"<td(.*)align=\"(center|right)\"( |)>(\S*|(\S*\s\S*))(\s*|)</td>", flags = re.M).findall(r.text)

                key_list = key_list[5:]

                item_len = len(temp_list)

                for i in range(0, item_len):
                    single_item = {}
                    single_item['time'] = key_list[i * 9][3]
                    single_item['user_name'] = key_list[i * 9 + 1][3]
                    single_item['user_real_name'] = key_list[i * 9 + 2][3]
                    single_item['type'] = key_list[i * 9 + 3][3]
                    single_item['sub_system_name'] = key_list[i * 9 + 4][3]
                    single_item['amount'] = float(key_list[i * 9 + 5][3])
                    single_item['current_balance'] = float(key_list[i * 9 + 6][3])
                    single_item['count'] = int(key_list[i * 9 + 7][3])
                    single_item['status'] = key_list[i * 9 + 8][3]
                    ret_list.append(single_item)
            return ret_list
        except Exception:
            import traceback
            traceback.print_exc()
            return None

    def card_get_today_log(self, userId):
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        user_account_id = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)[1]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounttodatTrjnObject.action", data = payload)

        ret_list = []

        temp_list = re.compile(r"<tr class=\"listbg", flags = re.DOTALL).findall(r.text)

        key_list = re.compile(r"<td(.*)align=\"(center|right)\"( |)>(\S*|(\S*\s\S*))(\s*|)</td>", flags = re.M).findall(r.text)

        key_list = key_list[9:]

        item_len = len(temp_list)

        ret_list = []
        for i in range(0, item_len):
            single_item = {}
            single_item['time'] = key_list[i * 10][3]
            single_item['user_name'] = key_list[i * 10 + 1][3]
            single_item['user_real_name'] = key_list[i * 10 + 2][3]
            single_item['type'] = key_list[i * 10 + 3][3]
            single_item['sub_system_name'] = key_list[i * 10 + 4][3]
            single_item['e_account'] = key_list[i * 10 + 5][3]
            single_item['amount'] = float(key_list[i * 10 + 6][3])
            single_item['current_balance'] = float(key_list[i * 10 + 7][3])
            single_item['count'] = int(key_list[i * 10 + 8][3])
            single_item['status'] = key_list[i * 10 + 9][3]
            ret_list.append(single_item)
        return ret_list

    def card_get_today_total_consume(self, userId):
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        user_account_id = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)[1]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounttodatTrjnObject.action", data = payload)

        consume_amount = float(re.compile(r"\u603b\u4ea4\u6613\u989d\u4e3a\u003a(.*)\uff08\u5143\uff09").findall(r.text)[0])

        return consume_amount

    def card_get_total_consume(self, userId, begindate, enddate):
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        user_account_id = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)[1]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounthisTrjn.action", data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        payload = {'account': user_account_id, 'inputObject': 'all', \
                    'Submit': ' 确 定 '}

        r = self.session.post(self.get_real_domain("10.11.10.13") + next_url, data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        payload = {'inputStartDate': begindate, 'inputEndDate': enddate}

        r = self.session.post(self.get_real_domain("10.11.10.13") + next_url, data = payload)

        next_url = re.compile(r"action=\"(.*)\" method=\"post").findall(r.text)[0]

        r = self.session.post(self.get_real_domain("10.11.10.13") + "accounthisTrjn.action" + next_url)

        consume_amount = float(re.compile(r"\u603b\u8ba1\u4ea4\u6613\u989d\u4e3a\u003a(.*)\uff08\u5143\uff09").findall(r.text)[0])

        return consume_amount

    def card_get_account_info(self, userId):
        result = {}
        if not self.has_login_card:
            self.card_login(userId)

        r = self.session.get(self.get_real_domain("10.11.10.13") + "accountcardUser.action")

        info_list = re.compile(r"<div align=\"left\">(.*)</div>").findall(r.text)
        result['real_name'] = info_list[0]
        result['idcard_number'] = info_list[10]
        return result

    def jwxt_get_code(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        import io

        r = self.session.get(self.get_real_domain("jwxt") + "default_jz.aspx")
        viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]

        with self.session.get(self.get_real_domain("jwxt") + "CheckCode.aspx", stream=True) as r:
            imageStorage = io.BytesIO()
            for block in r.iter_content(1024):
                imageStorage.write(block)
            imageStorage.seek(0)
            return (imageStorage, viewstate)

        return (None, None)

    def jwxt_login(self, userId, real_name, idcard_number, captcha, viewstate):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        payload = {'__VIEWSTATE': viewstate, 'txtXsxm': real_name.encode('gb2312'), \
                    'txtXssfzh': idcard_number, 'txtYzm': captcha, \
                    'btnLogin': 'a'}

        self.session.headers.update({'referer': self.get_real_domain("jwxt") + 'default_jz.aspx'})
        r = self.session.post(self.get_real_domain("jwxt") + 'default_jz.aspx', data = payload)

        if r.text.find('同学的家长') == -1:
            if r.text.find('<验证码>不正确！'):
                return (False, True)
            else:
                return (False, False)
        else:
            student_no = re.compile(r"xh=(.*)\" target=\"_blank\">").findall(r.text)[0]
            return (True, False, student_no)

    def jwxt_total_login(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        results = self.card_get_account_info(userId)
        img = self.jwxt_get_code(userId)
        viewstate = img[1]

        from zfcode import verify
        captcha = verify.verify(img[0])

        login_result = self.jwxt_login(userId, results['real_name'], results['idcard_number'], captcha, img[1])
        if not login_result[0] and login_result[1]:
            while login_result[1]:
                img = self.jwxt_get_code(userId)
                viewstate = img[1]

                from zfcode import verify
                captcha = verify.verify(img[0])

                login_result = self.jwxt_login(userId, results['real_name'], results['idcard_number'], captcha, img[1])

        if login_result[0]:
            return (True, login_result[2])
        else:
            return (False, None)

    def jwxt_get_lesson_table(self, userId):
        if not self.has_login_jwxt:
            result = self.jwxt_total_login(userId)
            if not result[0]:
                return

        card = self.class_database_op.get_card_info(userId)
        if not card:
            return

        student_no = card.user_name

        r = self.session.get(self.get_real_domain("jwxt") + 'xsxkqk.aspx?xh=' + student_no)
        key_list = re.compile(r"<td>(.*?)</td>", flags = re.M).findall(r.text)
        time_list = re.compile(r"<span id=\"DBGrid__ctl(\d*?)_Label4\">(.*?)</span>", flags = re.M).findall(r.text)

        key_list = key_list[16:]

        ret_list = {}

        item_count = int(len(key_list) / 15)
        for i in range(0, item_count):
            ret_key_dict = {}
            ret_key_dict['no'] = key_list[i * 15]
            ret_key_dict['code'] = key_list[i * 15 + 1]
            ret_key_dict['name'] = self.get_real_name(key_list[i * 15 + 2])
            ret_key_dict['type'] = key_list[i * 15 + 3]
            ret_key_dict['has_chosen'] = key_list[i * 15 + 4]
            ret_key_dict['teacher_name'] = self.get_real_name(key_list[i * 15 + 5])
            ret_key_dict['point'] = key_list[i * 15 + 6]
            ret_key_dict['weekly_hour'] = key_list[i * 15 + 7]
            ret_key_dict['time'] = time_list[i][1]
            ret_key_dict['room'] = key_list[i * 15 + 8]
            ret_key_dict['text_book'] = key_list[i * 15 + 9]
            ret_key_dict['study_mark'] = key_list[i * 15 + 10]
            ret_key_dict['teach_plan_upload_count'] = key_list[i * 15 + 10]
            ret_key_dict['teach_plan_upload_time'] = key_list[i * 15 + 10]
            ret_key_dict['teach_plan_upload_filename'] = key_list[i * 15 + 10]
            ret_key_dict['teach_plan_upload_download'] = key_list[i * 15 + 10]
            ret_list[ret_key_dict['name']] = ret_key_dict

        r = self.session.get(self.get_real_domain("jwxt") + 'xskbcx.aspx?xh=' + student_no)
        key_list = re.compile(r"<td (.*?|)align=\"Center\"(.*?|)>(.*?)</td>", flags = re.M).findall(r.text)

        key_list = key_list[5:]
        # 数据结构 A<br>周一第3,4节{第9-16周}<br>付百文(付百文)<br>教4007<br><br>离散数学<br>周一第3,4节{第1-8周}<br>何宁<br>教4003
        for key in key_list:
            if key[2] != '&nbsp;':
                sub_key_list = key[2].split('<br><br>')
                item_count = len(sub_key_list)
                for i in range(0, item_count):
                    child_key_list = sub_key_list[i].split('<br>')
                    ret_key_dict = {}
                    if len(child_key_list) >= 4:
                        ret_key_dict['name'] = child_key_list[0]
                        ret_key_dict['time'] = child_key_list[1]
                        ret_key_dict['teacher_name'] = child_key_list[2]
                        ret_key_dict['room'] = child_key_list[3]

                    #周二第10,11节{第1-16周}
                    try:
                        info_day = re.findall(r'周(.*?)第(.*?)节\{(.*?)\}', ret_key_dict['time'], re.M)
                        info_day[0]
                    except Exception:
                        continue

                    if ret_key_dict['name'] in ret_list:
                        if ret_list[ret_key_dict['name']]['time'].find(ret_key_dict['time']) == -1:
                            ret_list[ret_key_dict['name']]['time'] += ';' + ret_key_dict['time']
                            ret_list[ret_key_dict['name']]['room'] += ';' + ret_key_dict['room']
                    else:
                        ret_list[ret_key_dict['name']] = ret_key_dict

        return ret_list

    def get_real_name(self, raw_text):
        return re.compile(r"<a(.*?)>(.*?)</a>", flags = re.M).findall(raw_text)[0][1]

    def html_code_free(self, raw_text):
        return utils.remove_html_tag(raw_text.replace('&nbsp;', '').replace('<font color=#FF0000>', '').replace('</font>', '').replace("\n",""))

    def lib_search_books(self, word, page):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        #library_id=all&recordtype=all&kind=simple&suchen_word=1984&suchen_type=1&suchen_match=qx&kind=simple&show_type=wenzi&snumber_type=Y&search_no_type=Y&searchtimes=1&size=20&curpage=1&orderby=pubdate_date&ordersc=desc&page=1&pagesize=20
        payload = { \
                    'solrType': 'TITLE', 'pageNo': page, 'pageSize': 30, \
                    'keyword': word, 'classSearch': 0, 'word_publisher_facet': '', \
                    'type_publisher_facet': '', 'word_subject_facet': '', 'type_subject_facet': '', \
                    'word_classno_facet': '', 'type_classno_facet': '', 'word_material_facet': '', \
                    'type_material_facet': '', 'limit_publisher_facet': '', 'limit_subject_facet': '', \
                    'limit_classno_facet': '', 'limit_material_facet': '', 'searchPrecision': '', \
                    'xiaoqu': 'all'
                    }

        self.session.headers['Referer'] = self.get_real_domain('opac', is_https = True) + 'search-full-result.html'
        r = self.session.post(self.get_real_domain('opac', is_https = True) + 'search-full-result.json', data = payload, verify = False)
        result = r.json()

        total_page = result['totalPage']

        ret_list = []

        for single_item in result['data']:
            ret_key_dict = {}
            ret_key_dict['name'] = self.html_code_free(single_item['title'])[10:]
            ret_key_dict['author'] = single_item['authors']
            ret_key_dict['publisher'] = single_item['publisher']
            ret_key_dict['isbn'] = single_item['isn']
            ret_key_dict['publish_year'] = single_item['pubdateDate']
            ret_key_dict['search_book_no'] = single_item['bookSearchNo']
            ret_key_dict['have_number'] = int(single_item['guancangCount'])
            ret_key_dict['av_number'] = int(single_item['kejieCount'])
            ret_list.append(ret_key_dict)

        return (ret_list, total_page)

    def send_email(self, file_name, printer):
        destination = ['glzjin@zhaojin97.cn', printer.printer_value]

        text_subtype = 'plain'


        content="""\
        Test message
        """

        subject="打印"

        from os.path import basename

        from smtplib import SMTP_SSL as SMTP

        from email.mime.multipart import MIMEMultipart
        from email.mime.application import MIMEApplication
        from email.mime.text import MIMEText
        from email.utils import COMMASPACE, formatdate

        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From']   = self.config.smtp_sender
            msg['To'] = COMMASPACE.join(destination)
            msg['Date'] = formatdate(localtime=True)
            msg.attach(MIMEText(content))

            with open(file_name, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name = basename(file_name).decode('utf-8')
                )
            # After the file is closed
            part['Content-Disposition'] = 'attachment; filename="%s"' % basename(file_name).decode('utf-8')
            msg.attach(part)

            conn = SMTP(self.config.smtp_server)
            conn.set_debuglevel(False)
            conn.login(self.config.smtp_username, self.config.smtp_password)
            try:
                conn.sendmail(self.config.smtp_sender, destination, msg.as_string())
            finally:
                conn.quit()

            return True
        except Exception:
            import traceback
            traceback.print_exc()
            return False

    def lib_login(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        lib = self.class_database_op.get_lib_info(userId)
        if not lib:
            return False

        password = self.class_database_op.get_lib_info_password(lib.password)
        payload = { \
                    'login_type': 'ident_id', 'account': lib.user_name, 'password': password
                    }

        self.session.headers['Referer'] = self.get_real_domain('opac', is_https = True) + 'index.html'
        r = self.session.post(self.get_real_domain('opac', is_https = True) + 'logon.json', data = payload)

        result = r.json()
        # print(payload)

        if result['result']['code'] == 0:
            return True
        else:
            return False

    def lib_login_check(self, userId):
        return self.lib_login(userId)

    def lib_lend_book_list(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_lib:
            result = self.lib_login(userId)
            if not result:
                return

        lib = self.class_database_op.get_lib_info(userId)
        if not lib:
            return False

        self.session.headers['Referer'] = self.get_real_domain('opac', is_https = True) + 'reader-borrowinfo.html'
        payload = {
            'pageNo': 1,
            'pageSize': 100
        }
        r = self.session.post(self.get_real_domain('opac', is_https = True) + 'reader-borrowinfo.json', data = payload)
        result = r.json()

        ret_list = []

        for item in result['data']:
            ret_key_dict = {}
            ret_key_dict['name'] = item['title']
            ret_key_dict['barcode'] = item['bookBarcode']
            ret_key_dict['department'] = item['depName']
            ret_key_dict['state'] = item['statusDesc']
            ret_key_dict['back_date'] = item['mydate']

            days = time.mktime(time.strptime(ret_key_dict['back_date'], '%Y/%m/%d'))

            ret_key_dict['remain_days'] = int((days - current_day) / 86400)

            if ret_key_dict['remain_days'] >= 0:
                ret_key_dict['renew_barcode'] = item['bookBarcode']
                ret_key_dict['renew_department_id'] = item['departmentId']
                ret_key_dict['renew_library_id'] = item['libraryId']

            ret_list.append(ret_key_dict)

        return ret_list

    def lib_lend_book_renew(self, userId, index):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_lib:
            result = self.lib_login(userId)
            if not result:
                return

        lib = self.class_database_op.get_lib_info(userId)
        if not lib:
            return False

        i = 0
        for book in self.lib_lend_book_list(userId):
            i = i + 1

            if i == index:
                if 'renew_barcode' not in book:
                    return False

                payload = { \
                            'bookBarCode': book['renew_barcode'], 'departmentId': book['renew_department_id'], 'libraryId': book['renew_library_id']
                            }
                r = self.session.post(self.get_real_domain('opac', is_https = True) + 'xujie.json', data = payload)

                result = r.json()

                if result['result']['code'] == -1:
                    return False
                else:
                    return True

        return False

    def jwxt_stu_get_code(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        import io

        r = self.session.get(self.get_real_domain("jwxt") + "")
        viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]

        with self.session.get(self.get_real_domain("jwxt") + "CheckCode.aspx", stream=True) as r:
            imageStorage = io.BytesIO()
            for block in r.iter_content(1024):
                imageStorage.write(block)
            imageStorage.seek(0)
            return (imageStorage, viewstate)

        return (None, None)

    def jwxt_stu_login_process(self, userId, idcard_number, password, captcha, viewstate):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(userId):
                return

        payload = {'__VIEWSTATE': viewstate, 'txtUserName': idcard_number, \
                    'Textbox1': '', 'TextBox2': password, \
                    'txtSecretCode': captcha, 'RadioButtonList1': '%D1%A7%C9%FA', \
                    'Button1': '', 'lbLanguage': '', \
                    'hidPdrs': '', 'hidsc': '', \
                    }

        self.session.headers.update({'referer': self.get_real_domain("jwxt")})
        r = self.session.post(self.get_real_domain("jwxt") + 'default2.aspx', data = payload)

        if r.text.find('学生个人课表') == -1:
            if r.text.find('验证码不正确') != -1:
                return (False, True)
            else:
                return (False, False)
        else:
            self.has_login_jwxt = True
            self.stu_jwxt_url = r.text
            return (True, False, idcard_number, r.text)

    def jwxt_stu_login_check(self, userId):
        return self.jwxt_stu_login(userId)

    def jwxt_stu_login(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        result = self.class_database_op.get_jwxt_info(userId)
        img = self.jwxt_stu_get_code(userId)
        viewstate = img[1]

        from zfcode import verify
        captcha = verify.verify(img[0])

        password = self.class_database_op.get_jwxt_info_password(result.password)

        login_result = self.jwxt_stu_login_process(userId, result.user_name, password, captcha, img[1])
        if not login_result[0] and login_result[1]:
            while login_result[1]:
                img = self.jwxt_stu_get_code(userId)
                viewstate = img[1]

                from zfcode import verify
                captcha = verify.verify(img[0])

                login_result = self.jwxt_stu_login_process(userId, result.user_name, password, captcha, img[1])

        if login_result[0]:
            return (True, login_result[2])
        else:
            return (False, None)

    def jwxt_get_exam_list(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_jwxt:
            result = self.jwxt_stu_login(userId)
            if not result[0]:
                return

        exam_url = re.compile(r'学生个人课表</a></li><li><a href="(.*?)" target=\'zhuti\' onclick="GetMc\(\'学生考试查询\'\);">').findall(self.stu_jwxt_url)[0]
        r = self.session.get(self.get_real_domain("jwxt") + '' + exam_url)

        key_list = re.compile(r"<td>(.*)</td><td>(.*)</td><td>(.*)</td><td>(.*)</td><td>(.*)</td><td>&nbsp;</td><td>(.*)</td><td>(.*)</td>", flags = re.M).findall(r.text)

        return_list = []
        for exam in key_list:
            temp_dict = {}
            temp_dict['exam_no'] = exam[0]
            temp_dict['exam_name'] = exam[1]
            temp_dict['user_name'] = exam[2]
            temp_dict['datetime'] = exam[3]
            temp_dict['exam_room'] = exam[4]
            temp_dict['exam_sit_no'] = exam[5]
            temp_dict['room_area'] = exam[6]
            return_list.append(temp_dict)

        return return_list

    def jwxt_get_rank_list(self, userId):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_jwxt:
            result = self.jwxt_stu_login(userId)
            if not result[0]:
                return

        lessons_rank_url = re.compile(r'<a href="xsjxpj.aspx\?(.*?)" target=\'zhuti\' onclick="GetMc\(\'(.*?)\'\);">').findall(self.stu_jwxt_url)
        # <a href="xsjxpj.aspx?xkkh=(2017-2018-2)-CPU326011T-20030162-1&xh=2016080360054&gnmkdm=N12141" target='zhuti' onclick="GetMc('计算机网络');">计算机网络</a>

        return_list = []
        for lesson in lessons_rank_url:
            temp_dict = {}
            temp_dict['lesson_url'] = 'xsjxpj.aspx?' + lesson[0]
            temp_dict['lesson_name'] = lesson[1]
            return_list.append(temp_dict)

        return return_list

    def jwxt_rank_lesson(self, userId, lesson_url):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_jwxt:
            result = self.jwxt_stu_login(userId)
            if not result[0]:
                return

        self.session.headers['Referer'] = 'http://jwxt.buu.edu.cn/xs_main.aspx';
        r = self.session.get(self.get_real_domain("jwxt") + "" + lesson_url)
        viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]
        pkjc = re.compile(r"xkkh=(.*?)&xh=").findall(lesson_url)[0]
        select_list = re.compile(r"<select name=\"(.*)\" id=\"(.*)\">", flags = re.M).findall(r.text)[2:]
        drop_down_list = re.compile(r"<option( selected=\"selected\" | )value=\"(\d*)__\">(.*)</option>").findall(r.text)

        for drop_down_single_list in drop_down_list:

            drop_down = drop_down_single_list[1]
            payload = {'__VIEWSTATE': viewstate, '__EVENTTARGET': '', \
                        '__EVENTARGUMENT': '', 'pjkc': pkjc.encode('gb2312'), \
                        'DropDownList1': drop_down + '__', 'pjxx':'', \
                        'txt1': '', 'TextBox1': '0', \
                        'Button1': ' 保  存 '.encode('gb2312')
                        }

            r = self.session.post(self.get_real_domain("jwxt") + "" + lesson_url, data = payload)
            viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]
            pkjc = re.compile(r"xkkh=(.*?)&xh=").findall(lesson_url)[0]
            select_list = re.compile(r"<select name=\"(.*)\" id=\"(.*)\">", flags = re.M).findall(r.text)[2:]

            payload = {'__VIEWSTATE': viewstate, '__EVENTTARGET': '', \
                        '__EVENTARGUMENT': '', 'pjkc': pkjc.encode('gb2312'), \
                        'DropDownList1': drop_down + '__', 'pjxx':'', \
                        'txt1': '', 'TextBox1': '0', \
                        'Button1': ' 保  存 '.encode('gb2312')
                        }

            import random
            for select in select_list:
                payload[select[0]] = random.choice(['非常满意'.encode('gb2312'), '满意'.encode('gb2312')])
                payload[select[0].replace('js', 'txtjs').replace('JS', 'txtjs')] = ''

            self.session.headers.update({'referer': self.get_real_domain("jwxt") + "" + lesson_url})
            r = self.session.post(self.get_real_domain("jwxt") + "" + lesson_url, data = payload)

    def jwxt_rank_lessons_submit(self, userId, lesson_url):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        if not self.has_login_jwxt:
            result = self.jwxt_stu_login(userId)
            if not result[0]:
                return

        self.session.headers['Referer'] = 'http://jwxt.buu.edu.cn/xs_main.aspx';
        r = self.session.get(self.get_real_domain("jwxt") + "" + lesson_url)
        viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]
        pkjc = re.compile(r"xkkh=(.*?)&xh=").findall(lesson_url)[0]
        select_list = re.compile(r"<select name=\"(.*)\" id=\"(.*)\">", flags = re.M).findall(r.text)[2:]
        drop_down_list = re.compile(r"<option( selected=\"selected\" | )value=\"(\d*)__\">(.*)</option>").findall(r.text)

        for drop_down_single_list in drop_down_list:

            drop_down = drop_down_single_list[1]
            payload = {'__VIEWSTATE': viewstate, '__EVENTTARGET': '', \
                        '__EVENTARGUMENT': '', 'pjkc': pkjc.encode('gb2312'), \
                        'DropDownList1': drop_down + '__', 'pjxx':'', \
                        'txt1': '', 'TextBox1': '0', \
                        'Button2': ' 提  交 '.encode('gb2312')
                        }

            r = self.session.post(self.get_real_domain("jwxt") + "" + lesson_url, data = payload)
            viewstate = re.compile(r"name=\"__VIEWSTATE\" value=\"(.*)\" />").findall(r.text)[0]
            pkjc = re.compile(r"xkkh=(.*?)&xh=").findall(lesson_url)[0]
            select_list = re.compile(r"<select name=\"(.*)\" id=\"(.*)\">", flags = re.M).findall(r.text)[2:]

            payload = {'__VIEWSTATE': viewstate, '__EVENTTARGET': '', \
                        '__EVENTARGUMENT': '', 'pjkc': pkjc.encode('gb2312'), \
                        'DropDownList1': drop_down + '__', 'pjxx':'', \
                        'txt1': '', 'TextBox1': '0', \
                        'Button2': ' 提  交 '.encode('gb2312')
                        }

            for select in select_list[:-1]:
                payload[select[0]] = '非常满意'.encode('gb2312')
                payload[select[0].replace('JS1', 'txtjs1')] = ''

            payload[select_list[-1][0]] = '满意'.encode('gb2312')
            payload[select_list[-1][0].replace('JS1', 'txtjs1')] = ''

            self.session.headers.update({'referer': self.get_real_domain("jwxt") + "" + lesson_url})
            r = self.session.post(self.get_real_domain("jwxt") + "" + lesson_url, data = payload)

            return

    def baidu_wenku_download(self, download_link):
        if self.config.need_vpn and not self.has_login_vpn:
            if not self.webvpn_login(self.config.admin_id):
                return

        #模拟
        r = self.session.get(download_link)

        docId = re.compile(r'<input name="doc_id" value="(.*?)" type="hidden" />').findall(r.text)[0]
        downloadToken = re.compile(r'<input type="hidden" name="downloadToken" value="(.*?)" />').findall(r.text)[0]
        sz = re.compile(r'<input type="hidden" name="sz" value="(.*?)">').findall(r.text)[0]
        ct = re.compile(r'<input name="ct" value="(.*?)" type="hidden" />').findall(r.text)[0]
        t = time.time()
        t = str(int(round(t * 1000)))

        self.session.get("https://wenku.baidu.com/orgvip/interface/caniuse?doc_id=" + docId + "&dowmloadTime=" + t + "&_=" + t)

        r = self.session.get("https://wenku.baidu.com/browse/downloadrec?doc_id=" + docId + "&")

        payload = {'ct': ct, 'doc_id': docId, 'retType': 'newResponse', \
                    'sns_type': '', 'storage': '1', 'useTicket': '1', \
                    'target_uticket_num': '0', 'downloadToken': downloadToken, \
                    'sz': sz, 'v_code': '0', 'v_input': '0', 'req_vip_free_doc': '0'}

        with self.session.post("https://wenku.baidu.com/orgvip/submit/download", data = payload, stream=True, allow_redirects=True) as r:
            suffix = re.compile(r'filename="(.*?)\.(.*?)"').findall(r.headers.get('Content-Disposition'))[0][1]
            file_name = t + utils.random_string() + '.' + suffix
            file_path = 'cache/files/' + file_name
            open(file_path, 'wb').write(r.content)
            return (file_path, file_name)

        return (None, None)
