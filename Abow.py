import os
os.system('pip install telebot')
import telebot
import threading
import time
import socket
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== LOG SUSTUR =====
logging.getLogger("telebot").setLevel(logging.CRITICAL)

TOKEN = "8108298669:AAFj8TYRNS02HQBtYtl9aMM-SNCnLFBYgWs"
bot = telebot.TeleBot(TOKEN, threaded=True)

# ===== YETKİLİ =====
YETKILI_ID = 7181611360

KANALLAR = [-1002525145466, -1002993493265, -1003006686143, -1003672049233]
# ===== ANAHTAR KELİMELER (SADECE FORWARD) =====
ANAHTAR_KELIMELER = [
    "çalma", "sorgu", "panel", "klasör",
    "@klosorcu", "@crazysaplar", "@azedestekhat",
    "@tassaklireal", "instagram", "free",
    "kanal", "botlar", "ss", "bot", "kanallarda",
    "sxrgu", "𝙄𝙉𝙎𝙏𝘼𝙂𝙍𝘼𝙈"
]

# ===== ÖZEL CÜMLELER (SADECE NORMAL MESAJ) =====
OZEL_SUPHELI_CUMLELER = [
    "herkese 5 hesap çalma hakkı verildi süresi dolmadan kullanın!",
    "herkese 3 hesap çalma hakkı verildi!"
    "hesap çalma hakkı verildi!"
    "hesap çalma hakkı verildi"
]

# ===== AKTİF SİLME İŞLERİ =====
silme_isleri = {}  # message_id: cancel_flag

# ===== İNTERNET =====
def internet_var_mi():
    try:
        socket.create_connection(("api.telegram.org", 443), timeout=5)
        return True
    except:
        return False

# ===== YETKİLİYE BİLDİR =====
def yetkiliye_bildir(text, reply_markup=None):
    try:
        bot.send_message(
            YETKILI_ID,
            text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except:
        pass

# ===== 15 DK SONRA SİL =====
def gecikmeli_sil(chat_id, message_id):
    for _ in range(15 * 60):
        if silme_isleri.get(message_id) is False:
            return
        time.sleep(1)

    try:
        bot.delete_message(chat_id, message_id)
        yetkiliye_bildir(
            f"🗑️ **ŞÜPHELİ MESAJ SİLİNDİ**\n\n"
            f"📌 Kanal ID: `{chat_id}`\n"
            f"🆔 Mesaj ID: `{message_id}`"
        )
    except:
        pass

# ===== MESAJ KONTROL =====
def mesaj_kontrol(m):
    if m.chat.id not in KANALLAR:
        return

    icerik = ""

    if getattr(m, "text", None):
        icerik += m.text.lower()
    if getattr(m, "caption", None):
        icerik += m.caption.lower()
    if m.document and m.document.file_name:
        icerik += m.document.file_name.lower()

    # ===== FORWARD MI? =====
    is_forward = bool(m.forward_from or m.forward_from_chat or m.forward_date)

    supheli = False

    # 🔴 ANAHTAR KELİME → SADECE FORWARD
    if is_forward and any(k in icerik for k in ANAHTAR_KELIMELER):
        supheli = True

    # 🔴 ÖZEL CÜMLELER → SADECE NORMAL
    if not is_forward and any(c in icerik for c in OZEL_SUPHELI_CUMLELER):
        supheli = True

    if not supheli:
        return

    silme_isleri[m.message_id] = True

    threading.Thread(
        target=gecikmeli_sil,
        args=(m.chat.id, m.message_id),
        daemon=True
    ).start()

    link = f"https://t.me/c/{str(m.chat.id)[4:]}/{m.message_id}"

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "✅ Bu şüpheli bir mesaj değil",
            callback_data=f"iptal_{m.message_id}"
        )
    )

    yetkiliye_bildir(
        f"⚠️ **ŞÜPHELİ MESAJ TESPİT EDİLDİ**\n\n"
        f"🔗 [Mesaja Git]({link})\n\n"
        f"⏳ 15 dk sonra silinecek",
        reply_markup=markup
    )

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("iptal_"))
def iptal_handler(call):
    if call.from_user.id != YETKILI_ID:
        bot.answer_callback_query(call.id, "❌ Yetkin yok")
        return

    msg_id = int(call.data.split("_")[1])
    silme_isleri[msg_id] = False

    bot.answer_callback_query(call.id, "✅ Silme işlemi iptal edildi")
    bot.edit_message_text(
        "🟢 **Admin onayı verildi**\n\nBu mesaj artık silinmeyecek.",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

# ===== KANAL =====
@bot.channel_post_handler(content_types=["text", "photo", "document", "video", "audio"])
def kanal_handler(m):
    mesaj_kontrol(m)

# ===== ÖZEL MESAJ =====
@bot.message_handler(func=lambda m: m.chat.type == "private")
def ozel(m):
    if m.from_user.id != YETKILI_ID:
        bot.reply_to(m, "⛔ Bu botu kullanmak için yetkiniz yok.")
    else:
        bot.reply_to(m, "✅ Yetkili erişim aktif.")

# ===== LOOP =====
while True:
    if not internet_var_mi():
        time.sleep(5)
        continue
    try:
        bot.polling(none_stop=True)
    except:
        time.sleep(5)
