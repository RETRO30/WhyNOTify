from database.models import Account, AccountStatus, Channel, ChannelType

async def main_menu_text():
    count_accounts = await Account.get_total_count()
    text = f"Total accounts: {count_accounts}\n"
    for status in AccountStatus:
        count = await Account.get_count_by_status(status)
        text += f"{status.name}: {count}\n"
    
    count_channels = await Channel.get_total_count()
    text += f"\nTotal channels: {count_channels}\n"
    for channel_type in ChannelType:
        count = await Channel.get_count_by_type(channel_type)
        text += f"{channel_type.name}: {count}\n"
    return text