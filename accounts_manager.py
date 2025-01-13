from pyrogram import Client
from utils.config import Config


async def main():
    index = 0
    while True:
        tg = Client(f"account_{index}", api_id=Config.telegram_api.id, api_hash=Config.telegram_api.hash, in_memory=True)
        await tg.start()
        print(await tg.export_session_string())
        await tg.stop()
        
        
        
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
        