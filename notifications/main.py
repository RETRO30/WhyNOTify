import asyncio
from notifications.manager import WorkerManager
from utils.config import Config
from utils.logger import logger
from notifications.bot import send_tech_messages

async def main():
    try:
        # Инициализация менеджера воркеров
        
        await send_tech_messages("Bot started")
        worker_manager = WorkerManager()
        await worker_manager.start()
    except Exception as e:
        await send_tech_messages(f"Error: {e}")
        logger.error(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())