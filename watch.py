# 2026.3.9 started By FloralDew
from CourtReserver import CourtReserver
import json

court_date = '2026-03-12'
court_time = '20:00-21:00'

with open("UIS.json", 'r') as f: # UIS账号和密码
    uis_list = json.load(f)

courtReserver = CourtReserver( # 默认以第一个人的身份登录
    thread_num=0,
    username=uis_list[0]["username"],
    password=uis_list[0]["password"],
    court_date=court_date,
    court_time=court_time
)

courtReserver.preload_calendar()
courtReserver.get_element(back_to_previous_week=False)
courtReserver.watch_court()