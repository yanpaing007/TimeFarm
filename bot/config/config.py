from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    REF_ID: str = 'gWFElxEJG7L8PDye'
    
    FAKE_USERAGENT: bool = False
    AUTO_FARM: bool = True
    AUTO_STAKE: bool = True
    AUTO_CLAIM_REF: bool = True
    AUTO_TASK: bool = True
    AUTO_DAILY_ANSWER: bool = True
    ADDITIONAL_SLEEP: bool = True
    ADDITIONAL_SLEEP_TIME: list[int] = [100, 3600] # additional sleep time between farm and stake
    MIN_BALANCE_BEFORE_STAKE: int = 10000000  # wait until balance is 10,000,000
    AUTO_UPGRADE_LEVEL: bool = True
    MAX_UPGRADE_LEVEL: int = 6 
    NIGHT_SLEEP: bool = True   #strongly recommend to enable this
    NIGHT_SLEEP_TIME: list[list] = [[22 , 23],[3 , 4]] # 10,11pm to 3,4am


    USE_RANDOM_DELAY_IN_RUN: bool = True
    RANDOM_DELAY_IN_RUN: list[int] = [5, 30]

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()

