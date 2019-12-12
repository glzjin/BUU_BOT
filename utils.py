from qcloud_cos_py3.cos import CosBucket
import buu_config
import asyncio
import re

def upload_file(file_path, file_show_name):
    config = buu_config.config
    bucket = CosBucket(config.cos_app_id, config.cos_app_secret_id, \
                        config.cos_app_secret_key, config.cos_bucket_name, config.cos_region)

    f = open(file_path, "rb")
    bucket.upload_file(f, file_show_name)
    return config.cos_url + file_show_name

import random, string

def random_string(size = 6, chars = string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# -*- coding: utf-8 -*
def load_stat():
    loadavg = {}
    f = open("/proc/loadavg")
    con = f.read().split()
    f.close()
    loadavg['lavg_1']=con[0]
    loadavg['lavg_5']=con[1]
    loadavg['lavg_15']=con[2]
    loadavg['nr']=con[3]
    loadavg['last_pid']=con[4]
    return loadavg

def uptime_stat():
    uptime = {}
    f = open("/proc/uptime")
    con = f.read().split()
    f.close()
    all_sec = float(con[0])
    MINUTE,HOUR,DAY = 60,3600,86400
    uptime['day'] = int(all_sec / DAY )
    uptime['hour'] = int((all_sec % DAY) / HOUR)
    uptime['minute'] = int((all_sec % HOUR) / MINUTE)
    uptime['second'] = int(all_sec % MINUTE)
    uptime['Free rate'] = float(con[1]) / float(con[0])
    return uptime

def memory_stat():
    mem = {}
    f = open("/proc/meminfo")
    lines = f.readlines()
    f.close()
    for line in lines:
        if len(line) < 2: continue
        name = line.split(':')[0]
        var = line.split(':')[1].split()[0]
        mem[name] = round(float(var) / 1024.0, 2)
    mem['MemUsed'] = mem['MemTotal'] - mem['MemFree'] - mem['Buffers'] - mem['Cached']
    return mem

def is_ip(address):
    import socket
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            if not isinstance(address, str):
                address = address.decode('utf8')
            inet_pton(family, address)
            return family
        except (TypeError, ValueError, OSError, IOError):
            pass
    return False

def inet_pton(family, addr):
    import socket
    addr = to_str(addr)
    if family == socket.AF_INET:
        return socket.inet_aton(addr)
    elif family == socket.AF_INET6:
        if '.' in addr:  # a v4 addr
            v4addr = addr[addr.rindex(':') + 1:]
            v4addr = socket.inet_aton(v4addr)
            v4addr = ['%02X' % ord(x) for x in v4addr]
            v4addr.insert(2, ':')
            newaddr = addr[:addr.rindex(':') + 1] + ''.join(v4addr)
            return inet_pton(family, newaddr)
        dbyts = [0] * 8  # 8 groups
        grps = addr.split(':')
        for i, v in enumerate(grps):
            if v:
                dbyts[i] = int(v, 16)
            else:
                for j, w in enumerate(grps[::-1]):
                    if w:
                        dbyts[7 - j] = int(w, 16)
                    else:
                        break
                break
        return b''.join((chr(i // 256) + chr(i % 256)) for i in dbyts)
    else:
        raise RuntimeError("What family?")

def to_str(s):
    if bytes != str:
        if isinstance(s, bytes):
            return s.decode('utf-8')
    return s

def lessons_list_to_cal(lessons_list):
    import pytz
    from uuid import uuid1
    from icalendar import Calendar, Event
    from datetime import datetime, date
    from dateutil.relativedelta import relativedelta
    import buu_config

    config = buu_config.config()

    cal = Calendar()
    cal['version'] = '2.0'
    cal['prodid'] = '-//CQUT//Syllabus//CN'
    tz = pytz.timezone('Asia/Shanghai')

    for item in lessons_list:
        event = Event()

        info_day = re.findall(r'周(.*?)第(.*?)节', item['time'], re.M)
        info_day = info_day[0]

        info_week = re.findall(r'第(\d+)-(\d+)周', item['week'], re.M)
        info_week = info_week[0]

        dtstart_date = config.jwxt_first_week_monday + relativedelta(weeks = (int(info_week[0]) - 1)) + relativedelta(days = int(config.jwxt_dict_week[info_day[0]]))
        dtstart_datetime = datetime.combine(dtstart_date, datetime.min.time())

        sections = info_day[1].split(",")
        dtstart = dtstart_datetime + config.jwxt_dict_day[int(sections[0])]
        dtend = dtstart + relativedelta(minutes = 45)

        if len(sections) > 1:
            for i in range(1, len(sections)):
                dtend = dtstart_datetime + config.jwxt_dict_day[int(sections[i])] + relativedelta(minutes = 45)

        event.add('uid', str(uuid1()) + '@CQUT')
        event.add('summary', item['name'] + ' - ' + item['teacher'])
        event.add('dtstamp', datetime.now(tz))
        event.add('dtstart', dtstart.astimezone(tz))
        event.add('dtend', dtend.astimezone(tz))

        if item['week'].find('|') == -1 and item['week'].find('双周') == -1 and item['week'].find('单周') == -1:
            interval = 1
            count = (int(info_week[1]) - int(info_week[0])) + 1
        else:
            interval = 2
            count = (int(info_week[1]) - int(info_week[0])) / 2 + 1

        event.add('rrule',
                  {'freq': 'weekly', 'interval': interval,
                   'count': count})

        event.add('location', item['room'])

        cal.add_component(event)

    return cal

def exams_list_to_cal(exam_list):
    import pytz
    from uuid import uuid1
    from icalendar import Calendar, Event
    from datetime import datetime, date
    from dateutil.relativedelta import relativedelta
    import buu_config

    config = buu_config.config()

    cal = Calendar()
    cal['version'] = '2.0'
    cal['prodid'] = '-//CQUT//Syllabus//CN'
    tz = pytz.timezone('Asia/Shanghai')

    for item in exam_list:
        event = Event()

        #2018年07月09日(10:50-12:20)
        time_list = re.compile(r"(\d*?)年(\d*?)月(\d*?)日\((\d*?):(\d*?)\-(\d*?):(\d*?)\)", flags = re.M).findall(item['datetime'])[0]

        dtstart = datetime(int(time_list[0]), int(time_list[1]), int(time_list[2]), hour = int(time_list[3]), minute = int(time_list[4]), second = 0)
        dtend = datetime(int(time_list[0]), int(time_list[1]), int(time_list[2]), hour = int(time_list[5]), minute = int(time_list[6]), second = 0)

        event.add('uid', str(uuid1()) + '@CQUT')
        event.add('summary', item['exam_name'])
        event.add('dtstamp', datetime.now(tz))
        event.add('dtstart', dtstart.astimezone(tz))
        event.add('dtend', dtend.astimezone(tz))

        event.add('location',  item['room_area'] + ' - ' +item['exam_room'] + ' - 第 ' + item['exam_sit_no'] + '座')

        cal.add_component(event)

    return cal

def randomword(length):
    import random, string
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def doc_get_page_num(file_name, file_ext):
    if file_ext == '.pdf':
        from PyPDF2 import PdfFileReader
        pdf = PdfFileReader(open(file_name,'rb'))
        return (pdf.getNumPages(), file_name)
    elif file_ext in ['.doc', '.docx']:
        import subprocess
        file_prefix = file_name[:-len(file_ext)]
        pdf_filename = file_prefix + '.pdf'
        try:
            subprocess.check_call(['unoconv', '-f', 'pdf', '-o', pdf_filename, '-d', 'document', file_name])
        except subprocess.CalledProcessError as e:
            print('CalledProcessError', e)

        from PyPDF2 import PdfFileReader
        pdf = PdfFileReader(open(pdf_filename,'rb'))
        return (pdf.getNumPages(), pdf_filename)

def init_asyncio():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    return loop

def close_asyncio(loop):
    loop.stop()
    loop.close()

def remove_html_tag(source_text):
    dr = re.compile(r'<[^>]+>', re.S)
    dd = dr.sub('', source_text)
    return dd
