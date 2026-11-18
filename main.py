import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.constants import ChatMemberStatus

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام عزیزم ❤️\n"
        "به ربات مدیریت گروه خوش آمدی.\n\n"
        "برای دیدن امکانات دستور /help را بزن."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 راهنمای ربات:\n\n"
        "/start - شروع ربات\n"
        "/help - راهنما\n"
        "/ping - بررسی فعالیت ربات\n"
        "/id - دریافت شناسه گروه و کاربر\n"
        "/rules - قوانین گروه\n"
        "/ban - مسدود کردن کاربر (با ریپلای)\n"
        "/unban - رفع مسدودی کاربر\n"
        "/kick - اخراج کاربر (با ریپلای)\n"
        "/mute - سکوت کاربر (با ریپلای)\n"
        "/unmute - رفع سکوت کاربر\n"
        "/pin - سنجاق پیام (با ریپلای)\n"
        "/del - حذف پیام (با ریپلای)"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات فعال است ✅")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"شناسه گروه: {update.effective_chat.id}\n"
        f"شناسه شما: {update.effective_user.id}"
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 قوانین گروه:\n\n"
        "۱. احترام به همه اعضا\n"
        "۲. ارسال نکردن پیام‌های تبلیغاتی\n"
        "۳. پرهیز از توهین و بی‌احترامی\n"
        "۴. رعایت نظم گروه ❤️"
    )

async def is_admin(update, context):
    user = update.effective_user
    member = await context.bot.get_chat_member(
        update.effective_chat.id, user.id
    )
    return member.status in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    ]

async def moderation(update, context, action):
    message = update.message
    if not await is_admin(update, context):
        await message.reply_text("❌ فقط مدیران اجازه دارند.")
        return

    if not message.reply_to_message:
        await message.reply_text("روی پیام کاربر ریپلای کن.")
        return

    user = message.reply_to_message.from_user
    chat = update.effective_chat.id

    if action == "ban":
        await context.bot.ban_chat_member(chat, user.id)
    elif action == "kick":
        await context.bot.ban_chat_member(chat, user.id)
        await context.bot.unban_chat_member(chat, user.id)
    elif action == "mute":
        await context.bot.restrict_chat_member(
            chat, user.id,
            permissions={
                "can_send_messages": False,
                "can_send_audios": False,
                "can_send_documents": False,
                "can_send_photos": False,
                "can_send_videos": False,
                "can_send_polls": False,
                "can_send_other_messages": False
            }
        )
    elif action == "unmute":
        await context.bot.restrict_chat_member(
            chat, user.id,
            permissions={
                "can_send_messages": True,
                "can_send_audios": True,
                "can_send_documents": True,
                "can_send_photos": True,
                "can_send_videos": True,
                "can_send_polls": True,
                "can_send_other_messages": True
            }
        )

    await message.reply_text("✅ عملیات انجام شد.")

async def ban(u, c):
    await moderation(u, c, "ban")

async def kick(u, c):
    await moderation(u, c, "kick")

async def mute(u, c):
    await moderation(u, c, "mute")

async def unmute(u, c):
    await moderation(u, c, "unmute")

async def pin(update, context):
    if await is_admin(update, context):
        if update.message.reply_to_message:
            await update.message.reply_to_message.pin()
            await update.message.reply_text("📌 پیام سنجاق شد.")
    else:
        await update.message.reply_text("❌ فقط مدیران اجازه دارند.")

async def delete(update, context):
    if await is_admin(update, context):
        if update.message.reply_to_message:
            await update.message.reply_to_message.delete()
            await update.message.delete()
    else:
        await update.message.reply_text("❌ فقط مدیران اجازه دارند.")

async def welcome(update, context):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"خوش آمدی {member.first_name} عزیز ❤️\n"
            "به گروه ما خوش آمدی."
        )

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("del", delete))
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome)
    )

    app.run_polling()

if __name__ == "__main__":
    main()
