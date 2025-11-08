import telebot
from telebot import types
import instaloader
from moviepy.editor import VideoFileClip
import os
import json
import uuid
import shutil

# === Sozlamalar ===
BOT_TOKEN = "8227305565:AAF2YNVBV7fHHeou_eBvwiOjrQFt10hiIgo"
ADMIN_ID = 7318264933
USERS_FILE = "venv/users.json"
CHANNELS_FILE = "channels.json"
ADMIN_DATA_FILE = "admin_data.json"

bot = telebot.TeleBot(BOT_TOKEN)

loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False
)

video_file = None
folder_name = None

# === Foydalanuvchilar ===
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)

# === Kanal ro'yxati ===
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            return json.load(f)
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=2)

# === Admin ma'lumotlari ===
def load_admin_data():
    if os.path.exists(ADMIN_DATA_FILE):
        with open(ADMIN_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_admin_data(data):
    with open(ADMIN_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === Menyular ===
def main_user_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📩 Adminga xabar yuborish", "ℹ️ Admin haqida")
    bot.send_message(chat_id, "Assalomu Alaykum .Instagram linkini yuboring yoki pastdagi tugmalardan foydalaning 👇", reply_markup=markup)

def main_admin_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Xabar yuborish")
    markup.add("👤 Admin ma'lumotlari", "📡 Kanal sozlamalari")
    bot.send_message(chat_id, "🔧 Admin panelga xush kelibsiz!", reply_markup=markup)

# === /start komandasi ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    users = load_users()

    # Yangi foydalanuvchi uchun "xush kelibsiz" xabar
    if user_id not in users:
        save_user(user_id)
        welcome_text = (
            "🏝Xуш келибсиз!🇺🇿🇺🇿🇺🇿\n"
            "📥Bu bot orqali oson vidoelarni yuklab oling\n"
            "📥Teskor xizmat\n"
            "🧭Ish vaqti 24 соат\n"
            "🔗 t.me/ibrat_videolar_o1"
        )

        # Xush kelibsiz xabarini yuboramiz
        bot.send_message(user_id, welcome_text)
    else:
        save_user(user_id)

    # Admin yoki oddiy foydalanuvchi menyusi
    if user_id == ADMIN_ID:
        main_admin_menu(user_id)
    else:
        main_user_menu(user_id)

# === Tugma handler ===
@bot.message_handler(func=lambda m: True)
def handler(message):
    if message.chat.id == ADMIN_ID:
        admin_buttons(message)
    else:
        normal_user_buttons(message)

# === Foydalanuvchi funksiyalari ===
def normal_user_buttons(message):
    text = message.text

    if text == "📩 Adminga xabar yuborish":
        msg = bot.send_message(message.chat.id, "✏️ Adminga yuboriladigan xabarni kiriting:")
        bot.register_next_step_handler(msg, send_to_admin)
        return

    elif text == "ℹ️ Admin haqida":
        bot.send_message(message.chat.id,
                         "👤 Admin: Mahammadov Nodirjon\n"
                         "🏫 TATU FF 2-KURS\n"
                         "📢 Kanal: @ibrat_videolar_o1\n"
                         "📞 Kontakt: @Mahammadov_o1o")
        return

    elif text.startswith("http"):
        check_subscription_and_download(message)
        return

# === Majburiy obuna tekshiruvi ===
def check_subscription(user_id):
    channels = load_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            member = bot.get_chat_member(f"@{ch}", user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def check_subscription_and_download(message):
    user_id = message.chat.id
    if check_subscription(user_id):
        send_instagram_video(message)
    else:
        send_subscription_message(user_id)

def send_subscription_message(chat_id):
    channels = load_channels()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
        markup.add(types.InlineKeyboardButton(f"📢 @{ch}", url=f"https://t.me/{ch}"))
    markup.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subs"))
    bot.send_message(
        chat_id,
        "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling 👇",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subs(call):
    user_id = call.message.chat.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!", show_alert=True)
        bot.send_message(user_id, "🎉 Rahmat! Endi botdan foydalanishingiz mumkin.")
        main_user_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "🚫 Siz hali barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)
        send_subscription_message(user_id)

# === Adminga xabar yuborish ===
def send_to_admin(message):
    try:
        bot.send_message(ADMIN_ID, f"📩 Yangi xabar:\n\n{message.text}\n\nFoydalanuvchi ID: {message.chat.id}")
        bot.send_message(message.chat.id, "✅ Xabaringiz adminga yuborildi.")
    except:
        bot.send_message(message.chat.id, "❌ Xabar yuborishda xatolik.")
    main_user_menu(message.chat.id)

# === Instagram yuklash ===
def send_instagram_video(message):
    global video_file, folder_name
    url = message.text.strip()
    bot_msg = bot.send_message(message.chat.id, "⏳ Biroz kuting...")

    try:
        shortcode = url.split("/")[-2]
        folder_name = shortcode
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)

        video_file = None
        for file in os.listdir(shortcode):
            if file.endswith(".mp4"):
                video_file = os.path.join(shortcode, file)
                break

        if video_file:
            with open(video_file, "rb") as video:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🎧 Audioni yuklab olish", callback_data="get_audio"))
                bot.send_video(message.chat.id, video, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Video topilmadi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Xatolik: {e}")
    finally:
        bot.delete_message(message.chat.id, bot_msg.message_id)
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name, ignore_errors=True)

# === Audio yuklash ===
@bot.callback_query_handler(func=lambda call: call.data == "get_audio")
def get_audio(call):
    global video_file
    try:
        bot.send_message(call.message.chat.id, "🎵 Audio tayyorlanmoqda...")
        video = VideoFileClip(video_file)
        audio = video.audio
        audio_name = f"{uuid.uuid4()}.mp3"
        audio.write_audiofile(audio_name)
        with open(audio_name, "rb") as f:
            bot.send_audio(call.message.chat.id, f)
        video.close()
        os.remove(audio_name)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Audio yuklashda xatolik: {e}")

# === Admin funksiyalari ===
def admin_buttons(message):
    text = message.text

    if text == "📊 Statistika":
        users = load_users()
        bot.send_message(message.chat.id, f"👥 Foydalanuvchilar soni: {len(users)+34} ta")

    elif text == "📢 Xabar yuborish":
        msg = bot.send_message(message.chat.id, "✏️ Yuboriladigan xabarni yozing:")
        bot.register_next_step_handler(msg, broadcast_message)

    elif text == "👤 Admin ma'lumotlari":
        admin_data = load_admin_data()
        if not admin_data:
            msg = bot.send_message(message.chat.id, "Ism, kontakt, kanal manzilini yuboring:")
            bot.register_next_step_handler(msg, save_new_admin_data)
        else:
            bot.send_message(message.chat.id, f"📄 Admin ma'lumotlari:\n{json.dumps(admin_data, indent=2)}")

    elif text == "📡 Kanal sozlamalari":
        channels = load_channels()
        kanal_text = "\n".join([f"📢 @{ch}" for ch in channels]) if channels else "🚫 Hozircha kanal yo‘q."
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Obuna qo‘shish", "🗑 Kanalni o‘chirish")
        markup.add("🔙 Orqaga")
        bot.send_message(message.chat.id, f"📡 Majburiy kanallar:\n\n{kanal_text}", reply_markup=markup)

    elif text == "➕ Obuna qo‘shish":
        msg = bot.send_message(message.chat.id, "Yangi kanal username (masalan, @kanal_nomi) yuboring:")
        bot.register_next_step_handler(msg, add_channel)

    elif text == "🗑 Kanalni o‘chirish":
        channels = load_channels()
        if channels:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for ch in channels:
                markup.add(f"❌ @{ch}")
            markup.add("🔙 Orqaga")
            msg = bot.send_message(message.chat.id, "O‘chiriladigan kanalni tanlang:", reply_markup=markup)
            bot.register_next_step_handler(msg, remove_channel)
        else:
            bot.send_message(message.chat.id, "🚫 Ro‘yxatda kanal yo‘q.")

    elif text == "🔙 Orqaga":
        main_admin_menu(message.chat.id)

def remove_channel(message):
    ch_name = message.text.replace("❌ @", "").strip()
    channels = load_channels()
    if ch_name in channels:
        channels.remove(ch_name)
        save_channels(channels)
        bot.send_message(message.chat.id, f"✅ @{ch_name} kanali ro‘yxatdan o‘chirildi.")
    else:
        bot.send_message(message.chat.id, "⚠️ Bunday kanal topilmadi.")
    main_admin_menu(message.chat.id)

def broadcast_message(message):
    users = load_users()
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ {count} ta foydalanuvchiga yuborildi.")

def save_new_admin_data(message):
    data = {"info": message.text}
    save_admin_data(data)
    bot.send_message(message.chat.id, "✅ Ma'lumotlar saqlandi.")

def add_channel(message):
    channels = load_channels()
    new_channel = message.text.strip().replace("@", "")
    if new_channel not in channels:
        channels.append(new_channel)
        save_channels(channels)
        bot.send_message(message.chat.id, f"✅ @{new_channel} kanali qo‘shildi.")
    else:
        bot.send_message(message.chat.id, "⚠️ Bu kanal allaqachon ro‘yxatda bor.")
    main_admin_menu(message.chat.id)

print("✅ Bot ishga tushdi!")
bot.infinity_polling()
