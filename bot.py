from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from ultralytics import YOLO

import config as c
import geo
import store

PHOTOS = c.DATA / 'photos'
BUTTONS = [('Real forest fire', 'fire'), ('Nothing found', 'none'), ('Farm or village fire', 'farm'), ('Our controlled burn', 'burn')]
LABEL = {v: t for t, v in BUTTONS}
where = {}  # each user's last shared location, kept in memory (§11.3)
model = None


async def start(update, ctx):
    await update.message.reply_text(
        'AgniDrishti field reports.\n'
        '1. Share your location: tap the attachment icon, then Location.\n'
        '2. Send a photo of what you see.\n'
        '3. Tap what you found.\n'
        'Please use the location share: Telegram removes location from photos.')


async def location(update, ctx):
    loc = update.message.location
    where[update.effective_user.id] = (loc.latitude, loc.longitude)
    await update.message.reply_text('Location saved. Now send a photo.')


async def photo(update, ctx):
    PHOTOS.mkdir(parents=True, exist_ok=True)
    path = PHOTOS / f'{update.effective_user.id}_{update.message.message_id}.jpg'
    await (await update.message.photo[-1].get_file()).download_to_drive(path)
    r = model.predict(str(path), imgsz=640, conf=c.PHOTO_CONF, verbose=False)[0]
    seen = 'Smoke or fire seen' if len(r.boxes) else 'No smoke or fire seen'
    await update.message.reply_text(f'{seen}. What did you find?',
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=v)] for t, v in BUTTONS]))


def nearest(lat, lon):
    """The nearest non-LOG alert within BOT_RADIUS_KM, as (alert, km), else None."""
    df = store.load()
    df = df[df.tier != 'LOG'] if len(df) else df
    if df.empty:
        return None
    d = geo.km(lat, lon, df.latitude.values, df.longitude.values)
    i = int(d.argmin())
    return (df.iloc[i], float(d[i])) if d[i] <= c.BOT_RADIUS_KM else None


async def outcome(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.data not in LABEL:  # callback data comes from the client: accept only our four answers
        return
    pos = where.get(q.from_user.id)
    if not pos:
        await q.message.reply_text('Share your location first, then tap your answer again.')
        return
    hit = nearest(*pos)
    if hit is None:
        await q.message.reply_text(f'No DISPATCH or VERIFY alert within {c.BOT_RADIUS_KM} km of your location, so nothing was saved.')
        return
    a, dist = hit
    store.record(a['id'], 'field', q.data)
    await q.edit_message_text(f"Saved: {LABEL[q.data]} for alert {a['id']} ({dist:.1f} km from you). Thank you.")


def main():
    global model
    model = YOLO(c.PHOTO_MODEL)
    app = Application.builder().token(c.BOT_TOKEN).build()
    app.add_handler(CommandHandler(['start', 'help'], start))
    app.add_handler(MessageHandler(filters.LOCATION, location))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(CallbackQueryHandler(outcome))
    print('bot polling Telegram (only this process may poll this token)')
    app.run_polling()


if __name__ == '__main__':
    main()
