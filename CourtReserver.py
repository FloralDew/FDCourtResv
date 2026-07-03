# 2026.2.14 started By FloralDew
from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
# 显式等待
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as ex
# 时间相关
from datetime import datetime
import time
# 正则表达式
import re
# 盯场的退出
import threading

time_stamp = lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3] # 时间格式化输出

class WebController():

    def wait_send_keys(self, mark: webdriver.remote.webelement.WebElement | tuple[str, str], 
                         text, timeout=15, poll_freq=0.1, clear=False): # 等待输入框并输入内容. 私有方法
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_freq,
            ignored_exceptions=[ex.StaleElementReferenceException]
        )
        def send(driver): # 由until传入
            if isinstance(mark, webdriver.remote.webelement.WebElement): # 无作用域
                element = mark
            else:
                element = driver.find_element(*mark) # 解包
            if clear:
                element.clear()
            if element.is_displayed() and element.is_enabled():
                element.send_keys(text)
                return True
            return False
        wait.until(send) # 这样才能真正避免StaleElementReferenceException

    # 等待并点击元素(自动处理遮挡/刷新)
    def wait_click(self, mark: webdriver.remote.webelement.WebElement | tuple[str, str], 
                     timeout=15, poll_freq=0.1):
        # 输入webElement时, 警惕Stale造成的TimeOut错误
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_freq,
            ignored_exceptions=[
                ex.StaleElementReferenceException,
                ex.ElementClickInterceptedException,
            ]
        )

        def click(driver):
            if isinstance(mark, webdriver.remote.webelement.WebElement):
                element = mark
            else:
                element = driver.find_element(*mark) # 解包
            if element.is_displayed() and element.is_enabled():
                element.click()
                return True
            return False
        
        wait.until(click)

class CourtReserver(WebController): # 封装成类, 便于管理和维护

    def wait_calendar_refresh(self, timeout=10, poll_freq=0.1, xtra_wait=0.1): # 等待日历刷新完毕
        time.sleep(xtra_wait / 2) # 以时间换准确率. 详见README.
        WebDriverWait(self.driver, timeout, poll_freq).until( # 等待日历刷新完毕
            EC.none_of( # 条件取反. 不能用not
                EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                    (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                    'class', 
                    'loading-parent-box'
                )
            )
        )
        time.sleep(xtra_wait / 2) # 以时间换准确率. 详见README.

    def __init__(self, thread_num: int, username: str, password: str, tel: str, court_date: str, court_time: str, campus = 'Fenglin'):
        self.thread_num = thread_num
        self.court_date = court_date
        self.court_time = court_time
        self.calendar_text = ''
        self.court_element = None
        self.book_btn = None

        print(f"[{time_stamp()}](线程{thread_num}) 开始启动浏览器.")
        # 创建并启动浏览器
        browser_options = uc.ChromeOptions()
        driver = uc.Chrome(options=browser_options)
        driver.implicitly_wait(10)
        driver.maximize_window()
        self.driver = driver

        # 直接打开枫林学生活动中心-羽毛球的预约网站
        match campus:
            case 'Fenglin': court_id = 1169
            case 'Handan_Zhengda': court_id = 951
            case 'Handan_Beiqu': court_id = 938
            case _: raise ValueError(f'No such court named {campus}.')

        bflag = False
        while not bflag:
            try:
                driver.get(f"https://booking.fudan.edu.cn/reservation/fe/site/reservationInfo?id={court_id}")
                # 由于不存在cookies, 会跳转到登陆界面. 使用显式等待以解决StaleElementReferenceException
                self.wait_send_keys((By.ID, "login-username"), username)
                self.wait_send_keys((By.ID, "login-password"), password)
                bflag = True
            except Exception as e: # 有时候网页未能正常打开
                print(f"[{time_stamp()}](线程{thread_num}) 浏览器启动遇到问题. {str(e)[:20000]}..., 正在刷新...")
                driver.refresh()
        
        # 点击"登录"按钮
        self.wait_click((By.XPATH, '//*[@id="content_login"]/div[2]/div[2]/button'))

        # 此时可能弹出确认框, 但这不是alert框. 如有, 点击确认
        try:
            print(f"[{time_stamp()}](线程{thread_num}) 判断是否弹出了对话框...")
            # 第一个div到底是4还是5? 在寝室电脑上是4.
            # 7/3/2026更新: 又变成了5
            confirm_btn = driver.find_element(By.XPATH, '/html/body/div[5]/div/div/div[1]/div/div[3]/div[2]/div[2]/div[2]/button')
            print(f"[{time_stamp()}](线程{thread_num}) 弹出了对话框. 点击确认.")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", confirm_btn) # 防止ElementClickInterceptedException
            time.sleep(1) # 增强鲁棒性, 等待可能的滚动动画
            self.wait_click(confirm_btn)
            time.sleep(1) # 等待消失动画
        except Exception as e:
            print(f"[{time_stamp()}](线程{thread_num}) 未弹出对话框. {str(e)[:70]}...")
        finally:
            driver.execute_script("document.body.style.zoom='0.3'") # 防止ElementClickInterceptedException
            self.previous_week_btn = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]')
            self.next_week_btn = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]')
            # 2026.4.8更新 输入手机号. 这里使用clear = True没用
            self.wait_click((By.CLASS_NAME, 'n-base-clear')) # 手动点击清除
            self.wait_send_keys((By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[2]/div/div[2]/form/div/div[1]/div/div[1]/div[1]/input'), tel)
            print(f"[{time_stamp()}](线程{thread_num}) 浏览器启动完毕.")

    def preload_calendar(self):
        print(f"[{time_stamp()}](线程{self.thread_num}) 正在读取和预加载日历...")
        # 先判断今天是否能看到目标日的场次
        calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        if self.court_date not in calendar_text: # 如果不能看到
            # 点击"后一周"
            self.wait_click(self.next_week_btn)
            self.wait_calendar_refresh(xtra_wait=1) # 确保刷新完毕
            calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        else: # 如果能看到. 这里点击前一周再后一周的目的是, 让点击"后一周"的网页被缓存, 避免抢场时真正点击后一周还要重新请求
            self.wait_click(self.previous_week_btn)
            self.wait_click(self.next_week_btn)
        self.calendar_text = calendar_text
        print(f"[{time_stamp()}](线程{self.thread_num}) 读取和预加载完毕.")

    def get_element(self, back_to_previous_week=True):
        print(f"[{time_stamp()}](线程{self.thread_num}) 正在获取目标场次和预约按钮的element...")
        # 使用正则表达式匹配全部时段
        time_list = re.findall(r"\d\d:\d\d-\d\d:\d\d", self.calendar_text)
        # 匹配全部日期
        date_list = re.findall(r"\d\d\d\d-\d\d-\d\d", self.calendar_text)
        # 得到对应场次的XPATH
        target_xpath = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[2]/' + \
                        f'dl[{date_list.index(self.court_date)+2}]/dd[{time_list.index(self.court_time)+1}]'
        
        self.court_element = self.driver.find_element(By.XPATH, target_xpath)
        self.book_btn = self.driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[2]/div/div[2]/div/button')
        print(f"[{time_stamp()}](线程{self.thread_num}) 获取完毕!")

        if back_to_previous_week: # 用于autobook时, 需要退回前一周
            # 点击"前一周", 退回到目标场前一周的状态
            self.wait_click(self.previous_week_btn)

    def auto_book(self, retry_times: int):
        print(f"[{time_stamp()}](线程{self.thread_num}) 调用抢场函数...")
        # 点击"后一周"
        self.wait_click(self.next_week_btn)
        self.wait_calendar_refresh(xtra_wait = 0.05)
        i = 0
        while i < retry_times and '可预约' not in self.court_element.text:
            print(f"[{time_stamp()}](线程{self.thread_num}) 当前场次{self.court_element.text}, 下面进行第{i+1}次刷新尝试.") # 最多刷新retry_times次
            # 点击"前一周"
            self.wait_click(self.previous_week_btn) # 因为有循环, 这里第一次点击也使用了显式等待
            # 点击前一周后, 会出现一个类为pc-loading的元素挡住按钮, 而wait_click中有处理ElementClickInterceptedException的逻辑, 因此不需要等待日历刷新完毕
            # 点击"后一周"
            self.wait_click(self.next_week_btn)
            self.wait_calendar_refresh()
            i += 1

        if '可预约' not in self.court_element.text:
            print(f"[{time_stamp()}](线程{self.thread_num}) {retry_times}次刷新后仍未开放或已约满, 抢场失败.")
            return

        # 点击场次
        self.court_element.click() # 这里为了保证速度没有使用wait_click()
        # 点击"确认预约"
        try:
            for i in range(200):
                self.book_btn.click()
                time.sleep(0.05)
            else:
                print(f"[{time_stamp()}](线程{self.thread_num}) 10s内200次点击未返回, 可能抢场失败.")
        except Exception as e: # 一般是stale element reference, 因为抢场成功会跳转页面
            print(f"[{time_stamp()}](线程{self.thread_num}) 点击抢场成功! {str(e)[:70]}...")

    def watch_court(self, stop_event: threading.Event, poll_freq=10):
        print(f'[{time_stamp()}] 开始盯场...')
        while '可预约' not in self.court_element.text:
            self.wait_click(self.previous_week_btn)
            time.sleep(poll_freq)
            if stop_event.is_set():
                return
            self.wait_click(self.next_week_btn)
            self.wait_calendar_refresh()
        self.wait_click(self.court_element)
        self.wait_click(self.book_btn)
        print(f"[{time_stamp()}] 抓场成功!")
