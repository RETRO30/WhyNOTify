from typing import List, Self
from database.database import Base
from sqlalchemy import Column, Enum, Integer, String, DateTime, Text, ForeignKey, func, select, JSON
from sqlalchemy.orm import relationship
import enum
from database.database import async_session


class AccountStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BANNED = "banned"


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(100), nullable=False, unique=True)
    telegram_session = Column(Text, nullable=True)
    password = Column(String(100), nullable=True)
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.PENDING)
    proxy_id = Column(Integer, ForeignKey("proxies.id"), unique=True)
    proxy = relationship("Proxy", back_populates="account")

    @staticmethod
    async def add(phone_number: str, password=None, status=AccountStatus.PENDING, proxy=None):
        async with async_session() as session:
            new_account = Account(phone_number=phone_number, password=password, status=status, proxy=proxy)
            session.add(new_account)
            await session.commit()
            return new_account

    @staticmethod
    async def get_by_id(id: int):
        async with async_session() as session:
            account = await session.scalar(select(Account).where(Account.id == id))
            return account

    @staticmethod
    async def get_by_phone_number(phone_number):
        async with async_session() as session:
            account = await session.scalar(select(Account).where(Account.phone_number == phone_number))
            return account

    @staticmethod
    async def get_all():
        async with async_session() as session:
            accounts = await session.scalars(select(Account).order_by(Account.id))
            return accounts

    @staticmethod
    async def get_all_active():
        async with async_session() as session:
            accounts = await session.scalars(select(Account).where(Account.status == AccountStatus.ACTIVE).order_by(Account.id))
            return accounts

    @staticmethod
    async def get_count_by_status(status: AccountStatus):
        async with async_session() as session:
            count = await session.scalar(select(func.count(Account.id)).where(Account.status == status))
            return count

    @staticmethod
    async def get_total_count():
        async with async_session() as session:
            count = await session.scalar(select(func.count(Account.id)))
            return count

    @staticmethod
    async def delete_by_id(id: int):
        async with async_session() as session:
            account = await session.scalar(select(Account).where(Account.id == id))
            proxy = await session.scalar(select(Proxy).where(Proxy.account == account))
            if proxy:
                await session.delete(proxy)
            await session.delete(account)
            await session.commit()

    @staticmethod
    async def update_session(id: int, telegram_session: str):
        async with async_session() as session:
            account = await session.scalar(select(Account).where(Account.id == id))
            account.telegram_session = telegram_session
            account.status = AccountStatus.ACTIVE
            await session.commit()

    @staticmethod
    async def update_status(id: int, status: AccountStatus):
        async with async_session() as session:
            account = await session.scalar(select(Account).where(Account.id == id))
            account.status = status
            await session.commit()

    def __repr__(self):
        return f"Account({self.phone_number})"

    def __str__(self):
        return f"Account({self.phone_number})"


class Proxy(Base):
    __tablename__ = "proxies"
    id = Column(Integer, primary_key=True)
    scheme = Column(String(100), nullable=False)
    hostname = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    account = relationship("Account", uselist=False, back_populates="proxy")

    @staticmethod
    async def add(scheme: str, hostname: str, port: int, username: str, password: str, account=None):
        async with async_session() as session:
            new_proxy = Proxy(scheme=scheme, hostname=hostname, port=port, username=username, password=password, account=account)
            session.add(new_proxy)
            await session.commit()
            return new_proxy

    @staticmethod
    async def get(id: int):
        async with async_session() as session:
            proxy = await session.scalar(select(Proxy).where(Proxy.id == id))
            return proxy

    @staticmethod
    async def get_by_account(account: Account):
        async with async_session() as session:
            account = await session.merge(account)
            proxy = await session.scalar(select(Proxy).where(Proxy.account == account))
            return proxy

    @staticmethod
    async def delete_by_id(id: int):
        async with async_session() as session:
            proxy = await session.scalar(select(Proxy).where(Proxy.id == id))
            await session.delete(proxy)
            await session.commit()

    def __repr__(self):
        return f"Proxy({self.scheme}://{self.username}:{self.password}@{self.hostname}:{self.port})"

    def __str__(self):
        return f"Proxy({self.scheme}://{self.username}:{self.password}@{self.hostname}:{self.port})"


class ChannelType(enum.Enum):
    STICKERS = "stickers"
    TECHNICAL = "technical"


class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    channel_id = Column(String(100), nullable=False)
    type = Column(Enum(ChannelType), nullable=False)

    def __str__(self):
        return f"Channel(channel_id={self.channel_id})"

    def __repr__(self):
        return f"Channel(channel_id={self.channel_id})"

    @staticmethod
    async def add(name: str, channel_id: str, type: ChannelType):
        async with async_session() as session:
            new_channel = Channel(name=name, channel_id=channel_id, type=type)
            session.add(new_channel)
            await session.commit()
            return new_channel

    @staticmethod
    async def get_by_id(id: int):
        async with async_session() as session:
            channel = await session.scalar(select(Channel).where(Channel.id == id))
            return channel

    async def get_total_count():
        async with async_session() as session:
            count = await session.scalar(select(func.count(Channel.id)))
            return count

    async def get_count_by_type(type: ChannelType):
        async with async_session() as session:
            count = await session.scalar(select(func.count(Channel.id)).where(Channel.type == type))
            return count

    @staticmethod
    async def get_all():
        async with async_session() as session:
            channels = await session.scalars(select(Channel).order_by(Channel.id))
            return channels

    @staticmethod
    async def delete_by_id(id: int):
        async with async_session() as session:
            channel = await session.scalar(select(Channel).where(Channel.id == id))
            await session.delete(channel)
            await session.commit()


class Stickerpack(Base):
    __tablename__ = "stickerpacks"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    pack_id = Column(String(100), nullable=False)

    def __str__(self):
        return f"Stickerpack(pack_id={self.pack_id})"

    def __repr__(self):
        return f"Stickerpack(pack_id={self.pack_id})"

    @staticmethod
    async def add(name: str, pack_id: str):
        async with async_session() as session:
            new_pack = Stickerpack(name=name, pack_id=pack_id)
            session.add(new_pack)
            await session.commit()
            return new_pack

    @staticmethod
    async def get_by_id(id: int):
        async with async_session() as session:
            pack = await session.scalar(select(Stickerpack).where(Stickerpack.id == id))
            return pack

    @staticmethod
    async def get_all():
        async with async_session() as session:
            packs = await session.scalars(select(Stickerpack).order_by(Stickerpack.id))
            return packs

    @staticmethod
    async def delete_by_id(id: int):
        async with async_session() as session:
            pack = await session.scalar(select(Stickerpack).where(Stickerpack.id == id))
            await session.delete(pack)
            await session.commit()


class CollectionType(enum.Enum):
    STICKERS = "stickers"
    STICERPACKS = "stickerpacks"


class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    new_json = Column(JSON, nullable=False)
    update_json = Column(JSON, nullable=False)
    current_json = Column(JSON, nullable=False)
    additional_data = Column(String(100), nullable=True)
    type = Column(Enum(CollectionType), nullable=False)

    def __repr__(self):
        return f"Collections(id={self.id})"

    def __str__(self):
        return f"Collections(id={self.id})"

    @staticmethod
    async def add(new_json: list, update_json: list, current_json: list, type: CollectionType, additional_data: str = ""):
        async with async_session() as session:
            last_collection = await session.scalar(select(Collection).where(Collection.type == type).order_by(Collection.id.desc()).limit(1))
            new_collection = Collection(new_json=new_json,
                                        update_json=update_json,
                                        current_json=current_json,
                                        type=type,
                                        additional_data=additional_data)
            if len(new_json) > 0 or len(update_json) > 0 or last_collection is None:
                session.add(new_collection)
                await session.commit()
            return new_collection

    @staticmethod
    async def get_by_id(id: int):
        async with async_session() as session:
            collection = await session.scalar(select(Collection).where(Collection.id == id))
            return collection

    @staticmethod
    async def get_all():
        async with async_session() as session:
            collections = await session.scalars(select(Collection).order_by(Collection.id))
            return collections

    @staticmethod
    async def get_last(type: CollectionType, addtional_data: str = ""):
        async with async_session() as session:
            if addtional_data != "":
                collection = await session.scalar(
                    select(Collection).where(Collection.type == type).where(Collection.additional_data == addtional_data).order_by(
                        Collection.id.desc()).limit(1))
                return collection
            collection = await session.scalar(select(Collection).where(Collection.type == type).order_by(Collection.id.desc()).limit(1))
            return collection
