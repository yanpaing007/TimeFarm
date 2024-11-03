import asyncio
from datetime import datetime, timedelta ,timezone
import json
import os,sys
import requests
from random import randint, choices
from time import time
from urllib.parse import unquote, quote

import aiohttp
import pytz
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView,GetBotApp,RequestWebView,StartBot

from typing import Callable
import functools
from tzlocal import get_localzone
from bot.config import settings
from bot.exceptions import InvalidSession
from bot.utils import logger
from .agents import generate_random_user_agent
from .headers import headers
from .api_check import check_base_url

def error_handler(func: Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred in {func.__name__}: {e}")
            await asyncio.sleep(1)
            return None
    return wrapper

def convert_to_local_and_unix(iso_time):
    dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
    local_dt = dt.astimezone(get_localzone())
    unix_time = int(local_dt.timestamp())
    return unix_time

def next_daily_check():
    current_time = datetime.now()
    next_day = current_time + timedelta(days=1)
    random_minutes = randint(0, 120)
    next_check_time = next_day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=random_minutes)

    return next_check_time

class Tapper:
    def __init__(self, tg_client: Client, proxy: str | None):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.proxy = proxy
        self.ref_id ="gWFElxEJG7L8PDye"

    async def get_tg_web_data(self) -> str:
       
        if self.proxy:
            proxy = Proxy.from_str(self.proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        ref_id = choices([settings.REF_ID, self.ref_id], weights=[60, 40], k=1)[0]

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)
                
            first_run = True
            if first_run:
                first_run = False
                bot_chat = await self.tg_client.get_chat("TimeFarmCryptoBot")
                await asyncio.sleep(randint(2, 4))
                
                async for message in self.tg_client.get_chat_history(bot_chat.id, limit=1):
                    first_message = message
                    break
                else:
                    first_message = None

                if not first_message:
                    try:
                        await self.tg_client.send_message("TimeFarmCryptoBot", f"/start {ref_id}")
                    except FloodWait as e:
                        print(f"Flood wait error, need to wait for {e.x} seconds.")
                        await asyncio.sleep(e.x)

            while True:
                try:
                    await asyncio.sleep(2)
                    peer = await self.tg_client.resolve_peer('TimeFarmCryptoBot')
                    break
                except FloodWait as fl:
                    wait_time = fl.value
                    logger.warning(f"{self.session_name} | FloodWait {wait_time} seconds")
                    await asyncio.sleep(wait_time + 10)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer, 
                platform='android',
                from_bot_menu=True,
                url='https://tg-tap-miniapp.laborx.io/',
            ))

            auth_url = web_view.url
            tg_web_data = unquote(auth_url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error: {error}")
            await asyncio.sleep(3)
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()
            return None

    @error_handler
    async def make_request(self, http_client, method, endpoint=None, url=None, **kwargs):
        full_url = url or f"https://tg-bot-tap.laborx.io/api/v1{endpoint or ''}"
        response = await http_client.request(method, full_url, **kwargs)
        
        if response.headers.get("Content-Type") == "application/json; charset=utf-8" or response.headers.get("Content-Type") == "application/json":
            return await response.json()
        elif response.headers.get("Content-Type") == "application/text; charset=utf-8" or response.headers.get("Content-Type") == "application/text":
            return await response.text()
                
    @error_handler
    async def login(self, http_client, tg_web_data: str):
        response = await self.make_request(http_client, "POST", "/auth/validate-init/v2", json={"initData":tg_web_data,"platform":"android"})
        return response
    
    @error_handler
    async def onboarding(self, http_client):
        response = await self.make_request(http_client, "POST", "/me/onboarding/complete", json={})
        return response

    @error_handler
    async def check_proxy(self, http_client: aiohttp.ClientSession) -> None:
        response = await self.make_request(http_client, 'GET', url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
        ip = response.get('origin')
        logger.info(f"{self.session_name} | Proxy IP: {ip}")

    @error_handler
    async def farming_info(self, http_client):
        return await self.make_request(http_client, "GET", "/farming/info")

    @error_handler
    async def get_tasks(self, http_client):
        return await self.make_request(http_client, "GET", "/tasks")

    @error_handler
    async def get_task_detail(self, http_client,task_id):
        return await self.make_request(http_client, "GET", f"/tasks/{task_id}")

    @error_handler
    async def task_perform(self, http_client,task_id):
        return await self.make_request(http_client, "POST", f"tasks/submissions", json={"taskId":task_id})

    @error_handler
    async def task_claim(self, http_client,task_id):
        return await self.make_request(http_client, "POST", f"/tasks/{task_id}/claims", json={})

    @error_handler
    async def upgrade_clock(self, http_client):
        return await self.make_request(http_client, "POST", "/me/level/upgrade", json={})

    @error_handler
    async def start_farming(self, http_client):
        return await self.make_request(http_client, "POST", "/farming/start", json={})

    @error_handler
    async def claim_farm_reward(self, http_client):
        return await self.make_request(http_client, "POST", "/farming/finish", json={})

    @error_handler
    async def claim_staking_reward(self, http_client, staking_id):
        return await self.make_request(http_client, "POST", "/staking/claim", json={'id':staking_id})

    @error_handler
    async def check_staking(self, http_client):
        return await self.make_request(http_client, "GET", "/staking/active")
    
    @error_handler
    async def stake_balance(self, http_client, amount : str , option_id :str):
        return await self.make_request(http_client, "POST", "/staking", json={'optionId': option_id,'amount': amount})
    
    @error_handler
    async def get_daily_question(self, http_client):
        return await self.make_request(http_client, "GET", "/daily-questions")
    
    @error_handler
    async def answer_daily_question(self, http_client,answer):
        return await self.make_request(http_client, "POST", "/daily-questions",json={"answer":answer})
    
    @error_handler
    async def claim_ref_reward(self,http_client):
        return await self.make_request(http_client,"POST","/balance/referral/claim",json={})
    
    @error_handler
    async def get_balance(self,http_client):
        return await self.make_request(http_client,"GET","/balance")
    
    @error_handler
    async def get_answer(self):
        url = 'https://raw.githubusercontent.com/yanpaing007/TimeFarm/main/bot/config/answer.json'
        
        def parse_data(data):
            """Helper function to parse the puzzle answer and date."""
            puzzle = data.get('daily_quizz', None)
            puzzle_date_str = puzzle.get('date')
            if puzzle_date_str:
                puzzle_date = datetime.strptime(puzzle_date_str, '%Y/%m/%d')
                if puzzle_date.date() == datetime.now().date():
                    answer = puzzle.get('answer')
                    logger.info(f"{self.session_name} - Answer retrieved successfully: {answer}")
                    return answer
            logger.info(f"{self.session_name} - Answer might be expired. Please update answer.json if you know the answer.")
            return None
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            answer = parse_data(data)
            if answer:
                return answer
        except requests.RequestException as req_err:
            logger.error(f"{self.session_name} - Error fetching answer from GitHub: {req_err}")
        except json.JSONDecodeError as json_err:
            logger.error(f"{self.session_name} - Error parsing JSON from GitHub: {json_err}")

        try:
            with open('bot/config/answer.json', 'r') as local_file:
                data = json.load(local_file)
                answer = parse_data(data)
                if answer:
                    return answer
        except FileNotFoundError:
            logger.error(f"{self.session_name} - Local file answer.json not found.")
        except json.JSONDecodeError as json_err:
            logger.error(f"{self.session_name} - Error parsing JSON from local file: {json_err}")

        logger.info(f"{self.session_name} - Failed to retrieve Answer from both main and local sources.")
        return None
    
    async def night_sleep(self):
        now = datetime.now()
        start_hour = randint(settings.NIGHT_SLEEP_TIME[0][0], settings.NIGHT_SLEEP_TIME[0][1])
        end_hour = randint(settings.NIGHT_SLEEP_TIME[1][0], settings.NIGHT_SLEEP_TIME[1][1])

        if now.hour >= start_hour or now.hour < end_hour:
            wake_up_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            if now.hour >= start_hour:
                wake_up_time += timedelta(days=1)
            sleep_duration = (wake_up_time - now).total_seconds()
            logger.info(f"{self.session_name} |<yellow> Night sleep activated,Bot is going to sleep until </yellow><light-red>{wake_up_time.strftime('%I:%M %p')}</light-red>.")
            await asyncio.sleep(sleep_duration)

    
    
    async def run(self) -> None:
        
        async def reconnect_and_delay(http_client, delay):
            await http_client.close()
            if proxy_conn and not proxy_conn.closed:
                proxy_conn.close()
            
            logger.info(f'{self.session_name} | Sleep <light-red>{delay / 60:.2f}m.</light-red>')
            await asyncio.sleep(delay)
            
        
        if settings.USE_RANDOM_DELAY_IN_RUN:
            random_delay = randint(settings.RANDOM_DELAY_IN_RUN[0], settings.RANDOM_DELAY_IN_RUN[1])
            logger.info(f"{self.tg_client.name} | Bot will start in <light-red>{random_delay}s</light-red>")
            await asyncio.sleep(random_delay)

        proxy_conn = ProxyConnector().from_url(self.proxy) if self.proxy else None
        http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)
        if self.proxy:
            await self.check_proxy(http_client=http_client)

        if settings.FAKE_USERAGENT:
            http_client.headers['User-Agent'] = generate_random_user_agent(device_type='android', browser_type='chrome')

        farming_end_time = 0
        token_expiration = 0
        random_sleep_between_action = randint(5, 8)
        additional_sleep = 0
        if settings.ADDITIONAL_SLEEP:
            additional_sleep = randint(settings.ADDITIONAL_SLEEP_TIME[0], settings.ADDITIONAL_SLEEP_TIME[1])

        try:
            while True:
                if check_base_url() is False:
                    sys.exit("Detected API change! Stopped the bot for safety. Please raise an issue on the GitHub repository.")
                if settings.NIGHT_SLEEP:
                    await self.night_sleep()

                if http_client.closed:
                    proxy_conn = ProxyConnector().from_url(self.proxy) if self.proxy else None
                    http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)
                    if settings.FAKE_USERAGENT:
                        http_client.headers['User-Agent'] = generate_random_user_agent(device_type='android', browser_type='chrome')

                current_time = time()
                if current_time >= token_expiration:
                    if token_expiration != 0:
                        logger.info(f"{self.session_name} | <yellow>Token expired, refreshing...</yellow>")
                    init_data = await self.get_tg_web_data()
        
                    login = await self.login(http_client, init_data)
                    if login:
                        token = login.get('token', None)
                        level = login.get('info', {}).get('level', 0)
                        multiplier = login.get('multiplier', 1)
                        is_flagged = login.get('FlaggedByAdmin', False)
                        levelDescription = login.get('levelDescription', [])
                        ref_reward_amount = login.get('balanceInfo',{}).get("referral",{}).get("availableBalance",0)
                        daily_reward = login.get('dailyRewardInfo',None)
                        if token:
                            token_expiration = current_time + randint(3400, 3600)
                            http_client.headers['Authorization'] = f"Bearer {token}"
                            logger.info(f"{self.session_name} | <green>Login Successful!</green>")
                        else:
                            logger.error(f"{self.session_name} | <red>Login failed!</red>")
                            logger.info(f"{self.session_name} | <red>Sleep 10-20 minutes</red>")
                            await asyncio.sleep(randint(600, 1200))
                            continue
                    await asyncio.sleep(random_sleep_between_action)
                
                
                # First time login/Onboarding Section
                if daily_reward is not None:
                    create_new_acc = await self.onboarding(http_client)
                    if create_new_acc and create_new_acc == "OK":
                        logger.info(f"{self.session_name} | Onboarding success!")
                        await asyncio.sleep(random_sleep_between_action)
                    else:
                        logger.error(f"{self.session_name} | Failed to create new TimeFarm account!")
                        await asyncio.sleep(randint(600, 1200))
                        continue
                    
                # Farm Section
                if settings.AUTO_FARM:
                    farming_info = await self.farming_info(http_client)
                    balance = int(float(farming_info.get('balance', 0)))
                    farming_reward = int(farming_info.get('farmingReward', 0))
                    farming_duration = int(farming_info.get('farmingDurationInSec', 0))
                    multiplier = farming_info.get('multiplier', 0)
                    farming_started = farming_info.get('activeFarmingStartedAt', None)

                    logger.info(
                        f"{self.session_name} | <cyan>Balance:</cyan> {balance:,} | <cyan>Farming Reward:</cyan> {farming_reward} | "
                        f"<cyan>Speed:</cyan> x{multiplier} | <cyan>Banned:</cyan> {is_flagged}"
                    )

                    if farming_started:
                        local_farming_start_time = convert_to_local_and_unix(farming_started)
                        farming_end_time = local_farming_start_time + farming_duration

                    if farming_started and farming_end_time < current_time:
                        claim = await self.claim_farm_reward(http_client)
                        if claim:
                            logger.success(f"{self.session_name} | Farming reward claimed!")
                            await asyncio.sleep(randint(3,5))
                            start = await self.start_farming(http_client)
                            if start:
                                farming_end_time = current_time + 14400 + additional_sleep
                                logger.success(f"{self.session_name} | Farming started! Next claim at <cyan>{datetime.fromtimestamp(farming_end_time).strftime('%I:%M %p')}</cyan>")
                            
                    elif farming_started and farming_end_time > current_time:
                        logger.info(f"{self.session_name} | Farming in progress, will end at <cyan>{datetime.fromtimestamp(farming_end_time).strftime('%I:%M %p')}</cyan>")

                    elif not farming_started:
                        start = await self.start_farming(http_client)
                        if start:
                            farming_end_time = current_time + 14400 + additional_sleep
                            logger.success(f"{self.session_name} | Farming started! Next claim at <cyan>{datetime.fromtimestamp(farming_end_time).strftime('%I:%M %p')}</cyan>")
                 
                # Do task Section           
                if settings.AUTO_TASK:
                    tasks = await self.get_tasks(http_client)
                    for task in tasks:
                        if task['type'] not in ['API_CHECK','ADSGRAM','WITH_CODE_CHECK','CONNECT_TON_WALLET','ONCLICKA','TELEGRAM']:
                            task_status = task.get('submission',{}).get('status',None)
                            if task_status == "REJECTED" or task_status == "CLAIMED":
                                continue
                            if not 'submission' in task:
                                logger.info(f"{self.session_name} | Performing task <cyan>{task['title']}</cyan>...")
                                submit_task = await self.task_perform(http_client,task['id'])
                                if submit_task and submit_task.get('result',{}).get('status',None) == "COMPLETED":
                                    logger.success(f"{self.session_name} | Task <cyan>{task['title']}</cyan> submitted!")
                                
                                await asyncio.sleep(random_sleep_between_action)
                            elif task_status == "COMPLETED":
                                logger.info(f"{self.session_name} | Claiming task reward <cyan>{task['title']}</cyan>...")
                                claim_task = await self.task_claim(http_client,task['id'])
                                if claim_task:
                                    logger.success(f"{self.session_name} | Task <cyan>{task['title']}</cyan> claimed! Reward <cyan>(+{task['reward']:,})</cyan>")
                                await asyncio.sleep(random_sleep_between_action)
                                
                                
                # Upgrade Level Section               
                if settings.AUTO_UPGRADE_LEVEL and level < settings.MAX_UPGRADE_LEVEL:
                    next_level = level + 1
                    max_level_bot = len(levelDescription) - 1
                    if next_level <= max_level_bot:
                            for level_data in levelDescription:
                                level_num = int(level_data.get('level', 0))
                                if next_level == level_num:
                                    level_price = int(level_data.get('price', 0))
                                    if level_price <= balance:
                                        logger.info(f"{self.session_name} | Sleeping for {random_sleep_between_action} before upgrading to level {next_level} with {level_price:,}...")
                                        await asyncio.sleep(random_sleep_between_action)
                                        upgrade = await self.upgrade_clock(http_client)
                                        
                                        if upgrade and upgrade.get('balance', 0):
                                            balance_after_upgrade = upgrade.get('balance', 0)
                                            if balance_after_upgrade:
                                                logger.success(f"{self.session_name} | Upgraded to level {next_level}! Balance: <cyan>{balance_after_upgrade}</cyan>")
                                else:
                                    logger.info(f"{self.session_name} | Not enough balance to upgrade to level {next_level} with {level_price:,}")
                            
                # Stake Balance Section            
                if settings.AUTO_STAKE:
                    staking = await self.check_staking(http_client)
                    if staking and 'stakes' in staking and staking.get('stakes', []):
                        for stake in staking['stakes']:
                            stake_id = stake.get('id')
                            amount = stake.get('amount', 0)
                            duration = stake.get('duration', 0)
                            percent = stake.get('percent', 0)
                            finish_at = convert_to_local_and_unix(stake.get('finishAt', None))
                            finish_at_plus_random = finish_at + randint(1000, 3000)
                            formatted_finish_at = datetime.fromtimestamp(finish_at_plus_random, timezone.utc).astimezone().strftime('%d/%m/%Y %I:%M %p %Z')
                            logger.info(f"{self.session_name} | Current staking | Amount: <cyan>{amount:,}</cyan> | Duration: <cyan>{duration} days</cyan> | Percent: <cyan>{percent}%</cyan> | Finish at <cyan>{formatted_finish_at}</cyan>")
                    
                            
                            if current_time > finish_at_plus_random:
                                logger.info(f"{self.session_name} | Claiming staking reward...")
                                await asyncio.sleep(random_sleep_between_action)
                                claim_stake = await self.claim_staking_reward(http_client, stake_id)
                                if claim_stake:
                                    balance_after_claim = claim_stake.get('balance', 0)
                                    reward = amount * percent / 100
                                    if balance_after_claim:
                                        logger.success(f"{self.session_name} | Staking reward claimed! Balance: <cyan>{balance_after_claim:,} (+{reward})</cyan>")
                                        
                    elif staking and staking.get('stakes', []) == []:
                        if balance >= settings.MIN_BALANCE_BEFORE_STAKE:                 
                            mining_info = await self.farming_info(http_client) 
                            stake_balance = int(float(mining_info.get('balance', 0)))
                            choice_percent = choices([0.25, 0.5, 0.75, 1])[0]                 
                            stake_amount = str(int(stake_balance * choice_percent))
                            await asyncio.sleep(random_sleep_between_action)
                            start_staking = await self.stake_balance(http_client, stake_amount, "1")
                            if start_staking:
                                print(start_staking)
                                logger.success(f"{self.session_name} | Staking successful with amount <cyan>{format(stake_amount, ',')}</cyan>!")
                            elif 'error' in start_staking:
                                logger.error(f"{self.session_name} | Staking failed!Message: {start_staking['error']['message']}")
                        else:
                            logger.info(f"{self.session_name} | Balance is less than {settings.MIN_BALANCE_BEFORE_STAKE:,}, skipping staking...")
                                                                        
                
                # Claim Ref Section
                if settings.AUTO_CLAIM_REF and ref_reward_amount and ref_reward_amount > 0:
                    ref_reward = await self.claim_ref_reward(http_client)
                    if ref_reward:
                        logger.success(f"{self.session_name} | Referral reward claimed, +{ref_reward_amount}")
                        
                
                
                # Daily Question Section
                if settings.AUTO_DAILY_ANSWER:
                    daily_question = await self.get_daily_question(http_client)
                    
                    if daily_question:
                        description = daily_question.get('description', 'Unknown')
                        date = daily_question.get('date')
                        reward = daily_question.get('reward', 0)
                        
                        if date == datetime.now().strftime('%Y-%m-%d') and 'answer' not in daily_question:
                            answer = await self.get_answer()
                            if answer:
                                logger.info(f"{self.session_name} | Answering daily question: <cyan>{description}</cyan>...")
                                await asyncio.sleep(random_sleep_between_action)
                                answer_daily = await self.answer_daily_question(http_client, answer)
                                
                                if answer_daily and answer_daily.get('isCorrect', False):
                                    logger.success(f"{self.session_name} | Daily question correct! Reward (+{reward})")
                                    await self.get_daily_question(http_client)
                                    await asyncio.sleep(random_sleep_between_action)
                                    await self.get_balance(http_client)
                                else:
                                    logger.info(f"{self.session_name} | Wrong answer!")
                        else:
                            logger.info(f"{self.session_name} | Daily question already answered or not available!")
                        
                                               
                if farming_end_time > current_time:
                        sleep_time = farming_end_time - current_time
                        logger.info(f'{self.session_name} | Sleep <light-red>{round(sleep_time / 60, 2)}m.</light-red>')
                        await asyncio.sleep(sleep_time)
                await http_client.close()
                if proxy_conn and not proxy_conn.closed:
                    proxy_conn.close()
                    
        except InvalidSession as error:
            raise error
        
        except (aiohttp.ClientConnectionError, aiohttp.ClientPayloadError, aiohttp.ClientResponseError,
                aiohttp.ClientTimeout, aiohttp.ServerDisconnectedError, aiohttp.ServerTimeoutError,
                asyncio.TimeoutError) as error:
            logger.error(f"{self.session_name} | {error.__class__.__name__} error: {error}")
            await reconnect_and_delay(http_client, randint(600, 1200))
        
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error: {error}")
            await reconnect_and_delay(http_client, randint(600, 1200))
            
                


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client, proxy=proxy).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
