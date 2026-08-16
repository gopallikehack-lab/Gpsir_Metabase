#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Premium Metadata Extractor Bot v3.0
Developer: @GpsirEra
"""

import os
import json
import tempfile
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.metadata import extract_metadata, parse_metadata_to_readable

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "8932695749"))
BOT_USERNAME = os.getenv("BOT_USERNAME", "Gpsir_Metadata_Bot")
DEVELOPER = "@GpsirEra"
CHANNEL = "@GpsirEra"

# ========== PREMIUM EMOJI IDs ==========
PREMIUM_EMOJI = {
    "fire": "5424972470023104089",
    "check": "5206607081334906820",
    "cross": "5210952531676504517",
    "info": "5323442290708985472",
    "rocket": "5447410659077661506",
    "stats": "5231200819986047254",
    "like": "5337080053119336309",
    "play": "5348125953090403204",
    "bell": "5458603043203327669",
    "warning": "5447644880824181073",
}

def pe(key: str, fallback: str = "•") -> str:
    emoji_id = PREMIUM_EMOJI.get(key, "")
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# ========== HELPERS ==========
def format_metadata(data: dict) -> str:
    """Format metadata for Telegram message"""
    summary = data.get('summary', {})
    categories = data.get('categories', {})
    
    text = f"{pe('fire')} <b>METADATA EXTRACTED</b> {pe('fire')}\n\n"
    
    # Summary
    text += f"{pe('info')} <b>Quick Summary</b>\n"
    for key, value in summary.items():
        if value:
            label = key.replace('FileName', '📄 File').replace('Make', '📷 Brand').replace('Model', '📸 Model')
            text += f"• {label}: <code>{value}</code>\n"
    
    # GPS
    if data.get('gps'):
        text += f"\n🌍 <b>GPS:</b> <code>{data['gps']}</code>\n"
    
    # Categories
    text += f"\n{pe('stats')} <b>Details</b>\n"
    for cat_name, cat_data in categories.items():
        icon = cat_data.get('icon', '📌')
        items = cat_data.get('data', {})
        if items:
            text += f"\n{icon} <b>{cat_name}</b>\n"
            for key, value in list(items.items())[:5]:  # Limit per category
                label = key.replace('GPS', 'GPS ').replace('DateTimeOriginal', '📅 Date')
                text += f"• {label}: <code>{value}</code>\n"
            if len(items) > 5:
                text += f"• ... aur {len(items) - 5} aur\n"
    
    text += f"\n{pe('like')} <i>Full details in JSON</i>"
    return text

# ========== BOT HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton(f"{pe('rocket')} Upload Image", callback_data="upload")],
        [InlineKeyboardButton(f"{pe('stats')} About", callback_data="about")],
        [InlineKeyboardButton(f"{pe('like')} Channel", url="https://t.me/GpsirEra")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
{pe('fire')} <b>PREMIUM METADATA EXTRACTOR</b> {pe('fire')}

📸 Send me an image — I'll extract every hidden detail!

{pe('info')} <b>What I Can Do:</b>
• Camera info (Make, Model, Lens)
• GPS location (if present)
• EXIF, IPTC, XMP data
• Image properties
• Date/Time info

👨‍💻 <b>Developer:</b> {DEVELOPER}
📢 <b>Channel:</b> {CHANNEL}

⚡ <i>Just send any image file!</i>
"""
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""
{pe('info')} <b>About This Bot</b>

📸 <b>Premium Metadata Extractor</b>
Version: 3.0

<i>Extracts all hidden metadata from images including:</i>
• Camera settings (ISO, aperture, shutter)
• GPS coordinates with map link
• File information
• Author & copyright details
• EXIF/IPTC/XMP data

👨‍💻 <b>Developer:</b> {DEVELOPER}
📢 <b>Channel:</b> {CHANNEL}

⚡ <i>Powered by ExifTool</i>
"""
    await update.message.reply_text(text, parse_mode='HTML')

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    
    # Get file
    if msg.photo:
        file_obj = msg.photo[-1]
        ext = 'jpg'
    elif msg.document:
        file_obj = msg.document
        ext = file_obj.file_name.split('.')[-1] if file_obj.file_name else 'bin'
    else:
        await msg.reply_text("❌ Please send an image file.")
        return
    
    # Check if image
    allowed = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'heic', 'heif', 'raw', 'cr2', 'nef', 'arw', 'orf'}
    if ext.lower() not in allowed:
        await msg.reply_text(f"❌ Unsupported file: .{ext}\nSend JPG, PNG, GIF, WEBP, or RAW.")
        return
    
    progress = await msg.reply_text(f"{pe('rocket')} <b>Processing...</b>\nDownloading and extracting metadata...", parse_mode='HTML')
    
    try:
        # Download file
        file = await file_obj.get_file()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
            await file.download_to_drive(tmp.name)
            tmp_path = tmp.name
        
        # Extract metadata
        result = extract_metadata(tmp_path)
        if 'error' in result:
            await progress.edit_text(f"❌ Error: {result['error']}")
            os.unlink(tmp_path)
            return
        
        # Parse
        friendly = parse_metadata_to_readable(result['metadata'])
        
        # Format message
        text = format_metadata(friendly)
        
        # Keyboard
        keyboard = [
            [InlineKeyboardButton(f"{pe('check')} Full JSON", callback_data=f"json_{tmp_path}")],
            [InlineKeyboardButton(f"{pe('like')} Download JSON", callback_data=f"download_{tmp_path}")],
            [InlineKeyboardButton(f"{pe('stats')} Raw Data", callback_data=f"raw_{tmp_path}")],
            [InlineKeyboardButton("🌍 Open GPS", callback_data=f"gps_{friendly.get('gps', '')}") if friendly.get('gps') else None],
        ]
        keyboard = [k for k in keyboard if k is not None]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Store data in context
        context.user_data['last_data'] = friendly
        context.user_data['last_path'] = tmp_path
        
        await progress.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        await progress.edit_text(f"❌ Error: {str(e)}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data
    
    if data == "upload":
        await query.edit_message_text("📤 <b>Send me an image file!</b>\n\nJust upload or forward any photo.", parse_mode='HTML')
    
    elif data == "about":
        await about(update, context)
    
    elif data.startswith("json_"):
        path = data.replace("json_", "")
        if 'last_data' in user_data:
            json_str = json.dumps(user_data['last_data'].get('all_raw', {}), indent=2)
            # Truncate if too long
            if len(json_str) > 4000:
                json_str = json_str[:3500] + "\n... (truncated)"
            await query.message.reply_text(f"<pre>{json_str}</pre>", parse_mode='HTML')
    
    elif data.startswith("download_"):
        path = data.replace("download_", "")
        if 'last_data' in user_data:
            json_bytes = json.dumps(user_data['last_data'].get('all_raw', {}), indent=2).encode()
            await query.message.reply_document(
                document=json_bytes,
                filename=f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
    
    elif data.startswith("gps_"):
        gps = data.replace("gps_", "")
        if gps:
            await query.message.reply_text(f"🌍 <b>GPS Location</b>\n\n<code>{gps}</code>\n\n🔗 <a href='https://www.google.com/maps?q={gps}'>Open in Google Maps</a>", parse_mode='HTML')
        else:
            await query.message.reply_text("❌ No GPS data found.")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    # Stats placeholder
    stats = {
        "users": "N/A",
        "files": "N/A",
        "uptime": "N/A"
    }
    text = f"""
📊 <b>Admin Stats</b>

👤 Users: {stats['users']}
📁 Files: {stats['files']}
⏰ Uptime: {stats['uptime']}

👨‍💻 Developer: {DEVELOPER}
"""
    await update.message.reply_text(text, parse_mode='HTML')

# ========== MAIN ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("stats", admin_stats))
    
    # File handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_image))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print(f"🔥 {BOT_USERNAME} is running...")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    app.run_polling()

if __name__ == "__main__":
    main()
