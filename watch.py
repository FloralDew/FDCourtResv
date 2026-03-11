# 2026.3.9 started By FloralDew
from CourtReserver import *
import json
import threading

def watching_thread(thread_num: int, court_date: str, court_time: str, stop_event: threading.Event):
    with open("UIS.json", 'r') as f: # UIS账号和密码
        uis_list = json.load(f)
    d = uis_list[thread_num % len(uis_list)]

    courtReserver = CourtReserver(
        thread_num=thread_num,
        username=d["username"],
        password=d["password"],
        court_date=court_date,
        court_time=court_time
    )

    courtReserver.preload_calendar()
    courtReserver.get_element(back_to_previous_week=False)
    courtReserver.watch_court(stop_event=stop_event)

if __name__ == "__main__":
    court_dates = ['2026-03-13', '2026-03-13']
    court_times = ['20:00-21:00', '19:00-20:00'] # 必须一一对应.
    stop_event = threading.Event()
    # 依次启动多个浏览器
    threads = []
    for i in range(len(court_dates)):
        t = threading.Thread(target=watching_thread, args=(i, court_dates[i], court_times[i], stop_event))
        print(f">> 线程{i}负责: {court_dates[i]} {court_times[i]}")
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