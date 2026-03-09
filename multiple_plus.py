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
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException
# 时间相关
from datetime import datetime
import time
# 正则表达式
import re
# 多线程抢场
import threading

class CourtReserver(): # 封装成类, 便于管理和维护
    NEXT_WEEK_XPATH = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]'
    PREVIOUS_WEEK_XPATH = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]'

    def __wait_send_keys(self, locator, text, timeout=10, poll_frequency=0.2, clear=False): # 等待输入框并输入内容. 私有方法
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_frequency,
            ignored_exceptions=[StaleElementReferenceException]
        )
        def send(driver):
            element = driver.find_element(*locator) # 解包
            if clear:
                element.clear()
            element.send_keys(text)
            return True
        wait.until(send) # 这样才能真正避免StaleElementReferenceException

    def __wait_click(self, locator, timeout=10, poll_frequency=0.1): # 等待并点击元素(自动处理遮挡/刷新)
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_frequency,
            ignored_exceptions=[
                StaleElementReferenceException,
                ElementClickInterceptedException,
            ]
        )
        def click(driver):
            element = driver.find_element(*locator)
            element.click()
            return True
        wait.until(click)

    def __init__(self, thread_num: int, username: str, password: str, court_date: str, court_time: str, campus = 'Fenglin'):
        self.thread_num = thread_num
        self.court_date = court_date
        self.court_time = court_time
        self.campus = campus

        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{thread_num}) 开始启动浏览器.")
        # 创建并启动浏览器
        browser_option = Options()
        browser_option.add_argument('--no-sandbox')
        browser_option.add_experimental_option('detach', True)
        driver = webdriver.Edge(service=Service(r"./MsEdgeDriver/msedgedriver.exe"), options=browser_option)
        driver.implicitly_wait(8)
        driver.maximize_window() # 防止ElementClickInterceptedException
        self.driver = driver

        # 直接打开枫林学生活动中心-羽毛球的预约网站
        if campus == 'Fenglin':
            driver.get(r"https://booking.fudan.edu.cn/reservation/fe/site/reservationInfo?id=1169")
        #################### 在此处添加其他校区场地的网址 #######################

        # 由于不存在cookies, 会跳转到登陆界面. 使用显式等待以解决StaleElementReferenceException
        self.__wait_send_keys((By.ID, "login-username"), username)
        self.__wait_send_keys((By.ID, "login-password"), password)
        
        # 点击"登录"按钮
        self.__wait_click((By.XPATH, '//*[@id="content_login"]/div[2]/div[2]/button'))

        # 此时可能弹出确认框, 但这不是alert框. 如有, 点击确认
        try:
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{thread_num}) 判断是否弹出了对话框...")
            confirm_btn = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[1]/div/div[3]/div[2]/div[2]/div[2]/button') # 第一个div到底是4还是5? 在寝室电脑上是4
            print(f"(线程{thread_num}) 弹出了对话框. 点击确认.")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", confirm_btn) # 防止ElementClickInterceptedException
            WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable(confirm_btn)).click() # 必须这么写, 不能单纯btn.click(), 否则在网络状况不好时点了没用
        except Exception as e:
            print(f"(线程{thread_num}) 未弹出对话框. {str(e)[:70]}...")
        finally:
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{thread_num}) 浏览器启动完毕.")

    def preload_calendar(self):
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 正在读取和预加载日历...")
        # 先判断今天是否能看到目标日的场次
        calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        if self.court_date not in calendar_text: # 如果不能看到
            # 点击"后一周"
            self.__wait_click((By.XPATH, self.NEXT_WEEK_XPATH))
            # 这里等待日历刷新完毕没有使用等待pre-loading-box消失方法, 是为了100%确保获取正确的calendar_text. 一旦获取不到, 后面无法get_court_element
            WebDriverWait(self.driver, 5, 0.1).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "week_calendar"), self.court_date))
            calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        else: # 如果能看到. 这里点击前一周再后一周的目的是, 让点击"后一周"的网页被缓存, 避免抢场时真正点击后一周还要重新请求
            self.__wait_click((By.XPATH, self.PREVIOUS_WEEK_XPATH))
            self.__wait_click((By.XPATH, self.NEXT_WEEK_XPATH))
        self.calendar_text = calendar_text
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 读取和预加载完毕.")

    def get_court_element(self, for_autobook=True):
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 正在获取目标场次element...")
        # 使用正则表达式匹配全部时段
        time_list = re.findall(r"\d\d:\d\d-\d\d:\d\d", self.calendar_text)
        # 匹配全部日期
        date_list = re.findall(r"\d\d\d\d-\d\d-\d\d", self.calendar_text)
        # 得到对应场次的XPATH
        target_xpath = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[2]/' + \
                        f'dl[{date_list.index(self.court_date)+2}]/dd[{time_list.index(self.court_time)+1}]'
        
        element_court = self.driver.find_element(By.XPATH, target_xpath)
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 获取完毕!")
        self.element_court = element_court

        if for_autobook: # 用于autobook时, 需要退回前一周
            # 点击"前一周", 退回到目标场前一周的状态
            self.__wait_click((By.XPATH, self.PREVIOUS_WEEK_XPATH))
            # 等待"后一周"按钮可被点击. 这行纯属增强鲁棒性. 一般情况下很长时间后才会执行auto_book函数.
            WebDriverWait(self.driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH, self.NEXT_WEEK_XPATH)))

    def auto_book(self, retry_times: int):
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 调用抢场函数...")
        # 点击"后一周"
        self.driver.find_element(By.XPATH, self.NEXT_WEEK_XPATH).click()
        # 等待日历刷新完毕
        WebDriverWait(self.driver, 5, 0.1).until(
            EC.none_of( # 条件取反. 不能用not
                EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                    (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                    'class', 
                    'loading-parent-box'
                )
            )
        )
        time.sleep(0.03) # 以时间换准确率. 详见README.
        if '可预约' not in self.element_court.text:
            for i in range(retry_times):
                print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 当前场次未开放或已约满, 下面进行第{i+1}次刷新尝试.") # 最多刷新retry_times次
                # 点击"前一周"
                self.__wait_click((By.XPATH, self.PREVIOUS_WEEK_XPATH)) # 因为有循环, 这里第一次点击也使用了显式等待
                # 等待按钮可被点击后, 点击"后一周"
                self.__wait_click((By.XPATH, self.NEXT_WEEK_XPATH))
                WebDriverWait(self.driver, 5, 0.1).until( # 等待日历刷新完毕
                    EC.none_of( # 条件取反. 不能用not
                        EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                            (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                            'class', 
                            'loading-parent-box'
                        )
                    )
                )
                time.sleep(0.05) # 以时间换准确率. 详见README.
                print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num})", self.element_court.text)
                if '可预约' in self.element_court.text:
                    break
            else:
                print(f"(线程{self.thread_num}) {retry_times}次刷新后仍未开放或已约满, 抢场失败.")
                return

        # 点击场次
        self.element_court.click()
        # 点击"确认预约"
        book_btn = self.driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[2]/div/div[2]/div/button')
        try:
            for i in range(200):
                book_btn.click()
                time.sleep(0.05)
            else:
                print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 10s内200次点击未返回, 可能抢场失败.")
        except Exception as e: # 一般是stale element reference, 因为抢场成功会跳转页面
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}](线程{self.thread_num}) 点击抢场成功! {str(e)[:70]}...")
    
# 主函数. 通过它执行完整的创建浏览器-抢场过程.
def complete_booking_thread(thread_num: int, booking_time: datetime, court_date: str, court_time: str, 
                            stop_event: threading.Event, # 用于在浏览器打开后、抢场开始前KeyboardInterrupt
                            offset = 0 # 每个线程相对前一个线程抢场的偏移秒数. 由于加入了0.05s轮询, 可以为0
                            ):
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
        courtReserver.get_court_element(for_autobook=True)

        # 在精确时间调用抢场函数
        delay = (booking_time - datetime.now()).total_seconds() + thread_num * offset # 后面每个线程依次晚offset抢场, 防止"点击太频繁了"报错
        while delay > 2 and not stop_event.is_set(): # 每2s校准一次
            time.sleep(2)
            delay = (booking_time - datetime.now()).total_seconds() + thread_num * offset
        if not stop_event.is_set():
            time.sleep(max(0, delay))
            courtReserver.auto_book(retry_times=3)

if __name__ == "__main__":
    # 参数设置
    booking_time = datetime(2026, 3, 9, 15, 28)
    court_dates = ['2026-03-12']
    court_times = ['20:00-21:00'] # 必须一一对应.

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
        print(f">> 线程{i}负责: {court_dates[i]} {court_times[i]}")
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