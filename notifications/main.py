import asyncio
import traceback
from notifications.manager import WorkerManager
from utils.config import Config
from utils.logger import logger
from notifications.bot import send_tech_messages

async def main():
    logger.success("Initializing...")
    try:
        # Инициализация менеджера воркеров
        await send_tech_messages("Bot started")
        worker_manager = WorkerManager()
        await worker_manager.start()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        logger.debug(traceback.format_exc())
        await send_tech_messages(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())