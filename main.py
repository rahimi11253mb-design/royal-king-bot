
import os
import re
import logging
from datetime import datetime, timedelta, timezone

from telegram import (
    Update,
    ChatPermissions,
    ReplyKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📋 راهنما", "📜 قوانین"],
        ["🆔 شناسه من", "👥 تعداد اعضا"],
        ["💚 وضعیت ربات", "📖 راهنمای مدیریت"],
    ],
    resize_keyboard=True,
)

DEFAULT_RULES = (
    "📜 قوانین گروه ROYAL KING\n\n"
    "1️⃣ احترام به اعضا الزامی است.\n"
    "2️⃣ تبلیغات و لینک ممنوع است.\n"
    "3️⃣ فحاشی و توهین ممنوع است.\n"
    "4️⃣ پیام تکراری ممنوع است.\n"
    "5️⃣ رعایت دستورات مدیران الزامی است."
)

BAD_WORDS = [
    "کثافت",
    "حرامزاده",
    "بی‌شعور",
]

LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|bit\.ly/|instagram\.com/)",
    re.IGNORECASE,
)

WARNINGS = {}


def is_admin(member):
    return member.status in ("creator", "administrator")


async def admin_check(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )
    if not is_admin(member):
        await update.effective_message.reply_text(
            "⛔ فقط مدیران اجازه اجرای این دستور را دارند."
        )
        return False
    return True


async def bot_admin_check(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        context.bot.id,
    )
    if not is_admin(member):
        await update.effective_message.reply_text(
            "⚠️ ابتدا ربات را مدیر گروه کن."
        )
        return False
    return True


async def start(update, context):
    await update.message.reply_text(
        "👑 سلام! به ربات مدیریت ROYAL KING خوش آمدی.\n"
        "برای استفاده از امکانات، دکمه‌های فارسی را انتخاب کن.",
        reply_markup=KEYBOARD,
    )


async def help_command(update, context):
    await update.message.reply_text(
        "📋 راهنمای ROYAL KING\n\n"
        "/start - شروع\n"
        "/help - راهنما\n"
        "/rules - قوانین\n"
        "/id - شناسه\n"
        "/members - تعداد اعضا\n"
        "/status - وضعیت ربات\n\n"
        "دستورات مدیریت (روی پیام عضو پاسخ بده):\n"
        "/warn - اخطار\n"
        "/warnings - تعداد اخطار\n"
        "/mute - سکوت ۱۰ دقیقه‌ای\n"
        "/unmute - رفع سکوت\n"
        "/ban - مسدودسازی\n"
        "/kick - اخراج\n"
        "/del - حذف پیام\n"
        "/pin - سنجاق پیام\n"
        "/setrules متن - تغییر قوانین"
    )


async def rules(update, context):
    await update.message.reply_text(
        context.chat_data.get("rules", DEFAULT_RULES)
    )


async def setrules(update, context):
    if not await admin_check(update, context):
        return

    new_rules = " ".join(context.args).strip()
    if not new_rules:
        await update.message.reply_text(
            "نمونه: /setrules احترام به همه اعضا الزامی است"
        )
        return

    context.chat_data["rules"] = (
        "📜 قوانین گروه ROYAL KING\n\n" + new_rules
    )
    await update.message.reply_text("✅ قوانین تغییر کرد.")


async def get_id(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 شناسه شما: {user.id}\nنام: {user.full_name}"
    )


async def members(update, context):
    count = await context.bot.get_chat_member_count(
        update.effective_chat.id
    )
    await update.message.reply_text(
        f"👥 تعداد اعضا: {count}"
    )


async def status(update, context):
    await update.message.reply_text(
        "💚 ربات ROYAL KING فعال است."
    )


async def get_target(update):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    await update.message.reply_text(
        "⚠️ برای این دستور روی پیام عضو پاسخ بده."
    )
    return None

async def warn(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    target = await get_target(update)
    if not target or target.is_bot:
        return

    key = (update.effective_chat.id, target.id)
    WARNINGS[key] = WARNINGS.get(key, 0) + 1
    count = WARNINGS[key]

    await update.message.reply_text(
        f"⚠️ به {target.full_name} اخطار داده شد: {count}/3"
    )

    if count >= 3:
        until = datetime.now(timezone.utc) + timedelta(minutes=10)
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        WARNINGS[key] = 0
        await update.message.reply_text(
            f"🔇 {target.full_name} برای ۱۰ دقیقه سکوت شد."
        )


async def warnings(update, context):
    if not await admin_check(update, context):
        return

    target = await get_target(update)
    if not target:
        return

    count = WARNINGS.get(
        (update.effective_chat.id, target.id), 0
    )
    await update.message.reply_text(
        f"⚠️ تعداد اخطارهای {target.full_name}: {count}"
    )


async def mute(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    target = await get_target(update)
    if not target or target.is_bot:
        return

    until = datetime.now(timezone.utc) + timedelta(minutes=10)

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        ChatPermissions(can_send_messages=False),
        until_date=until,
    )

    await update.message.reply_text(
        f"🔇 {target.full_name} برای ۱۰ دقیقه سکوت شد."
    )


async def unmute(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    target = await get_target(update)
    if not target:
        return

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        ),
    )

    await update.message.reply_text(
        f"🔊 سکوت {target.full_name} برداشته شد."
    )


async def ban(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    target = await get_target(update)
    if not target or target.is_bot:
        return

    await context.bot.ban_chat_member(
        update.effective_chat.id,
        target.id,
    )
    await update.message.reply_text(
        f"🚫 {target.full_name} مسدود شد."
    )


async def kick(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    target = await get_target(update)
    if not target or target.is_bot:
        return

    chat_id = update.effective_chat.id

    await context.bot.ban_chat_member(chat_id, target.id)
    await context.bot.unban_chat_member(
        chat_id,
        target.id,
        only_if_banned=True,
    )

    await update.message.reply_text(
        f"👢 {target.full_name} از گروه اخراج شد."
    )


async def delete_message(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "روی پیام موردنظر پاسخ بده."
        )
        return

    await update.message.reply_to_message.delete()
    await update.message.reply_text("🗑 پیام حذف شد.")


async def pin_message(update, context):
    if not await admin_check(update, context):
        return
    if not await bot_admin_check(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "روی پیام موردنظر پاسخ بده."
        )
        return

    await update.message.reply_to_message.pin()
    await update.message.reply_text("📌 پیام سنجاق شد.")


async def welcome(update, context):
    for user in update.message.new_chat_members:
        if user.id == context.bot.id:
            continue

        await update.message.reply_text(
            f"🌹 خوش آمدی {user.full_name} عزیز!\n"
            "به گروه ROYAL KING خوش آمدی.\n"
            "لطفاً قوانین گروه را رعایت کن. ❤️"
        )


async def check_messages(update, context):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not message.text:
        return

    try:
        member = await context.bot.get_chat_member(
            chat.id, user.id
        )
        if is_admin(member):
            return
    except Exception:
        log.exception("بررسی مدیر ناموفق بود")
        return

    text = message.text.lower()
    has_link = bool(LINK_PATTERN.search(text))
    has_bad_word = any(word in text for word in BAD_WORDS)

    if not (has_link or has_bad_word):
        return

    try:
        await message.delete()

        reason = (
            "ارسال لینک یا تبلیغات"
            if has_link else "استفاده از کلمات نامناسب"
        )

        key = (chat.id, user.id)
        WARNINGS[key] = WARNINGS.get(key, 0) + 1
        count = WARNINGS[key]

        await context.bot.send_message(
            chat.id,
            f"⚠️ {user.full_name}\n"
            f"پیام به دلیل {reason} حذف شد.\n"
            f"اخطار: {count}/3"
        )

        if count >= 3:
            until = datetime.now(timezone.utc) + timedelta(minutes=10)

            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                ChatPermissions(can_send_messages=False),
                until_date=until,
            )

            WARNINGS[key] = 0

            await context.bot.send_message(
                chat.id,
                f"🔇 {user.full_name} به دلیل سه اخطار "
                "برای ۱۰ دقیقه سکوت شد."
            )

    except Exception:
        log.exception("خطا در بررسی پیام")


async def keyboard_buttons(update, context):
    text = update.message.text

    if text == "📋 راهنما":
        await help_command(update, context)
    elif text == "📜 قوانین":
        await rules(update, context)
    elif text == "🆔 شناسه من":
        await get_id(update, context)
    elif text == "👥 تعداد اعضا":
        await members(update, context)
    elif text == "💚 وضعیت ربات":
        await status(update, context)
    elif text == "📖 راهنمای مدیریت":
        await help_command(update, context)


async def post_init(application):
    commands = [
        BotCommand("start", "شروع ربات"),
        BotCommand("help", "راهنمای فارسی"),
        BotCommand("rules", "قوانین گروه"),
        BotCommand("id", "شناسه من"),
        BotCommand("members", "تعداد اعضا"),
        BotCommand("status", "وضعیت ربات"),
        BotCommand("warn", "اخطار به عضو"),
        BotCommand("warnings", "مشاهده اخطارها"),
        BotCommand("mute", "سکوت عضو"),
        BotCommand("unmute", "رفع سکوت"),
        BotCommand("ban", "مسدود کردن عضو"),
        BotCommand("kick", "اخراج عضو"),
        BotCommand("del", "حذف پیام"),
        BotCommand("pin", "سنجاق پیام"),
        BotCommand("setrules", "تغییر قوانین"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    if not TOKEN:
        raise RuntimeError("متغیر BOT_TOKEN تنظیم نشده است.")

    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("members", members))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("warnings", warnings))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("del", delete_message))
    app.add_handler(CommandHandler("pin", pin_message))

    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            check_messages,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(
                r"^(📋 راهنما|📜 قوانین|🆔 شناسه من|"
                r"👥 تعداد اعضا|💚 وضعیت ربات|📖 راهنمای مدیریت)$"
            ),
            keyboard_buttons,
        )
    )

    log.info("ROYAL KING started")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
