# FDCourtResv

In short, this is a selenium-based python script that helps to reserve sports courts automatically.

## Repo Overview

Files in this repository are listed as follows:

- **[LearnSelenium.ipynb](LearnSelenium.ipynb)**. A brief selenium tutorial. It is basically all you need to understand the code in the script.
- **derpecated/[single.py](single.py)**. The primary version of the script with basic waiting mechanism, designed for single-court reservation only.
- **deprecated/[multiple.py](multiple.py)**. The second version of the booking script, capable of multiple-court reservation.
---
- **[CourtReserver.py](CourtReserver.py)**. The class.
- **[multiple_plus.py](multiple_plus.py)**. A more robust, class-encapsulated version of the booking script (latest).
- **[watch.py](watch.py)**. Adds support for booking the court once available when it is not 7 o'clock.
---
- **readme.md**.

## Environment

- Python 3.13.3
- Selenium 4.40.0
- Microsoft Edge and its Driver 144.0.3719.115

> To maintain stability, it is strongly recommended to disable the Auto-update of Edge. To do it: 
>
> - run services.msc
> - switch the start-type of **edgeupdate** from Auto to disabled
> - switch the start-type of **edgeupdatem** from Manual to disabled

## How to Use the Script
1. Configure your UIS and targeted court(s). Create "config.json" in the working directory and add:
```
{
    "UIS":
    [
        {
            "username": "xxx", 
            "password": "xxx",
            "tel": "xxx"
        },
        {
            "username": "xxx", 
            "password": "xxx",
            "tel": "xxx"
        }
    ],

    "booking_time": "2026-04-08 06:59:57.5",
    
    "retry_times": 10,

    "courts":
    [
        {
            "campus": "Fenglin",
            "date": "2026-04-10",
            "time": "19:00-20:00"
        },
        {
            "campus": "Fenglin",
            "date": "2026-04-10",
            "time": "20:00-21:00"
        }
    ]
}
```
in which "booking_time" denotes the reservation time (decimal **CANNOT** be omitted), usually two days prior to the court date. (However, it is recommended to set an earlier time, like 06:59:57.5, and increase retry_times to contend with network congestion.)

2. Simply run multiple_plus.py (reserve at certain time, retry quickly if it fails) **OR** watch.py (check every few seconds and reserve once available). If you choose the latter, parameter "booking_time" and "retry_times" will be ignored.

### IMPORTANT NOTES

Successful auto reservation can succeed **ONLY** when:

- Your PC doesn't hibernate or sleep
- Anti-virus software doesn't stop the script from opening the browser
- Windows update doesn't reboot your PC when you are asleep

### Typical Terminal Output
#### Success
```
[00:27:33.152897] 预计等待23366.847118s后启动浏览器.
...
[05:57:33.160762] 预计等待3566.839248s后启动浏览器.
>> 线程0负责: Fenglin 2026-03-16 19:00-20:00
>> 线程1负责: Fenglin 2026-03-16 20:00-21:00
[06:57:00.001581](线程0) 开始启动浏览器.
[06:57:00.004376](线程1) 开始启动浏览器.
[06:57:01.771717](线程0) 判断是否弹出了对话框...
[06:57:01.986354](线程1) 判断是否弹出了对话框...
[06:57:09.783834](线程0) 未弹出对话框. Message: no such element: Unable to locate element: {"method":"xpath",...
[06:57:09.837341](线程0) 浏览器启动完毕.
[06:57:09.837431](线程0) 正在读取和预加载日历...
[06:57:10.066166](线程1) 未弹出对话框. Message: no such element: Unable to locate element: {"method":"xpath",...
[06:57:10.084047](线程1) 浏览器启动完毕.
[06:57:10.084173](线程1) 正在读取和预加载日历...
[06:57:10.128238](线程0) 读取和预加载完毕.
[06:57:10.128334](线程0) 正在获取目标场次和预约按钮的element...
[06:57:10.152930](线程0) 获取完毕!
[06:57:10.364945](线程1) 读取和预加载完毕.
[06:57:10.365030](线程1) 正在获取目标场次和预约按钮的element...
[06:57:10.380029](线程1) 获取完毕!
[07:00:00.000117](线程1) 调用抢场函数...
[07:00:00.000160](线程0) 调用抢场函数...
[07:00:01.275263](线程0) 点击抢场成功! Message: stale element reference: stale element not found in the curre...
[07:00:01.740788](线程1) 点击抢场成功! Message: stale element reference: stale element not found in the curre...
[07:00:02.091422] 所有线程均已结束.
```
#### Fail
```
>> 线程0负责: Fenglin 2026-03-17 20:00-21:00
>> 线程1负责: Fenglin 2026-03-17 19:00-20:00
[14:32:59.869874](线程0) 开始启动浏览器.
[14:32:59.870030](线程1) 开始启动浏览器.
[14:33:03.097994](线程1) 判断是否弹出了对话框...
[14:33:03.208332](线程0) 判断是否弹出了对话框...
[14:33:13.115354](线程1) 未弹出对话框. Message: no such element: Unable to locate element: {"method":"xpath",...
[14:33:13.126294](线程1) 浏览器启动完毕.
[14:33:13.126714](线程1) 正在读取和预加载日历...
[14:33:13.238766](线程0) 未弹出对话框. Message: no such element: Unable to locate element: {"method":"xpath",...
[14:33:13.303741](线程0) 浏览器启动完毕.
[14:33:13.303872](线程0) 正在读取和预加载日历...
[14:33:14.273049](线程1) 读取和预加载完毕.
[14:33:14.273892](线程1) 正在获取目标场次和预约按钮的element...
[14:33:14.289771](线程1) 获取完毕!
[14:33:14.634401](线程0) 读取和预加载完毕.
[14:33:14.634660](线程0) 正在获取目标场次和预约按钮的element...
[14:33:14.666044](线程0) 获取完毕!
[14:35:00.000595](线程0) 调用抢场函数...
[14:35:00.001138](线程1) 调用抢场函数...
[14:35:00.263228](线程0) 当前场次约满 (4/4), 下面进行第1次刷新尝试.
[14:35:00.266357](线程1) 当前场次约满 (4/4), 下面进行第1次刷新尝试.
...
[14:35:01.486466](线程1) 当前场次约满 (4/4), 下面进行第5次刷新尝试.
[14:35:01.502873](线程0) 当前场次约满 (4/4), 下面进行第5次刷新尝试.
[14:35:01.800446](线程1) 5次刷新后仍未开放或已约满, 抢场失败.
[14:35:01.871505](线程0) 5次刷新后仍未开放或已约满, 抢场失败.
[14:35:01.941770] 所有线程均已结束.
```

## How it Works

Most details are explained in the comments of the code. 

### A High Level Overview

- By repeated `time.sleep(1800)`, the script remains silent until three minutes before seven.
- Then, browsers are initialized (the number of browsers depends on how many courts will be reserved simultaneously), each operated by a thread and responsible for one court.
- Each thread gets the web element of the corresponding court button according to date and time:
  - First extract the text of the week calendar.
  - Then use regular expression to extract all dates and times that exist in the calendar as two lists.
  - Get the list index of the date and time of the desired court, and then XPATH is clear.

- Switch to the previous week page and counts down to seven.
- The instant it turns seven, all threads click "next week", then the court, and finally the confirm button.
  - If it displays "Not open" or "Full" instead of "Available" on the court button, the script will go through a three-time retry (configurable by argument "retry_times" in function auto_book()). Each clicks "previous week" then "next week" to refresh the calendar.


### Muse

Below I'd like to elaborate on some important or interesting designs.

- **Ways to speed the booking process**. During the development process, I came up with multiple approaches that contribute to booking speed.
  - First and foremost, it is known that refreshing the website is much slower than simply click the "next week" button, but few know they both refresh the booking state. In other words, you can click "next week" the moment it turns seven and the court will be available. The script copies aforementioned acts to ensure punctuality.
  - Second, the script awaits the calendar to be refreshed (This is rather important, since premature click can lead to clicking the stale court) in a clever way: wait until the attribute "loading-parent-box" disappears. By step by step debugging, I found that this attribute appears very shortly after the button is clicked, and disappears right after the calendar switches. It (0.46s per cycle, tested in Science Library on 3/9/2026) reduces time spent by 30% compared to waiting until certain text (say, the date of target court) appears in the calendar. However, it leads to the above problem (40% chance of clicking the stale court). To reduce uncertainty, a `time.sleep()` is necessary.
  - Third, the script finds the web element of the court and the booking button three minutes prior to the actual booking process, and thus save about 20ms by test.
  - Fourth, by clicking "previous week" and then "next week", the script ensures the page containing the targeted court is preloaded.
  - Too frequent reserving can lead to failure. More specifically, a minimum time interval is required between two successive reservations using one UIS. At first, argument "offset" in auto_book() function was defined to specify this interval, and was set to 3s by default. But then I found a more widely-applied way: repeatedly click the reserve button at high frequency until reservation succeeds.
  - As you can tell in the previous point, if reservations are made using different account simultaneously, the problem can be avoided. The script supports that.
- **Important waits in the booking process.** Web programs is different from other programs, since loading takes time. Proper wait approaches are crucial for an efficient script.
  - **Implicit wait.** Once find_element() is called, implicit wait allows the script to wait for certain seconds before the element finally appears on the website. But presence doesn't mean clickable, so this approach is only adopted when the element is sure to have appeared for some time.
  - **Explicit wait.** This approach is widely applied and particularly useful in successive operations, like clicking the court button after calendar refreshes. Because:
    - Module EC makes it possible to wait until certain attributes of the element appears, like clickable.
    - The polling interval of explicit wait is also configurable, bringing much more flexibility and efficiency.
    - It is also possible to ignore certain exceptions during explicit wait, which can save a try-catch.
    - However, neglect of exceptions can somehow hinder bug-fix if there is any.
- **Save interruption.** At first, I use scheduler to start the booking thread at exact seven, but `scheduler.run()` will block the thread and preclude Keyboard-Interrupt. Hence, I use cyclic sleep instead. A stop-event was defined: once set, the loop will break.
  - It is worth mentioning that scheduler can achieve the precision of 0.0005s, but cyclic sleep only 0.002s. However, that's still acceptable.
