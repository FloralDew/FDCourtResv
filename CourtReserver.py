# 2026.2.14 started By FloralDew
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
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

time_stamp = lambda: datetime.now().strftime("%H:%M:%S.%f") # 时间格式化输出

class CourtReserver(): # 封装成类, 便于管理和维护

    def __wait_send_keys(self, mark: webdriver.remote.webelement.WebElement | tuple[str, str], 
                         text, timeout=10, poll_freq=0.2, clear=False): # 等待输入框并输入内容. 私有方法
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_freq,
            ignored_exceptions=[StaleElementReferenceException]
        )
        def send(driver): # 由until传入
            if isinstance(mark, webdriver.remote.webelement.WebElement):
                element = mark
            else:
                element = driver.find_element(*mark) # 解包
            if clear:
                element.clear()
            element.send_keys(text)
            return True
        wait.until(send) # 这样才能真正避免StaleElementReferenceException

    def __wait_click(self, mark: webdriver.remote.webelement.WebElement | tuple[str, str], 
                     timeout=10, poll_freq=0.1): # 等待并点击元素(自动处理遮挡/刷新)
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_freq,
            ignored_exceptions=[
                StaleElementReferenceException,
                ElementClickInterceptedException,
            ]
        )
    
        def click(driver):
            if isinstance(mark, webdriver.remote.webelement.WebElement):
                element = mark
            else:
                element = driver.find_element(*mark) # 解包
            element.click()
            return True
        wait.until(click)

    def __wait_calendar_refresh(self, xtra_wait=0.05): # 等待日历刷新完毕
        WebDriverWait(self.driver, 5, 0.1).until( # 等待日历刷新完毕
            EC.none_of( # 条件取反. 不能用not
                EC.text_to_be_present_in_element_attribute( # 日历类中包含loading-parent-box. 注意这个日历不是week_calendar, 是它的上级
                    (By.XPATH, '/html/body/div[1]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]'), 
                    'class', 
                    'loading-parent-box'
                )
            )
        )
        time.sleep(xtra_wait) # 以时间换准确率. 详见README.

    def __init__(self, thread_num: int, username: str, password: str, court_date: str, court_time: str, campus = 'Fenglin'):
        self.thread_num = thread_num
        self.court_date = court_date
        self.court_time = court_time
        self.campus = campus
        self.calendar_text = ''
        self.court_element = None
        self.book_btn = None

        print(f"[{time_stamp()}](线程{thread_num}) 开始启动浏览器.")
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
            print(f"[{time_stamp()}](线程{thread_num}) 判断是否弹出了对话框...")
            # 第一个div到底是4还是5? 在寝室电脑上是4
            confirm_btn = driver.find_element(By.XPATH, '/html/body/div[4]/div/div/div[1]/div/div[3]/div[2]/div[2]/div[2]/button')
            print(f"[{time_stamp()}](线程{thread_num}) 弹出了对话框. 点击确认.")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", confirm_btn) # 防止ElementClickInterceptedException
            self.__wait_click(confirm_btn) # 不能单纯btn.click(), 否则在网络状况不好时点了没用
        except Exception as e:
            print(f"[{time_stamp()}](线程{thread_num}) 未弹出对话框. {str(e)[:70]}...")
        finally:
            self.previous_week_btn = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]')
            self.next_week_btn = driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]')
            print(f"[{time_stamp()}](线程{thread_num}) 浏览器启动完毕.")

    def preload_calendar(self):
        print(f"[{time_stamp()}](线程{self.thread_num}) 正在读取和预加载日历...")
        # 先判断今天是否能看到目标日的场次
        calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        if self.court_date not in calendar_text: # 如果不能看到
            # 点击"后一周"
            self.__wait_click(self.next_week_btn)
            # 这里等待日历刷新完毕没有使用等待pre-loading-box消失方法, 是为了100%确保获取正确的calendar_text. 一旦获取不到, 后面无法get_element
            WebDriverWait(self.driver, 5, 0.1).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "week_calendar"), self.court_date))
            calendar_text = self.driver.find_element(By.CLASS_NAME, "week_calendar").text
        else: # 如果能看到. 这里点击前一周再后一周的目的是, 让点击"后一周"的网页被缓存, 避免抢场时真正点击后一周还要重新请求
            self.__wait_click(self.previous_week_btn)
            self.__wait_click(self.next_week_btn)
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
            self.__wait_click(self.previous_week_btn)

    def auto_book(self, retry_times: int):
        print(f"[{time_stamp()}](线程{self.thread_num}) 调用抢场函数...")
        # 点击"后一周"
        self.__wait_click(self.next_week_btn)
        self.__wait_calendar_refresh(0.03)
        i = 0
        while i < retry_times and '可预约' not in self.court_element.text:
            print(f"[{time_stamp()}](线程{self.thread_num}) 当前场次{self.court_element.text}, 下面进行第{i+1}次刷新尝试.") # 最多刷新retry_times次
            # 点击"前一周"
            self.__wait_click(self.previous_week_btn) # 因为有循环, 这里第一次点击也使用了显式等待
            # 等待按钮可被点击后, 点击"后一周"
            self.__wait_click(self.next_week_btn)
            self.__wait_calendar_refresh()
            i += 1

        if '可预约' not in self.court_element.text:
            print(f"[{time_stamp()}](线程{self.thread_num}) {retry_times}次刷新后仍未开放或已约满, 抢场失败.")
            return

        # 点击场次
        self.court_element.click() # 这里为了保证速度没有使用__wait_click()
        # 点击"确认预约"
        try:
            for i in range(200):
                self.book_btn.click()
                time.sleep(0.05)
            else:
                print(f"[{time_stamp()}](线程{self.thread_num}) 10s内200次点击未返回, 可能抢场失败.")
        except Exception as e: # 一般是stale element reference, 因为抢场成功会跳转页面
            print(f"[{time_stamp()}](线程{self.thread_num}) 点击抢场成功! {str(e)[:70]}...")

    def watch_court(self, poll_freq=10):
        while '可预约' not in self.court_element.text:
            self.__wait_click(self.previous_week_btn)
            time.sleep(poll_freq)
            self.__wait_click(self.next_week_btn)
            self.__wait_calendar_refresh()
        self.__wait_click(self.court_element)
        print(f"[{time_stamp()}] 抓场成功!")
