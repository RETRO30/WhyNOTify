from dataclasses import dataclass
from typing import List
from environs import Env

@dataclass(frozen=True, slots=True)
class Logger:
    level: str
    
@dataclass(frozen=True, slots=True)
class Database:
    hostname: str
    port: int
    username: str
    password: str
    database: str
    
@dataclass(frozen=True, slots=True)
class TelegramAPI:
    id: int
    hash: str

@dataclass(frozen=True, slots=True)
class TelegramBot:
    admin_token: str
    admins: List[str]
    notification_token: str


@dataclass(slots=True)
class Config:
    logger: Logger
    database: Database
    telegram_api: TelegramAPI
    telegram_bot: TelegramBot

    
def setup_config():
    env = Env()
    env.read_env()
    config = Config(
        logger=Logger(
            level=env.str("LOG_LEVEL")
        ),
        database=Database(
            hostname=env.str("DB_HOST"),
            port=env.int("POSTGRES_PORT"),
            username=env.str("POSTGRES_USER"),
            password=env.str("POSTGRES_PASSWORD"),
            database=env.str("POSTGRES_DB")
        ),
        telegram_api=TelegramAPI(
            id=env.int("API_ID"),
            hash=env.str("API_HASH")
        ),
        telegram_bot=TelegramBot(
            admin_token=env.str("ADMIN_BOT_TOKEN"),
            admins=env.list("ADMIN_IDS"),
            notification_token=env.str("NOTIFICATION_BOT_TOKEN")
        )
    )
    return config
    
Config = setup_config()
        