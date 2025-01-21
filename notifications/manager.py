import asyncio
from collections import deque
from datetime import datetime
from typing import List, Tuple
from database.models import Account, Collection, CollectionType, Stickerpack
from notifications.stickers import Stickers
from notifications.bot import send_messages, send_tech_messages, send_tech_collections_message, send_tech_stickerpacks_message
from notifications.schemas import Response, Status, Description
from utils.logger import logger

first_check_stickers = True
first_chack_stickerpacks = True

class Worker:
    def __init__(self, account: Account):
        self.account = account
        self.stickers = Stickers(account)
        
    async def setup(self):
        response: Response = await self.stickers.setup()
        if response.status == Status.ERROR:
            logger.error(f"{self.account} | Error setting up stickers: {response.description}")
            await send_tech_messages(f"{self.account} | Error setting up stickers: {response.description}")
            return response
        
        if response.status == Status.SUCCESS:
            logger.success(f"{self.account} | Stickers setup successful")
            return response
        
    async def task_stickers(self):
        global first_check_stickers
        last_collection = await Collection.get_last(type=CollectionType.STICKERS)
        
        response: Response = await self.stickers.check_updates(last_collections=last_collection)
        
        if response.status == Status.ERROR:
            await send_tech_messages(f"{self.account} | Error checking updates: {response.description}")
            logger.error(f"{self.account} | Error checking updates: {response.description}")
            return response
        await send_messages(collection=response.data)
        if first_check_stickers:
            await send_tech_collections_message(collection=response.data)
            first_check_stickers = False
        return response
        
    async def task_stickerpacks(self):
        global first_chack_stickerpacks
        stickerpacks: Tuple[Stickerpack] | None = await Stickerpack.get_all()
        
        if stickerpacks is None:
            return Response(Status.SUCCESS, Description.OK)
        for stickerpack in stickerpacks:
            last_collection = await Collection.get_last(type=CollectionType.STICKERPACKS, addtional_data=str(stickerpack.pack_id))
            
            response: Response = await self.stickers.check_update_stickerpacks(id=stickerpack.pack_id, last_collections=last_collection)
            
            if response.status == Status.ERROR:
                await send_tech_messages(f"{self.account} | Error checking updates stickerpacks: {response.description}")
                logger.error(f"{self.account} | Error checking updates stickerpacks: {response.description}")
                return response
            await send_messages(collection=response.data)
            if first_chack_stickerpacks:
                await send_tech_stickerpacks_message(collection=response.data)
                first_chack_stickerpacks = False
            return response
                
        
    
    async def task(self):
        response: Response = await self.task_stickers()
        if response.status == Status.ERROR:
            return response
        
        response: Response = await self.task_stickerpacks()
        return response
            
            
class WorkerManager:
    def __init__(self, utilization_percent: int = 50):
        self.workers: List[Worker] = []
        self.account_queue = deque()
        self.active_workers = {}  # worker: last_error_time
        self.utilization_percent = utilization_percent
        self.cooldown = 60  # cooldown in seconds
        self.request_delay = 5

    async def load_accounts_from_db(self):
        """
        Метод для загрузки аккаунтов из базы данных
        Здесь нужно реализовать вашу логику получения аккаунтов
        """
        accounts = await Account.get_all_active()  # Предполагаемый метод получения аккаунтов
        current_time = datetime.now()
        if not accounts:
            return
        for account in accounts:
            if account not in self.account_queue:
                # Проверяем, не находится ли аккаунт в кулдауне
                last_error = self.active_workers.get(account)
                if not last_error or (current_time - last_error).total_seconds() > self.cooldown:
                    self.account_queue.append(account)

    async def setup_workers(self):
        """Инициализация воркеров из очереди аккаунтов"""
        num_accounts = len(self.account_queue)
        workers_to_create = int(num_accounts * (self.utilization_percent / 100))
        
        for _ in range(workers_to_create):
            if self.account_queue:
                account = self.account_queue.popleft()
                worker = Worker(account)
                setup_response = await worker.setup()
                
                if setup_response.status == Status.SUCCESS:
                    self.workers.append(worker)
                    logger.success(f"Worker for {account} initialized successfully")
                else:
                    # Возвращаем аккаунт в конец очереди с пометкой времени ошибки
                    self.active_workers[account] = datetime.now()
                    await self.handle_failed_account(account)

    async def handle_failed_account(self, account):
        """Обработка аккаунта, у которого произошла ошибка"""
        await asyncio.sleep(self.cooldown)
        self.account_queue.append(account)

    async def replace_worker(self, worker: Worker):
        """Замена воркера на новый из очереди"""
        if worker in self.workers:
            self.workers.remove(worker)
            self.active_workers[worker.account] = datetime.now()
            
            # Пытаемся взять новый аккаунт из очереди
            while self.account_queue:
                new_account = self.account_queue.popleft()
                new_worker = Worker(new_account)
                setup_response = await new_worker.setup()
                
                if setup_response.status == Status.SUCCESS:
                    self.workers.append(new_worker)
                    logger.success(f"Replaced worker {worker.account} with {new_account}")
                    break
                else:
                    self.active_workers[new_account] = datetime.now()
                    await self.handle_failed_account(new_account)

    async def run_worker_task(self, worker: Worker):
        """Запуск задачи воркера с обработкой ошибок"""
        while True:
            try:
                response = await worker.task()
                if response and response.status == Status.ERROR:
                    await self.replace_worker(worker)
                    break
                await asyncio.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"Error in worker {worker.account}: {str(e)}")
                await send_tech_messages(f"Error in worker {worker.account}: {str(e)}")
                await self.replace_worker(worker)
                break

    async def start(self):
        """Запуск менеджера воркеров"""
        while True:
            await self.load_accounts_from_db()
            await self.setup_workers()
            
            # Запускаем задачи для всех воркеров
            tasks = [self.run_worker_task(worker) for worker in self.workers]
            await asyncio.gather(*tasks)
            
            # Ждем некоторое время перед следующей проверкой очереди
            await asyncio.sleep(30)
        
        
    
    

