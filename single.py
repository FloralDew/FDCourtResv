# 2026.2.14 started By floralDew
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
# 显式等待
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# 时间相关
from datetime import datetime
import time
import sched
# 正则表达式
import re

# 启动浏览器, UIS登陆, 打开预约网站
def init(username = "your_student_ID", password = "your_UIS_password", campus = 'Fenglin'):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 开始启动浏览器.")
    # 创建并启动浏览器
    browser_option = Options()
    browser_option.add_argument('--no-sandbox')
    browser_option.add_experimental_option('detach', True)
    driver = webdriver.Edge(service=Service(r"./MsEdgeDriver/msedgedriver.exe"), options=browser_option)
    driver.implicitly_wait(8)
    driver.maximize_window()

    # 直接打开枫林学生活动中心-羽毛球的预约网站
    driver.get(r"https://booking.fudan.edu.cn/reservation/fe/site/reservationInfo?id=1169")
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
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 判断是否弹出了对话框...")
        driver.find_element(By.XPATH, '/html/body/div[5]/div/div/div[1]/div/div[3]/div[2]/div[2]/div[2]/button').click()
    finally:
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 判断完毕.")
        return driver

# 获取目标场次element
def get_court_element(driver: webdriver.Edge, calendar_text: str, court_date: str, court_time: str):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 正在获取目标场次element...")
    # 使用正则表达式匹配全部时段
    time_list = re.findall(r"\d\d:\d\d-\d\d:\d\d", calendar_text)
    # 匹配全部日期
    date_list = re.findall(r"\d\d\d\d-\d\d-\d\d", calendar_text)
    # 得到对应场次的XPATH
    target_xpath = '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[2]/' + \
                    f'dl[{date_list.index(court_date)+2}]/dd[{time_list.index(court_time)+1}]'
    
    element_court = driver.find_element(By.XPATH, target_xpath)
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 获取完毕!")
    return element_court

# 抢场. 注意默认为点击"后一周"再抢场.
def auto_book(driver: webdriver.Edge, element_court, retry_times: int):
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 调用抢场函数...")
    # 点击"后一周"
    driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]').click()
    # 等待目标日在日历中出现
    WebDriverWait(driver, 5, 0.1).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "week_calendar"), court_date))
        
    if '可预约' not in element_court.text:
        for i in range(retry_times):
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 当前场次未开放或已约满, 下面进行第{i+1}次刷新尝试.") # 最多刷新三次
            # 点击"前一周"
            driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]').click()
            # 等待按钮可被点击后, 点击"后一周"
            WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH,
                '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]'))).click()
            WebDriverWait(driver, 5, 0.1).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "week_calendar"), court_date)) # 等待目标日出现
            print(f"[{datetime.now().strftime("%H:%M:%S.%f")}]", element_court.text)
            if '可预约' in element_court.text:
                break
        else:
            print(f"{retry_times}次刷新后仍未开放或已约满, 抢场失败.")
            return

    # 点击场次
    element_court.click()
    # 点击"确认预约"
    driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[2]/div/div[2]/div/button').click()
    print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 抢场成功!")

if __name__ == "__main__":
    # 参数设置
    booking_time = datetime(2026, 2, 16, 15, 8)
    court_date = '2026-02-16'
    court_time = '08:00-09:00'

    # 提前五分钟启动浏览器. 这个时间不用很精确, 因此没有使用调度器.
    delay = (booking_time - datetime.now()).total_seconds() - 300
    while(delay > 900): # 每15min校准一次
        print(f"[{datetime.now().strftime("%H:%M:%S.%f")}] 预计等待{delay}s后启动浏览器.")
        time.sleep(900)
        delay = (booking_time - datetime.now()).total_seconds() - 300
    time.sleep(max(0, delay))

    driver = init() # 启动浏览器, UIS登陆, 打开预约网站

    # 先判断今天是否能看到目标日的场次
    calendar_text = driver.find_element(By.CLASS_NAME, "week_calendar").text
    if court_date not in calendar_text: # 如果不能看到
        # 点击"后一周"
        driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]').click()
        # 等待目标日在日历中出现
        WebDriverWait(driver, 5, 0.2).until(EC.text_to_be_present_in_element((By.CLASS_NAME, "week_calendar"), court_date))
        calendar_text = driver.find_element(By.CLASS_NAME, "week_calendar").text
    # 获取对应场次的element
    element_court = get_court_element(driver, calendar_text, court_date, court_time)
    # 点击"前一周"
    driver.find_element(By.XPATH, '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[2]').click()
    # 等待"后一周"按钮可被点击后. 这行纯属增强鲁棒性. 一般情况下很长时间后才会执行auto_book函数.
    WebDriverWait(driver, 5, 0.2).until(EC.element_to_be_clickable((By.XPATH,
        '//*[@id="__nuxt"]/div/div[3]/div[2]/div/div[1]/div/div[1]/div[2]/div[2]/div[1]/div/div[1]/div[4]')))

    # 使用调度器以在精确时间调用抢场函数
    scheduler = sched.scheduler(time.time, time.sleep)
    delay = (booking_time - datetime.now()).total_seconds()
    scheduler.enter(delay, 1, auto_book, argument=(driver, element_court, 3)) # delay可以为负. 此时默认为0
    scheduler.run() # 阻塞