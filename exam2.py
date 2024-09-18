import asyncio
import os
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, \
    ConversationHandler, ContextTypes, CallbackContext
import sqlite3

FIRST_NAME, LAST_NAME, EXAM_NAME, EXAM_COUNT, EXAM_TIME, QUESTION_TEXT, CASE1, CASE2, CASE3, CASE4, ANSWER, SEECREATEDEXAM, IMAGE = range(
    13)
from question2 import send_next_question,correction


async def start_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # print("start exam ")
    if len(context.args) != 1:
        await update.message.reply_text("یک دنیا معذرت ولی این لینک ازمون معتبر نیست 😓 اصن ایدی نیومده سمتم که...")
        return ConversationHandler.END
    try:
        exam_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ایدی ازمون داده شده معتبر نیست🤔 اصن نمیتونم به عدد تبدیلش کنم  ")
        return ConversationHandler.END

    user_id = update.message.from_user.id

    # Check if the user has already participated in this exam
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()

    # Get user ID from user table  tel_id
    c.execute('SELECT id FROM user WHERE tel_id = ?', (user_id,))
    user = c.fetchone()

    if user:
        user_id_in_db = user[0]
        c.execute('SELECT id FROM result WHERE user_id = ? AND exam_id = ?', (user_id_in_db, exam_id))
        result = c.fetchone()

        if result:
            await update.message.reply_text("شما قبلا در این آزمون شرکت کرده‌اید و نمی‌توانید دوباره شرکت کنید.")
            conn.close()
            return ConversationHandler.END

    conn.close()

    context.user_data['exam_id'] = exam_id

    await update.message.reply_text("""
    سلام و درورد 🖐😁
    صفا اوردی🤩
    لطفا با حفظ خونسردی تمام و کمال نام و نام خانوادگیتو بهمون بگو🤗

    """)

    return FIRST_NAME



async def start_create_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        await update.message.reply_text("سلام و ارادت بر ادمین گرامی🤓 لطفا یک نام برای ازمون بده بیاد.")
        return EXAM_NAME
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END


async def set_exam_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    exam_name = update.message.text
    # Check if the exam already exists
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('SELECT id FROM exam WHERE name = ?', (exam_name,))
    if c.fetchone():
        await update.message.reply_text(
            "اقا داداش اینو نامو که قبلا برای یک ازمون دیگه انتخاب کردی 🙄. یک نام خاص و دلبر دیگه انتخاب کن.💎")
        conn.close()
        return EXAM_NAME
    else:

        context.user_data['exam_name'] = exam_name
        await update.message.reply_text("سلطان بگو ببینم کاربرا چقد تایم لازم دارن برای این ازمون ؟ (به ثانیه بگو)🙃")
        return EXAM_TIME


async def set_exam_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['exam_count'] = int(update.message.text)
    context.user_data['current_question'] = 1
    await update.message.reply_text(f"سوال 1:لطفا متن سوال رو بفرست.")
    return QUESTION_TEXT


async def set_exam_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    exam_name = context.user_data['exam_name']
    try:
        exam_time = int(update.message.text)
        context.user_data['exam_time'] = exam_time
    except:
        await update.message.reply_text("تایم وارد شده از نوع عددی نبود.. دوباره بفرست ")
        return EXAM_TIME
    # Check if the exam already exists
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()

    c.execute('INSERT INTO exam (name,time) VALUES (?,?)', (exam_name, exam_time))
    context.user_data['exam_id'] = c.lastrowid
    conn.commit()
    conn.close()

    await update.message.reply_text(" سوال میخوای برای ازمونت بدی بهمون ؟🙃")
    return EXAM_COUNT


async def list_exams(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('SELECT name, id FROM exam')
        exams = c.fetchall()
        conn.close()

        if not exams:
            await update.message.reply_text("دستم خالیه ستون آزمونی در بساط ندارم😟")
        else:
            keyboard = []
            for exam in exams:
                exam_name = exam[0]
                exam_id = exam[1]
                keyboard.append([
                    InlineKeyboardButton(f"نام آزمون: {exam_name} - ایدی: {exam_id}",
                                         callback_data=f"show_exam {exam_id}")
                ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("آزمون‌های در دسترس:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")



async def end_exam(context: CallbackContext) -> None:
    # print("end exam call")
    job_data = context.job.data
    user_id = job_data['user_id']
    exam_id = job_data['exam_id']
    exam_questions= job_data['exam_questions']

    end_message = "آقا دمت گرم آزمون تموم شد مرام گذاشتی شرکت کردی. بدروددد😘🖐"
    score_message =correction(user_id, exam_id, exam_questions)

    update = job_data['update']
    if update.message:
        await update.message.reply_text(end_message)
        await update.message.reply_text(score_message)
    elif update.callback_query:
        await update.callback_query.message.reply_text(end_message)
        await update.callback_query.message.reply_text(score_message)

    job_data.clear()



async def load_exam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    exam_id = context.user_data['exam_id']

    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('SELECT id, time FROM exam WHERE id = ? and status = ?', (exam_id,1))
    exam = c.fetchone()

    if not exam :
        await update.message.reply_text("ازمونی با ایدی که دادی نیست یا ازمون غیر فعال است😶")
        conn.close()
        return ConversationHandler.END
    else:
        exam_id = exam[0]
        context.user_data['exam_time'] = exam[1]
        c.execute('SELECT * FROM questions WHERE exam_id = ?', (exam_id,))
        questions = c.fetchall()
        conn.close()

        if not questions:
            await update.message.reply_text("هیچ سوالی برای این ازمون ندادی که .... بریم از اول..")
            return ConversationHandler.END

        context.user_data['exam_questions'] = [
            {'id': q[0], 'text_question': q[1], 'case1': q[2], 'case2': q[3], 'case3': q[4], 'case4': q[5],
             'answer': q[6], 'image': q[7],'user-answer':0} for q in questions]
        context.user_data['current_question_index'] = 0
        context.user_data['exam_id'] = exam_id
        context.user_data['update'] = update
        context.user_data['all-q'] = len(questions)

        job_queue = context.job_queue
        job_context = {
            'user_id': context.user_data['user_id'],
            'exam_id': exam_id,
            'exam_questions':context.user_data['exam_questions'],
            'update': update,
            'all-q':len(questions)
        }

        # print("start", time.time())


        job=job_queue.run_once(end_exam, when=context.user_data['exam_time'], data=job_context)
        context.user_data['exam_end_job'] = job

        await send_next_question(update, context)

        return ConversationHandler.END


def get_user_results_for_exam(exam_id):
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()

    # Find the exam ID based on the exam name
    c.execute('SELECT id FROM exam WHERE id = ?', (exam_id,))
    exam_row = c.fetchone()
    if exam_row is None:
        conn.close()
        return None  # Exam not found

    exam_id = exam_row[0]

    # Fetch user information and their result for the specified exam
    c.execute('''
    SELECT user.firstname, user.lastname,user.national_code,user.username, result.correct, result.falsee, result.nulll, result.percentt
    FROM user
    JOIN result ON user.id = result.user_id
    WHERE result.exam_id = ?
    ORDER BY result.percentt DESC
    ''', (exam_id,))

    user_results = c.fetchall()

    conn.close()
    return user_results


async def get_exam_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        if len(context.args) != 1:
            await update.message.reply_text("ایدی برای سرچ ازمون نیومد")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("ای دی ازمون رو عددی نیس  ")
            return ConversationHandler.END

        user_results = get_user_results_for_exam(exam_id)
        if user_results:
            count=1

            message = "نتایج برای ازمون '{}':\n\n\n".format(exam_id)
            with open(f"{exam_id}.txt", 'w', encoding='utf-8') as file:
                file.write(message + '\n')
            with open(f"{exam_id}.txt", 'a', encoding='utf-8') as file:
                for row in user_results:
                    message += f"دانش اموز شماره ی : {count}\n"
                    message += f"نام و نام خانوادگی: {row[0]}\n"
                    message += f"کد ملی: {row[2]}\n"
                    message += f"یوزر نیم: {row[3]}\n"
                    message += f"تعداد سوالات درست: {row[4]}\n"
                    message += f"تعداد سوالات غلط: {row[5]}\n"
                    message += f"تعداد سوالات نزده: {row[6]}\n"
                    message += f"درصد ازمون: {row[7]}\n\n"
                    message += "----------------------------------------------\n\n"

                    file.write(message + '\n')
                    message = ''
                    count+=1

            file_obj = open(f"{exam_id}.txt", "rb")
            # file_obj.name = f"{exam_id}.txt"

            # Send the file to the user
            await context.bot.send_document(update.message.chat_id, document=file_obj)

            # Close the file
            file_obj.close()
        else:
            message = "هیچ ازمونی با مشخاص مورد نطر یافت نشد. ایدی مورد نظر برای سرچ '{}'".format(exam_id)

            await update.message.reply_text(message)

    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END


async def show_exam(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query
    exam_id = int(query.data.split()[1])

    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()

    # Fetch exam information
    c.execute('SELECT id,name, time,status FROM exam WHERE id = ?', (exam_id,))
    exam = c.fetchone()

    # Fetch questions for the exam
    c.execute('SELECT id, text_question, case1, case2, case3, case4, answer FROM questions WHERE exam_id = ?',
              (exam_id,))
    questions = c.fetchall()

    conn.close()

    if exam:
        exam_id, exam_name, exam_time,exam_status = exam
        message = f"اطلاعات آزمون:\nایدی: {exam_id}\nنام: {exam_name}\nزمان ازمون: {exam_time}\n وضعیت فعال بودن ازمون :{exam_status}\n\n"
        message += "\n\n\n\nسوالات:\n"
        if update.message:
            await update.message.reply_text(message)

        elif update.callback_query:
            await update.callback_query.message.reply_text(message)

        if not questions:
            message = "سوالی برای این آزمون موجود نیست."
            if update.message:
                await update.message.reply_text(message)

            elif update.callback_query:
                await update.callback_query.message.reply_text(message)
        else:
            counter=1
            for question in questions:
                question_id, text_question, case1, case2, case3, case4, answer = question
                message = (f"\n ایدی سوال در دیتابیس  {question_id}\n شماره سوال:{counter} \n{text_question}\n\n"
                            f"۱. {case1}\n"
                            f"۲. {case2}\n"
                            f"۳. {case3}\n"
                            f"۴. {case4}\n"
                            f"جواب صحیح: {answer}\n")
                counter+=1
                if update.message:
                    await update.message.reply_text(message)

                elif update.callback_query:
                    await update.callback_query.message.reply_text(message)


    else:
        message = "آزمون یافت نشد."
        if update.message:
            await update.message.reply_text(message)

        elif update.callback_query:
            await update.callback_query.message.reply_text(message)

    # await query.edit_message_text(text=message)



async def edit_exam_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        # Retrieve the argument from the command
        if len(context.args) < 2:
            await update.message.reply_text(
                "دو تا شماره بعد از eqt بزنی که اولی ایدی ازمون و دومی تایم جدید به ثانیه هست. متن جدید رو هم باید بعدش بفرستی.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            new_time = int(context.args[1])

        except ValueError:
            await update.message.reply_text("ای دی ها باید از جنس عدد باشند .  ")
            return ConversationHandler.END

        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('''
                UPDATE exam
                SET time = ?
                WHERE id = ? 
            ''', (new_time, exam_id))
        conn.commit()

        if c.rowcount == 0:
            await update.message.reply_text("ازمون مورد نظر یافت نشد.")
            conn.close()
            return ConversationHandler.END

        conn.close()

        await update.message.reply_text("تایم ازمون بروز رسانی شد.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END


async def edit_exam_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        # Retrieve the argument from the command
        if len(context.args) < 2:
            await update.message.reply_text(
                "دو تا شماره بعد از estatus بزنی که اولی ایدی ازمون و دومی وضعیت ازمون که f یا  t باید باشه.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            new_status = context.args[1]
            if new_status == "f":
                new_status =False
            elif new_status=="t":
                new_status =True
            else:
                raise Exception("عبارت وارد شده باید یا t یا f باشد همچنین ایدی باید از جنس عدد باشد")

        except ValueError:
            await update.message.reply_text("ای دی ها باید از جنس عدد باشند .  ")
            return ConversationHandler.END

        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('''
                UPDATE exam
                SET status = ?
                WHERE id = ? 
            ''', (new_status, exam_id))
        conn.commit()

        if c.rowcount == 0:
            await update.message.reply_text("ازمون مورد نظر یافت نشد.")
            conn.close()
            return ConversationHandler.END

        conn.close()

        await update.message.reply_text("وضعیت ازمون بروز شد.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END





async def end_examm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data['user_id']
    exam_id = context.user_data['exam_id']
    exam_questions = context.user_data['exam_questions']

    end_message = "آقا دمت گرم آزمون تموم شد مرام گذاشتی شرکت کردی. بدروددد😘🖐"
    job = context.user_data.get('exam_end_job')
    if job:
        job.schedule_removal()
        del context.user_data['exam_end_job']

    score_message = correction(user_id, exam_id, exam_questions)

    if update.message:
        await update.message.reply_text(end_message)
        await update.message.reply_text(score_message)
    elif update.callback_query:
        await update.callback_query.message.reply_text(end_message)
        await update.callback_query.message.reply_text(score_message)
    # print("payan")
    return ConversationHandler.END