# 2026.2.14 started By FloralDew
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
# UIS
import json
# 显式等待
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 时间相关
from datetime import datetime
import time
# 正则表达式
import re
# 多线程抢场
import threading

FOLLOWING_WEEK_XPATH = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]'
PREVIOUS_WEEK_XPATH = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]'

# 启动浏览器, UIS登陆, 打开预约网站
def init(num: int, username: str, password: str, campus = 'Fenglin'):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 开始启动浏览器.")
    # 创建并启动浏览器
    browser_option = Options()
    browser_option.add_argument('--no-sandbox')
    browser_option.add_experimental_option('detach', True)
    driver = webdriver.Edge(service=Service(r"./MsEdgeDriver/msedgedriver.exe"), options=browser_option)
    driver.implicitly_wait(8)
    driver.maximize_window()

    # 直接打开枫林学生活动中心-羽毛球的预约网站
    if campus == 'Fenglin':
        driver.get(r"https://booking.fudan.edu.cn/reservation/fe/site/reservationInfo?id=1169")
    #################### 在此处添加其他校区场地的网址 #######################

    # 由于不存在cookies, 会跳转到登陆界面. 这个时间不好把握, 因此必须使用try
    try:
        driver.find_element(By.ID, "login-username") # 这个会变成stale
    finally:
        driver.find_element(By.ID, "login-username").send_keys(username)
        driver.find_element(By.ID, "login-password").send_keys(password)
    # 点击"登录"按钮
    driver.find_element(By.XPATH, '//*[@id="content_login"]/div[2]/div[2]/button').click()

    # 此时可能弹出确认框, 但这不是alert框. 如有, 点击确认
    try:
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 判断是否弹出了对话框...")
        confirm_btn = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[1]/div/div[3]/div[2]/div[2]/div[2]/button') # 第一个div到底是4还是5? 在寝室电脑上是4
        print(f"(线程{num}) 弹出了对话框. 点击确认.")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", confirm_btn) # 防止ElementClickInterceptedException
        confirm_btn.click()
    except Exception:
        print(f"(线程{num}) 未弹出对话框.")
    finally:
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 浏览器启动完毕.")
        return driver

# 获取目标场次element
def get_court_element(num: int, driver: webdriver.Edge, calendar_text: str, court_date: str, court_time: str):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 正在获取目标场次element...")
    # 使用正则表达式匹配全部时段
    time_list = re.findall(r"\d\d:\d\d-\d\d:\d\d", calendar_text)
    # 匹配全部日期
    date_list = re.findall(r"\d\d\d\d-\d\d-\d\d", calendar_text)
    # 得到对应场次的XPATH
    target_xpath = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[2]/' + \
                    f'dl[{date_list.index(court_date)+2}]/dd[{time_list.index(court_time)+1}]'
    
    element_court = driver.find_element(By.XPATH, target_xpath)
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 获取完毕!")
    return element_court

# 抢场. 注意默认为点击"后一周"再抢场.
def auto_book(num: int, driver: webdriver.Edge, element_court, retry_times: int):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 调用抢场函数...")
    # 点击"后一周"
    driver.find_element(By.XPATH, FOLLOWING_WEEK_XPATH).click()
    # 等待日历刷新完毕
    WebDriverWait(driver, 5, 0.1).until(
        EC.none_of( # 条件取反. 不能用not
            EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                'class', 
                'loading-parent-box'
            )
        )
    )
    if '可预约' not in element_court.text:
        for i in range(retry_times):
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 当前场次未开放或已约满, 下面进行第{i+1}次刷新尝试.") # 最多刷新三次
            # 点击"前一周"
            driver.find_element(By.XPATH, PREVIOUS_WEEK_XPATH).click()
            # 等待按钮可被点击后, 点击"后一周"
            WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH, FOLLOWING_WEEK_XPATH))).click()
            WebDriverWait(driver, 5, 0.1).until( # 等待日历刷新完毕
                EC.none_of( # 条件取反. 不能用not
                    EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                        (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                        'class', 
                        'loading-parent-box'
                    )
                )
            )
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num})", element_court.text)
            if '可预约' in element_court.text:
                break
        else:
            print(f"(线程{num}) {retry_times}次刷新后仍未开放或已约满, 抢场失败.")
            return

    # 点击场次
    element_court.click()
    # 点击"确认预约"
    book_btn = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[2]/div/div[2]/div/button')
    try:
        for i in range(200):
            book_btn.click()
            time.sleep(0.05)
        else:
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 10s内200次点击未返回, 可能抢场失败.")
    except Exception as e: # 一般是stale element reference, 因为抢场成功会跳转页面
        # print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) {str(e)[:70]}...") 
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{num}) 点击抢场成功!")

# 主函数. 通过它执行完整的创建浏览器-抢场过程.
def complete_booking_thread(num: int, booking_time: datetime, court_date: str, court_time: str, 
                            stop_event: threading.Event, # 用于在浏览器打开后、抢场开始前KeyboardInterrupt
                            offset = 0 # 每个线程相对前一个线程抢场的偏移秒数. 由于加入了0.05s轮询, 可以为0
                            ):
        with open("UIS.json", 'r') as f: # UIS账号和密码
            d = json.load(f)

        driver = init(num, username=d["username"], password=d["password"]) # 启动浏览器, UIS登陆, 打开预约网站

        # 先判断今天是否能看到目标日的场次
        calendar_text = driver.find_element(By.CLASS_NAME, "week_calendar").text
        if court_date not in calendar_text: # 如果不能看到
            # 点击"后一周"
            driver.find_element(By.XPATH, FOLLOWING_WEEK_XPATH).click()
            WebDriverWait(driver, 5, 0.1).until( # 等待日历刷新完毕
                EC.none_of( # 条件取反. 不能用not
                    EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                        (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                        'class', 
                        'loading-parent-box'
                    )
                )
            )
            calendar_text = driver.find_element(By.CLASS_NAME, "week_calendar").text
        else: # 如果能看到. 这里点击前一周再后一周的目的是, 让点击"后一周"的网页被缓存, 避免抢场时真正点击后一周还要重新请求
            driver.find_element(By.XPATH, PREVIOUS_WEEK_XPATH).click()
            WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH, FOLLOWING_WEEK_XPATH))).click()

        # 获取对应场次的element
        element_court = get_court_element(num, driver, calendar_text, court_date, court_time)
        # 点击"前一周", 退回到目标场前一周的状态
        driver.find_element(By.XPATH, PREVIOUS_WEEK_XPATH).click()
        # 等待"后一周"按钮可被点击. 这行纯属增强鲁棒性. 一般情况下很长时间后才会执行auto_book函数.
        WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH, FOLLOWING_WEEK_XPATH)))

        # 在精确时间调用抢场函数
        delay = (booking_time - datetime.now()).total_seconds() + num * offset # 后面每个线程依次晚offset抢场, 防止"点击太频繁了"报错
        while delay > 2 and not stop_event.is_set(): # 每2s校准一次
            time.sleep(2)
            delay = (booking_time - datetime.now()).total_seconds() + num * offset
        if not stop_event.is_set():
            time.sleep(max(0, delay))
            auto_book(num, driver, element_court, retry_times=3)

if __name__ == "__main__":
    # 参数设置
    booking_time = datetime(2026, 3, 6, 7, 0)
    court_dates = ['2026-03-08', '2026-03-09']
    court_times = ['19:00-20:00', '20:00-21:00'] # 必须一一对应.

    # 提前三分钟启动浏览器.
    SECONDS_BEFORE = 180
    delay = (booking_time - datetime.now()).total_seconds() - SECONDS_BEFORE
    while delay > 1800: # 每30min校准一次
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 预计等待{delay}s后启动浏览器.")
        time.sleep(1800)
        delay = (booking_time - datetime.now()).total_seconds() - SECONDS_BEFORE
    time.sleep(max(0, delay))

    stop_event = threading.Event()
    # 依次启动多个浏览器
    threads = []
    for i in range(len(court_dates)):
        t = threading.Thread(target=complete_booking_thread, args=(i, booking_time, court_dates[i], court_times[i], stop_event))
        print(f"**线程{i}负责: {court_dates[i]} {court_times[i]}**")
        t.start()
        threads.append(t)

    try:
        while threading.active_count() > 1: # 除主线程外还有别的线程在运行.
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        print(f'[{datetime.now().strftime("%H:%M:%S.%f")}] 强制退出...')

    # 等待所有线程结束
    for t in threads:
        t.join()

    print(f'[{datetime.now().strftime("%H:%M:%S.%f")}] 所有线程均已结束.')