# FDCourtResv

In short, this is a selenium-based python script that helps to reserve sports courts **(especially the badminton court in Fenglin Campus, but extension interface remains accessible)** automatically.

## Repo Overview

Files in this repository are listed as follows:

- **[LearnSelenium.ipynb](LearnSelenium.ipynb)**. A brief selenium tutorial. It is basically all you need to understand the code in the script.
- **[single.py](single.py)**. The primary version of the script with junior waiting method. It is designed for only one court.
- **[multiple.py](multiple.py)**. The advanced version of the script. Readme is for this file.
- **readme.md**.

## Environment

- Python 3.13.3
- Selenium 4.40.0
- Microsoft Edge and its Driver 144.0.3719.115

> To maintain stability, it is strongly recommended to disable the Auto-update of Edge. To do it: 
>
> - run services.msc
> - switch start-type of **edgeupdate** from Auto to disabled
> - switch start-type of **edgeupdatem** from Manual to disabled

## How to Use the Script

1. Configure your UIS. Create "UIS.json" in the same directory as multiple.py and add:
```
{
    "username": "xxx", 
    "password": "xxx"
}
```
2. Set the desired booking time as the example in main thread demonstrated. Usually its the seven o'clock of the second day before the court.
3. Specify the dates and times of your desired court respectively in the two lists given in the main thread. Note that they must be in pairs.
4. Simply run the script.

## How it Works

Most details are explained in the comments of the code. 

### A High Level Overview

- By repeated time.sleep(1800), the script remains silent until three minutes before seven.
- Then, browsers are initialized (The number of browsers depends on how many courts will be reserved simultaneously), each operated by a thread and responsible for one court.
- Each thread gets the web element of the corresponding court button according to date and time:
  - First extract the text of the week calendar.
  - Then use regular expression to extract all dates and times that exist in the calendar as two lists.
  - Get the list index of the date and time of the desired court, and then XPATH is clear.

- Switch to the previous week page and counts down to seven.
- The instant it turns seven, all threads click "next week", then the court, and finally the confirm button.
  - If it displays "Not open" or "Full" instead of "Available" on the court button, the script will go through a three-time retry (three times by default, and configurable by argument "retry_times" in function auto_book()). Each clicks "previous week" then "next week" to refresh the calendar.


### Muse

Below I'd like to elaborate on some important or interesting designs.

- **Ways to speed the booking process**. During the development process, I came up with multiple approaches that contribute to booking speed.
  - First and foremost, it is known that refreshing the website is much slower than simply click the "next week" button, but few know they both refresh the booking state. In other words, you can click "next week" the moment it turns seven and the court will be available. The script copies aforementioned acts to ensure punctuality.
  - Second, the script awaits the calendar to be refreshed (This is rather important, since premature click can lead to clicking the stale court) in a clever way: wait until the attribute "loading-parent-box" disappear. It saves 40% time compared to waiting until certain text (say, the date of target court) appears in the calendar. However, sometimes the former approach leads to the aforementioned problem, but it's rare.
  - Third, the script finds the web element of the court three minutes prior to the actual booking process, and thus save about 10ms by test.
  - Fourth, by clicking "previous week" and then "next week", the script makes sure the page where targeted court is on is preloaded.
  - Too frequent reserving can lead to failure. More specifically, a minimum time interval is required between two successive reservations. At first, argument "offset" in auto_book() function was defined to specify this interval, and was set to 3s by default. But then I found a more widely-applied way: repeatedly click the reserve button at high frequency until reservation succeeds.
- **Important waits in the booking process.** Web programs is different from other programs, since loading takes time. Proper wait approaches are crucial for an efficient script.
  - **Implicit wait.** Once find_element() is called, implicit wait allows the script to wait for certain seconds before the element finally appears on the website. But presence doesn't mean clickable, so this approach is only adopted when the element is sure to have appeared for some time.
  - **Explicit wait.** Module EC makes it possible to wait until certain attributes of the element appears, like clickable. The polling interval of explicit wait is also configurable, bringing much more flexibility and efficiency. This approach is widely applied in successive operations, like clicking the court button after calendar refreshes. 

- **Save interruption.** At first, I use scheduler to start the booking thread at exact seven, but scheduler.run() will block the thread and preclude Keyboard-Interrupt. Hence, I use cyclic sleep instead. A stop-event was defined: once set, the loop will break.
  - It is worth mentioning that scheduler can achieve the precision of 0.0005s, but cyclic sleep only 0.002s. However, that's still acceptable.

