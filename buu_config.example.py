# -*- coding: utf-8 -*

from dateutil.relativedelta import relativedelta
from datetime import date

class config(object):
    admin_id = 1

    redis_addr = 'localhost'
    redir_port = 7001
    redis_password = ''
    redis_db = 0

    mysql_addr = 'localhost'
    mysql_port = 3306
    mysql_username = ''
    mysql_password = ''
    mysql_database = ''

    version = '20180626'

    need_vpn = True

    mybuu_username = ''
    mybuu_password = ''

    jwxt_first_week_monday = date(2019, 9, 2)

    jwxt_dict_week = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6}
    jwxt_dict_day = {
                    1: relativedelta(hours = 8, minutes = 00), 2: relativedelta(hours = 8, minutes = 50),
                    3: relativedelta(hours = 9, minutes = 55), 4: relativedelta(hours = 10, minutes = 45),
                    5: relativedelta(hours = 11, minutes = 35), 6: relativedelta(hours = 13, minutes = 00),
                    7: relativedelta(hours = 13, minutes = 50), 8: relativedelta(hours = 14, minutes = 50),
                    9: relativedelta(hours = 15, minutes = 40), 10: relativedelta(hours = 16, minutes = 40),
                    11: relativedelta(hours = 17, minutes = 30), 12: relativedelta(hours = 18, minutes = 20),
                    13: relativedelta(hours = 19, minutes = 10)
                }

    aes_key = ''

    tuling_key = ''
    bot_nickname = '@联大小助'

    request_proxies = {
        'http': 'socks5://buu:@192.168.1.1:6491/',
        'https': 'socks5://buu:@192.168.1.1:6491/'
    }

    fail_clean = ['current_printer_id', 'operating', 'inputing', 'current_print_file_name', 'current_print_file_page_count' \
                    'current_print_file_print_price', 'current_print_create_time', 'current_page', 'total_page', 'word', 'operating']
    print_price = 0.2

    smtp_server = 'smtp.mxhichina.com'
    smtp_username = 'printer@zhaoj.in'
    smtp_sender = 'printer@zhaoj.in'
    smtp_password = ''

    weixin_token = ''
    weixin_appid = ''
    weixin_appsecret = ''
    weixin_encoding_aeskey = ''

    cos_app_id = '1251267611'
    cos_app_secret_id = ''
    cos_app_secret_key = ''
    cos_bucket_name = 'buurobot'
    cos_region = 'bj'
    cos_url = 'https://buurobot-1251267611.cos.ap-beijing.myqcloud.com/'

    wechat_menu = {'button':[
        {
            'name': '关于小助',
            'sub_button': [
                {
                    'type': 'view',
                    'name': '意见反馈',
                    'url':  'https://jinshuju.net/f/w6qTir',
                },
                {
                    'type': 'media_id',
                    'name': '本号二维码',
                    'media_id': 'vAY3Fs9fVWi_MsFR8q0p-ovbjdtIDDNDKf_VTvcga1g',
                },
            ],
        },
        {
            'type': 'view',
            'name': '财管学堂',
            'url':  'https://gyxt.wetolink.com/ssa/weixin/login',
        }
    ]}

    vpn_proxies = {
        'http': 'socks5://buu:@192.168.122.1:6491/',
        'https': 'socks5://buu:@192.168.122.1:6491/'
    }

    verbose = True
