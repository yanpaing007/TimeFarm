[![Static Badge](https://img.shields.io/badge/Telegram-Bot%20Link-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/TimeFarmCryptoBot?start=gWFElxEJG7L8PDye)
> [!NOTE]
> I made this bot to behave like human interacting instead of bot by adding several time between each farm reward claim and stake claim time,this may have slightly impact on our reward but will have less chance of getting banned
> [!IMPORTANT]
> I suggest don't turn oof important feature like NIGHT_SLEEP

## Recommendation before use

# 🔥🔥 PYTHON version must be 3.10 to 3.11.5 🔥🔥

## Features

|                               Feature                                | Supported |
|:-------------------------------------------------------------------:|:---------:|
|                           Multithreading                            |     ✅     |
|                    Proxy binding to session                         |     ✅     |
|                 Auto Referral of your accounts                      |     ✅     |
|                    Automatic task completion                        |     ✅     |
|                  Support for pyrogram .session                      |     ✅     |
|                           Auto farming                              |     ✅     |
|                        Auto Stake                                   |     ✅     |
|                    Auto Claim Referral                              |     ✅     |
|                    Auto Daily Answer                                 |     ✅     |

## [Settings](https://github.com/yanpaing007/TimeFarm/blob/main/.env-example/)
|        Settings         |                                      Description                                       |
|:-----------------------:|:--------------------------------------------------------------------------------------:|
|  **API_ID**             |        Your Telegram API ID (integer)                                                  |
|  **API_HASH**           |        Your Telegram API Hash (string)                                                 |
|  **REF_ID**             |        Your referral id after startapp=                                                |
| **FAKE_USERAGENT**      |        Use a fake user agent for sessions (True / False)                               |
| **AUTO_FARM**           |        Automatically farm (True / False)                                               |
| **AUTO_STAKE**          |        Automatically stake (True / False)                                              |
| **AUTO_CLAIM_REF**      |        Automatically claim referral rewards (True / False)                             |
| **AUTO_TASK**           |        Automatically complete tasks (True / False)                                     |
| **AUTO_DAILY_ANSWER**   |        Automatically answer daily questions (True / False)                             |
| **ADDITIONAL_SLEEP**    |        Use additional sleep (True / False)                                             |
| **ADDITIONAL_SLEEP_TIME** |      Additional sleep time range (e.g., [100, 3600])                                  |
| **MIN_BALANCE_BEFORE_STAKE** | Minimum balance before staking (integer)                                          |
| **AUTO_UPGRADE_LEVEL**  |        Automatically upgrade level (True / False)                                      |
| **MAX_UPGRADE_LEVEL**   |        Maximum upgrade level (integer)                                                 |
| **NIGHT_SLEEP**         |        Use night sleep (True / False)                                                  |
| **NIGHT_SLEEP_TIME**    |        Night sleep time range (e.g., [[22, 23], [3, 4]])                               |
| **USE_RANDOM_DELAY_IN_RUN** | Whether to use random delay at startup (True / False)                              |
| **RANDOM_DELAY_IN_RUN** |        Random delay at startup (e.g., [5, 30])                                         |
| **USE_PROXY_FROM_FILE** |        Whether to use a proxy from the `bot/config/proxies.txt` file (True / False)    |

## Quick Start 📚

To fast install libraries and run bot - open run.bat on Windows or run.sh on Linux

## Prerequisites
Before you begin, make sure you have the following installed:
- [Python](https://www.python.org/downloads/) **version 3.10 to 3.11.5**

## Obtaining API Keys
1. Go to my.telegram.org and log in using your phone number.
2. Select "API development tools" and fill out the form to register a new application.
3. Record the API_ID and API_HASH provided after registering your application in the .env file.
4. If you don't have session files or first time bot user,first create a session folder ,then after run.sh (linux/mac) or run.bat(windows),choose option 2


## Installation
You can download the [**repository**](https://github.com/yanpaing007/TimeFarm) by cloning it to your system and installing the necessary dependencies:
```shell
git clone https://github.com/yanpaing007/TimeFarm.git
cd TimeFarm
```

Then you can do automatic installation by typing:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

# Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
python3 main.py
```

You can also use arguments for quick start, for example:
```shell
~/TimeFarm >>> python3 main.py --action (1/2)
# Or
~/TimeFarm >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
python main.py
```

You can also use arguments for quick start, for example:
```shell
~/TimeFarm >>> python main.py --action (1/2)
# Or
~/TimeFarm >>> python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```
