# 2026.3.9 started By FloralDew
from CourtReserver import CourtReserver, time_stamp
import json
import threading
import time

def watching_thread(thread_num: int, campus: str, court_date: str, court_time: str, stop_event: threading.Event):
    with open("config.json", 'r') as f: # UIS账号和密码
        d = json.load(f)
    uis_lst = d["UIS"]
    uis = uis_lst[thread_num % len(uis_lst)]

    courtReserver = CourtReserver(
        thread_num=thread_num,
        username=uis["username"],
        password=uis["password"],
        tel=uis["tel"],
        court_date=court_date,
        court_time=court_time,
        campus=campus
    )

    courtReserver.preload_calendar()
    courtReserver.get_element(back_to_previous_week=False)
    courtReserver.watch_court(stop_event=stop_event)

if __name__ == "__main__":
    # 参数设置
    with open('config.json', 'r') as f:
        d = json.load(f)
    courts_lst = d["courts"]
    stop_event = threading.Event()
    # 依次启动多个浏览器
    threads = []
    for i in range(len(courts_lst)):
        t = threading.Thread(target=watching_thread, args=(
            i, courts_lst[i]["campus"], courts_lst[i]["date"], courts_lst[i]["time"], stop_event))
        print(f">> 线程{i}负责: {courts_lst[i]["campus"]} {courts_lst[i]["date"]} {courts_lst[i]["time"]}")
        t.start()
        threads.append(t)

    try:
        while threading.active_count() > 1: # 除主线程外还有别的线程在运行.
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        print(f'[{time_stamp()}] 强制退出...')

    # 等待所有线程结束
    for t in threads:
        t.join()

    print(f'[{time_stamp()}] 所有线程均已结束.')