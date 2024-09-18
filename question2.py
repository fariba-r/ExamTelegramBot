
import sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, \
    ConversationHandler, ContextTypes, CallbackContext
from dotenv import load_dotenv
import os
import io
from PIL import Image



load_dotenv()

FIRST_NAME, LAST_NAME, EXAM_NAME, EXAM_COUNT,EXAM_TIME, QUESTION_TEXT, CASE1, CASE2, CASE3, CASE4, ANSWER,SEECREATEDEXAM,IMAGE,SAVE_IMAGE,QuestionNumber = range(15)
# async def add_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     context.user_data['question_text'] = update.message.text
#     # await update.message.reply_text("گزینه اول رو بفرست :")
#     # update.message.reply_text('اگه سوال نیاز به عکس داره برام بفرست اگر نه بزن رو کلیک کنسل😊')
#
#     keyboard = [[InlineKeyboardButton("عکس نداره", callback_data='skip_image')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     update.message.reply_text('اگه سوال نیاز به عکس داره برام بفرست اگر نه بزن رو کلیک کنسل😊',
#                               reply_markup=reply_markup)
#
#     return IMAGE

async def add_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['question_text'] = update.message.text

    keyboard = [[InlineKeyboardButton("عکس نداره", callback_data='skip_image')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('اگر سوالت نیاز به عکس داره برام بفرست اگر نداره روی کلید بزن🙂',
                                    reply_markup=reply_markup)
    return IMAGE

async def add_case1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['case1'] = update.message.text
    await update.message.reply_text("گزینه دوم سوال بفرست :")
    return CASE2

async def add_case2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['case2'] = update.message.text
    await update.message.reply_text("گزینه سوم سوال :")
    return CASE3

async def add_case3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['case3'] = update.message.text
    await update.message.reply_text("گزینه چهارم سوال :")
    return CASE4

async def add_case4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['case4'] = update.message.text
    await update.message.reply_text("شماره ی گزینه ی جواب رو بده ببینم خودت بلدی شیطون 😉( یک عدد بین 1 تا 4)")
    return ANSWER

async def add_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        answer = int(update.message.text)
        if answer < 1 or answer > 4:
            raise ValueError("Answer out of range")
    except ValueError:
        await update.message.reply_text("عی دل غافل حواست کجاست ادمین جان !!🥱 بین 1 تا 4 یکی انتخاب کن لطفا. چیزی که وارد کردی نامعتبر بود...")
        return ANSWER

    # Insert the question into the database
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO questions (text_question,image, case1, case2, case3, case4, answer, exam_id) 
    VALUES (?, ?, ?, ?, ?, ?, ?,?)
    ''', (
        context.user_data['question_text'],
        context.user_data['image'],
        context.user_data['case1'],
        context.user_data['case2'],
        context.user_data['case3'],
        context.user_data['case4'],
        answer,
        context.user_data['exam_id']
    ))
    conn.commit()
    conn.close()

    if context.user_data['current_question'] < context.user_data['exam_count']:
        context.user_data['current_question'] += 1
        await update.message.reply_text(
            f"سوال {context.user_data['current_question']} :✍: متن سوال بعدی پلیز")
        return QUESTION_TEXT
    else:
        await update.message.reply_text("عرض خسته نباشید به داوش گلم ادمین خان اعظم. آزمون ساخته شد برو حالشو ببر.")
        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('SELECT id, name FROM exam ORDER BY id DESC LIMIT 1')
        last_exam = c.fetchone()
        conn.close()

        if last_exam is None:
            await update.message.reply_text("خطا در نشان دادن آخرین آزمون ساخته شده😪")
        else:
            await update.message.reply_text(f"شماره آزمون: {last_exam[0]}, نام آزمون: {last_exam[1]}")

    return ConversationHandler.END


def save_result_exam_db(user_id,exam_id,correct,false,all):
    # print("save result")
    percent = (correct - false/ 3) /all * 100
    nul=all-correct-false

    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('INSERT INTO result (user_id, exam_id, correct, falsee, nulll, percentt) VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, exam_id, correct, false, nul,percent))
    conn.commit()
    conn.close()


    score_message = f"""
    درصد شما(با احتساب نمره منفی):{percent}
    تعداد درست :{correct}
    تعداد غلط :{false}
    تعداد نزده :{nul}

    حالا اگه سوالایی که غلط جواب دادی رو کلا نمیزدی درصدت میشد :{correct / (all) * 100}


             """

    return score_message





def correction(user_id, exam_id, exam_questions):
    # print("correction")
    correct, false, nul = 0,0,0
    all = len(exam_questions)
    for question in exam_questions:
        # print(question['user-answer'])
        if question['user-answer'] == question['answer']:
            correct += 1

        elif question['user-answer'] == 0:
            nul += 1

        else :
            false += 1

    return save_result_exam_db(user_id, exam_id, correct, false, all)

def show_case(question)->list:
    keyword=[]
    selected_case=question['user-answer']

    if selected_case == 1:
        keyword.append([InlineKeyboardButton(f"1️⃣ {question['case1']}  ✅", callback_data=f"answer_{question['id']}_1")])
    else:
        keyword.append([InlineKeyboardButton(f"1️⃣ {question['case1']} ", callback_data=f"answer_{question['id']}_1")])

    if selected_case == 2:
        keyword.append([InlineKeyboardButton(f"2️⃣ {question['case2']}  ✅", callback_data=f"answer_{question['id']}_2")])
    else:
        keyword.append([InlineKeyboardButton(f"2️⃣ {question['case2']} ", callback_data=f"answer_{question['id']}_2")])

    if selected_case == 3:
        keyword.append([InlineKeyboardButton(f"3️⃣ {question['case3']}  ✅", callback_data=f"answer_{question['id']}_3")])
    else:
        keyword.append([InlineKeyboardButton(f"3️⃣ {question['case3']} ", callback_data=f"answer_{question['id']}_3")])

    if selected_case == 4:
        keyword.append([InlineKeyboardButton(f"4️⃣ {question['case4']}  ✅", callback_data=f"answer_{question['id']}_4")])
    else:
        keyword.append([InlineKeyboardButton(f"4️⃣ {question['case4']} ", callback_data=f"answer_{question['id']}_4")])

    return keyword







async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    # print("send_next_question2")

    index = context.user_data.get('current_question_index',0 )
    questions = context.user_data.get('exam_questions', [])
    # print(context.user_data['current_question_index'], len(questions))
    # print("index questions: ", index)

    if index < len(questions):
        question = questions[index]
        photo_file_id=question['image']

        try:
            if photo_file_id is not None  :
                if update.message:


                    await update.message.reply_photo(photo=photo_file_id)
                elif update.callback_query:
                    await update.callback_query.message.reply_photo(photo=photo_file_id)

        except Exception as e:
            print(f"Error sending photo: {e}")
        if question['user-answer'] ==0 :
            keyboard = [
                [InlineKeyboardButton(f"1️⃣ {question['case1']}", callback_data=f"answer_{question['id']}_1")],
                [InlineKeyboardButton(f"2️⃣ {question['case2']}", callback_data=f"answer_{question['id']}_2")],
                [InlineKeyboardButton(f"3️⃣ {question['case3']}", callback_data=f"answer_{question['id']}_3")],
                [InlineKeyboardButton(f"4️⃣ {question['case4']}", callback_data=f"answer_{question['id']}_4")],
                        ]
        else:
            keyboard = show_case(question)
        if index == len(questions)-1 and index != 0:
            keyboard.append([InlineKeyboardButton("نمایش سوال قبل ", callback_data=f"answer_{question['id']}_-1")])
            keyboard.append([InlineKeyboardButton("پایان ازمون ", callback_data=f"answer_{question['id']}_0")])

        elif index == 0 and index != len(questions)-1 :

            keyboard.append([InlineKeyboardButton("نمایش سوال بعد ", callback_data=f"answer_{question['id']}_0")])
        elif index ==0 and index == len(questions)-1:
            keyboard.append([InlineKeyboardButton("پایان ازمون ", callback_data=f"answer_{question['id']}_0")])

        else:
            keyboard.append([InlineKeyboardButton("نمایش سوال بعد ", callback_data=f"answer_{question['id']}_0")])
            keyboard.append([InlineKeyboardButton("نمایش سوال قبل ", callback_data=f"answer_{question['id']}_-1")])


        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = f"سوال {context.user_data['current_question_index']+1}:❔\n{question['text_question']}"
        if update.message:
               message= await update.message.reply_text(message_text, reply_markup=reply_markup)
        elif update.callback_query:
               message= await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup)
        # /////////////////////////////////////////////////////////////////
        context.user_data['last_message_id'] = message.message_id
        context.user_data['chat_id'] = message.chat_id




    else:

        if index-1 == len(questions):

            context.user_data['current_question_index'] -= 3
            keyboard = [
                [InlineKeyboardButton(f"برگشت به ازمون 🟢", callback_data=f"answer_{context.user_data['current_question_index']}_-2")],
                [InlineKeyboardButton(f"پایان ازمون 🔴", callback_data=f"end_exam")],

            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = "لطفا یک مورد را انتخاب کن "

            if update.message:
                m=await update.message.reply_text(message_text, reply_markup=reply_markup)
            elif update.callback_query:
                m=await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup)
            context.user_data['finish-question'] = m.message_id
            context.user_data['chat_id-fq'] = m.chat_id
        else:
            # Insert the result into the database
            user_id = context.user_data['user_id']
            exam_id = context.user_data['exam_id']
            exam_questions=context.user_data['exam_questions']



            end_message = "آقا دمت گرم آزمون تموم شد مرام گذاشتی شرکت کردی. بدروددد😘🖐"
            job = context.user_data.get('exam_end_job')
            if job:
                job.schedule_removal()
                del context.user_data['exam_end_job']

            score_message =correction(user_id, exam_id, exam_questions)

            if update.message:
                await update.message.reply_text(end_message)
                await update.message.reply_text(score_message)
            elif update.callback_query:
                await update.callback_query.message.reply_text(end_message)
                await update.callback_query.message.reply_text(score_message)

            return ConversationHandler.END


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print( context.user_data['current_question_index'])
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    question_id = int(data[1])
    selected_answer = int(data[2])
    # print("question_id",question_id)


    if selected_answer ==-1 or selected_answer == 0:
        questions = context.user_data['exam_questions']
        question = next((q for q in questions if q['id'] == question_id), questions[-1])


        keyboard = []
        for i in range(1, 5):
            button_text = f" {question[f'case{i}']}"
            button = InlineKeyboardButton(button_text, callback_data=f"ignored_{question['id']}_{i}")
            keyboard.append([button])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_reply_markup(reply_markup=reply_markup)



        # print("selected answer: ", selected_answer)
        if selected_answer == -1:
            context.user_data['current_question_index'] -= 1
            await send_next_question(update, context)




        elif selected_answer == 0:
            try:

                await context.bot.delete_message(chat_id=context.user_data['chat_id-fq'
                                                                           ''], message_id=context.user_data['finish-question'])
            except :
                pass

            context.user_data['current_question_index'] += 1

            await send_next_question(update, context)
    elif selected_answer == -2:
        context.user_data['current_question_index'] += 1
        await send_next_question(update, context)

    else:
        questions = context.user_data['exam_questions']
        question = next((q for q in questions if q['id'] == question_id), None)

        if question:

            keyboard = []


            question["user-answer"] = selected_answer

            for i in range(1, 5):
                if i == selected_answer:
                    button_text = f"✅ {question[f'case{i}']}"

                else:
                    button_text = question[f'case{i}']


                button = InlineKeyboardButton(button_text, callback_data=f"ignored_{question['id']}_{i}")
                keyboard.append([button])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=reply_markup)


            context.user_data['current_question_index'] += 1
        else:
            await query.message.reply_text("سوالو نتونستم پیدا کنم، یک دنیا معذرت😥")

        if context.user_data['current_question_index']==len(questions):

            context.user_data['current_question_index'] += 1


        await send_next_question(update, context)




async def edit_question_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        # Retrieve the argument from the command
        if len(context.args) != 3:
            await update.message.reply_text(
                "سه تا شماره باید بعد از eqa بزنی که اولی ایدی ازمون ,ایدی سوال و جواب ویرایش شده هست. اینا رو رعایت کن و دوباره دستور رو رد کن بیاد.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            question_id = int(context.args[1])
            edited_answer = int(context.args[2])
        except ValueError:
            await update.message.reply_text("ای دی ها باید از جنس عدد باشند .  ")
            return ConversationHandler.END
        try:

            if edited_answer < 1 or edited_answer > 4:
                raise ValueError("Answer out of range")
        except (IndexError, ValueError):
            await update.message.reply_text("جواب باید عددی بین 1  تا 4 باشد.")
            return ConversationHandler.END

        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('''
                    UPDATE questions
                    SET answer = ?
                    WHERE id = ? AND exam_id = ?
                ''', (edited_answer, question_id, exam_id))
        conn.commit()

        if c.rowcount == 0:
            await update.message.reply_text("سوالی با این مشخصات یافت نشد.")
            conn.close()
            return ConversationHandler.END

        conn.close()

        await update.message.reply_text("پاسخ سوال مورد نظر به روز رسانی شد.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END



async def edit_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        # Retrieve the argument from the command
        if len(context.args) < 2:
            await update.message.reply_text(
                "دو تا شماره بعد از eqt بزنی که اولی ایدی ازمون و دومی ایدی سوال هست. متن جدید رو هم باید بعدش بفرستی.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            question_id = int(context.args[1])
            new_text = ' '.join(context.args[2:])
        except ValueError:
            await update.message.reply_text("ای دی ها باید از جنس عدد باشند .  ")
            return ConversationHandler.END

        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()
        c.execute('''
                UPDATE questions
                SET text_question = ?
                WHERE id = ? AND exam_id = ?
            ''', (new_text, question_id, exam_id))
        conn.commit()

        if c.rowcount == 0:
            await update.message.reply_text("سوالی با این مشخصات یافت نشد.")
            conn.close()
            return ConversationHandler.END

        conn.close()

        await update.message.reply_text("متن سوال مورد نظر به روز رسانی شد.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END



async def edit_question_case(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        if len(context.args) < 4:
            await update.message.reply_text(
                "چهار تا شماره باید بعد از eqc بزنی که اولی ایدی ازمون , دومی ایدی سوال, سومی شماره کیس (1 تا 4) و چهارمی متن کیس ویرایش شده هست. اینا رو رعایت کن و دوباره دستور رو رد کن بیاد.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            question_id = int(context.args[1])
            case_number = int(context.args[2])
            new_case_text = ' '.join(context.args[3:])
        except ValueError:
            await update.message.reply_text("ای دی ها و شماره کیس باید از جنس عدد باشند.")
            return ConversationHandler.END

        if case_number < 1 or case_number > 4:
            await update.message.reply_text("شماره کیس باید عددی بین 1 تا 4 باشد.")
            return ConversationHandler.END

        conn = sqlite3.connect('quiz_bot.db')
        c = conn.cursor()

        # Determine which case to update
        column_name = f'case{case_number}'

        c.execute(f'''
            UPDATE questions
            SET {column_name} = ?
            WHERE id = ? AND exam_id = ?
        ''', (new_case_text, question_id, exam_id))
        conn.commit()

        if c.rowcount == 0:
            await update.message.reply_text("سوالی با این مشخصات یافت نشد.")
            conn.close()
            return ConversationHandler.END

        conn.close()

        await update.message.reply_text("متن کیس مورد نظر به روز رسانی شد.")
        return ConversationHandler.END

    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file_id = update.message.photo[-1].file_id
    context.user_data['image'] = photo_file_id

    # await save_question_to_db(context.user_data)
    await update.message.reply_text('عکسو گرفتم و ذخیره کردم \nحالا گزینه اول سوال رو بفرست برام')

    return CASE1


async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data['image'] = None
    # await save_question_to_db(context.user_data)

    await query.edit_message_text(text="متن سوال بدون عکس ذخیره شد .\n لطفا گزینه اول سوال رو بفرست")
    return CASE1


async def edit_question_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        if len(context.args) < 2:
            await update.message.reply_text(
                "دو تا شماره باید بعد از eqc بزنی که اولی ایدی ازمون , دومی ایدی سوال,  هست. اینا رو رعایت کن و دوباره دستور رو رد کن بیاد.")
            return ConversationHandler.END
        try:
            exam_id = int(context.args[0])
            question_id = int(context.args[1])
        #     save this and call
            context.user_data['exam_id'] = exam_id
            context.user_data['question_id'] = question_id
            await update.message.reply_text("عکس جدید رو رد کن بیاد")
            return SAVE_IMAGE


        except ValueError:
            await update.message.reply_text("ای دی ها و شماره کیس باید از جنس عدد باشند.")
            return ConversationHandler.END
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")
        return ConversationHandler.END

async def save_edit_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file_id = update.message.photo[-1].file_id


    exam_id = context.user_data['exam_id']
    question_id = context.user_data['question_id']
    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()



    c.execute(f'''
                UPDATE questions
                SET image = ?
                WHERE id = ? AND exam_id = ?
            ''', (photo_file_id, question_id, exam_id))
    conn.commit()

    if c.rowcount == 0:
        await update.message.reply_text("سوالی با این مشخصات یافت نشد.")
        conn.close()
        return ConversationHandler.END

    conn.close()

    await update.message.reply_text("عکس سوال با موفقیت بروزرسانی شد.")
    return ConversationHandler.END


async def handle_question_number(update: Update, context: CallbackContext) -> int:
    try:

        message_id = context.user_data['last_message_id']
        chat_id = context.user_data['chat_id']
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)


        question_number = int(update.message.text.strip().lower().replace('q', '')) - 1
        if 0 <= question_number < len(context.user_data['exam_questions']):
            # Valid question number, navigate to that question
            context.user_data['current_question_index'] = question_number
            await send_next_question(update, context)
        else:
            # Invalid question number
            await update.message.reply_text("شماره سوال معتبر نیست.🤔 ")
            await send_next_question(update, context)
    except ValueError:

        await update.message.reply_text("دوباره دپار خود درگیری شدم یک دنیا معذرت ...")
    except KeyError:
        await update.message.reply_text(" اخه عدد هم شد اسم ...یه اسم قشنگ بده سید \n یکی دیگه بده لطفا..")



