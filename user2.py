from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, \
    ConversationHandler, ContextTypes
import sqlite3

FIRST_NAME, LAST_NAME, EXAM_NAME, EXAM_COUNT,EXAM_TIME, QUESTION_TEXT, CASE1, CASE2, CASE3, CASE4, ANSWER,SEECREATEDEXAM ,IMAGE = range(13)
from exam2 import load_exam
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['first_name'] = update.message.text
    context.user_data['last_name']=''
    await update.message.reply_text(f" {update.message.text} جان🥰 لطفا کد ملیت رو (به فارسی)  بهم بگو  تا ازمونو شروع کنیم☺. ")
    return LAST_NAME



async def set_nationalcode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['national_code'] = update.message.text
    if update.message.from_user.username:
        username = update.message.from_user.username


    else: username = update.message.from_user.full_name if update.message.from_user.full_name else update.message.from_user.id

    tel_id = update.message.from_user.id
    # Check if user exists and insert if not
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('SELECT id FROM user WHERE tel_id = ?',
              (tel_id, ))
    user = c.fetchone()

    if user is None:
        c.execute('INSERT INTO user (firstname, lastname,national_code,tel_id ,username) VALUES (?, ?,?,?,?)',
                  (context.user_data['first_name'],'', context.user_data['national_code'],tel_id,username))
        context.user_data['user_id'] = c.lastrowid
        conn.commit()
    else:
        c.execute('UPDATE user SET firstname = ?, lastname = ?, national_code = ?, tel_id = ?, username = ? WHERE tel_id = ?',
                  (context.user_data['first_name'], '',context.user_data['national_code'], tel_id, username, tel_id))
        conn.commit()
        context.user_data['user_id'] = user[0]

    conn.close()
    context.user_data['falsee']=0
    context.user_data['nulll'] = 0
    context.user_data['correct'] = 0
    context.user_data['percentt'] = 0
    await update.message.reply_text("بریم که بترکونیم 💪✌😎")
    await load_exam(update, context)
    return ConversationHandler.END


