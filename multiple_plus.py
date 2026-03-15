# 主抢场类
from CourtReserver import CourtReserver, time_stamp
# 多线程抢场
import threading
# 时间相关
from datetime import datetime
import time
# UIS
import json
    
# 主函数. 通过它执行完整的创建浏览器-抢场过程.
def booking_thread(thread_num: int, booking_time: datetime, campus: str, court_date: str, court_time: str, 
                            stop_event: threading.Event, # 用于在浏览器打开后、抢场开始前KeyboardInterrupt
                            offset = 0 # 每个线程相对前一个线程抢场的偏移秒数. 由于加入了0.05s轮询, 可以为0
                            ):
    with open("config.json", 'r') as f: # UIS账号和密码
        d = json.load(f)
    uis_lst = d["UIS"]
    uis = uis_lst[thread_num % len(uis_lst)]

    courtReserver = CourtReserver(
        thread_num=thread_num,
        username=uis["username"],
        password=uis["password"],
        court_date=court_date,
        court_time=court_time,
        campus=campus
    )
    
    courtReserver.preload_calendar()
    courtReserver.get_element(back_to_previous_week=True)

    # 在精确时间调用抢场函数
    delay = (booking_time - datetime.now()).total_seconds() + thread_num * offset # 后面每个线程依次晚offset抢场, 防止"点击太频繁了"报错
    while delay > 2 and not stop_event.is_set(): # 每2s校准一次
        time.sleep(2)
        delay = (booking_time - datetime.now()).total_seconds() + thread_num * offset
    if not stop_event.is_set():
        time.sleep(max(0, delay))
        courtReserver.auto_book(retry_times=5)

if __name__ == "__main__":
    # 参数设置
    with open('config.json', 'r') as f:
        d = json.load(f)
    booking_time = datetime.strptime(d["booking_time"], r"%Y-%m-%d %H:%M:%S")
    courts_lst = d["courts"]

    # 提前三分钟启动浏览器.
    SECONDS_BEFORE = 180
    delay = (booking_time - datetime.now()).total_seconds() - SECONDS_BEFORE
    while delay > 1800: # 每30min校准一次
        print(f"[{time_stamp()}] 预计等待{delay}s后启动浏览器.")
        time.sleep(1800)
        delay = (booking_time - datetime.now()).total_seconds() - SECONDS_BEFORE
    time.sleep(max(0, delay))

    stop_event = threading.Event()
    # 依次启动多个浏览器
    threads = []
    for i in range(len(courts_lst)):
        t = threading.Thread(target=booking_thread, args=(
            i, booking_time, courts_lst[i]["campus"], courts_lst[i]["date"], courts_lst[i]["time"], stop_event))
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