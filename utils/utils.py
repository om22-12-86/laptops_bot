from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

CHANNEL_ID = -xxxxxxx  # ID твоего канала

async def is_admin(bot: Bot, user_id: int) -> bool:
    """Проверяет, является ли пользователь админом канала."""
    try:
        admins = await bot.get_chat_administrators(CHANNEL_ID)
        admin_ids = {admin.user.id for admin in admins if isinstance(admin, (ChatMemberAdministrator, ChatMemberOwner))}
        return user_id in admin_ids
    except Exception as e:
        print(f"Ошибка при проверке админа: {e}")
        return False