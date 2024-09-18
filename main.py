from db import setup_database
from exam2 import *
from user2 import *
from question2 import *
from dotenv import load_dotenv
import os

load_dotenv()


# State definitions for ConversationHandler
FIRST_NAME, LAST_NAME, EXAM_NAME, EXAM_COUNT, EXAM_TIME, QUESTION_TEXT, CASE1, CASE2, CASE3, CASE4, ANSWER, SEECREATEDEXAM, IMAGE ,SAVE_IMAGE,QuestionNumber= range( 15)

questions = []
exam_id_counter = 1
question_id_counter = 1

setup_database()


async def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if str(user_id) in os.getenv('ACOUNTID').split("_"):
        help_text = (
            """
‼راهنمای استفاده از بات ازمون ساز‼


1️⃣ -->🔐 /list_exams =
 نمایش لیست آزمون‌ها
با زدن این دستور لیست کل ازمون ها با ایدی نمایش داده می شود. با کلیک کردن بر روی هر کدام از ازمون های نمایش داده شده می توانید جزییات هر ازمون اعمم از تایم برای هر سوال و تمامی سوالات ازمون به همراه گزینه ها و پاسخ را دریافت کنید.


2️⃣ -->🔐 /start_create_exam =
 ساخت ازمون جدید
با این دستور می توانید ازمون جدید بسازید. اگر در حین ساخت نیازمند کنیل کردن فرایند ساخت و ادامه ندادن ان بودید عبارت /cancel را وارد نمایید تا فرایند ساخت ازمون کنسل شود.


3️⃣ --> /start_exam <int id> =
 شروع ازمون
 برای شروع ازمون دو راه موجود است توجه شود ای دی ازمون را می توان از دستورات جزییات ازمون بدست اورد:
👉با استفاده از لینک کمکی:
https://t.me/examCmpSruBot?start=start_exam_<int id>
با قرار دادن ای دی ازمون دز انتهای لینک می توانید در ان ازمون شرکت کنید.
👉 با استفاده از دستور:
/start_exam <int id>  می توان در ازمون شرکت کرد
با استفاده از دستور

هر کاربر تنها یک بار می تواند از در یک ازمون شرکت کند .
کاربر می تواند به سوالا قبل و بعد برود و همچنین پاسخ قبل خود را ویرایش کند.


4️⃣ --> 🔐/exam_results <int id> =
 دیدن اطلاعات کاربران شرکت کننده در ازمون  


5️⃣ --> 🔐/eqt <exam_id> <question_id> <new_text> =
 ویرایش متن سوال


6️⃣ --> 🔐/eqc <exam_id> <question_id> <case_number> <new_case_text> =
 ویرایش گزینه سوال"


7️⃣ --> 🔐/eqa <exam_id> <question_id> <new_answer> =
 ویرایش جواب سوال"

8️⃣ --> 🔐/eqp <exam_id> <question_id> =
 ویرایش عکس سوال

9️⃣ --> 🔐/etime <exam_id>  =
 ویرایش تایم ازمون 
 
1️⃣0️⃣ --> 🔐/estatus <exam_id> f/t =
تغییر وضعیت فعالسازی یم ازمون با وارد کردن  f یا t که به ترتیب برای غیر فعالسازی و فعالسازی ازمون هست.
 
 
8️⃣ --> 🔐/help =
 نمایش این راهنما

💡 دستوراتی که با نماد 🔐 مشخص شده است نیازمند دسترسی ادمین هست و فقط ادمین توانایی انجام ان عملیات را دارد.


            """
        )
        await update.message.reply_text(help_text)
    else:
        await update.message.reply_text("نکن خطر داره حسن 😤 شما که ادمین نیستی برادر بسیجی برو با برگ ترت بیا👻")


async def handle_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')

    exam_name = data[1]  # Adjusted to match callback_data formatting in InlineKeyboardButton

    conn = sqlite3.connect('quiz_bot.db')
    c = conn.cursor()
    c.execute('SELECT id FROM exam WHERE name = ?', (exam_name,))
    exam = c.fetchone()

    if exam:
        exam_id = exam[0]
        c.execute('SELECT * FROM questions WHERE exam_id = ?', (exam_id,))
        questions = c.fetchall()
        conn.close()

        if not questions:
            await query.message.reply_text("No questions found for this exam.")
        else:
            context.user_data['exam_questions'] = [
                {'id': q[0], 'text_question': q[1], 'case1': q[2], 'case2': q[3], 'case3': q[4], 'case4': q[5],
                 'answer': q[6]} for q in questions]
            context.user_data['current_question_index'] = 0
            context.user_data['exam_id'] = exam_id
            await send_next_question(query.message, context)
    else:
        await query.message.reply_text("No exam found with that name.")
        conn.close()


async def start_exam_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.args:
        param = context.args[0]
        if param.startswith("start_exam_"):
            exam_id = param.split("_")[-1]
            context.user_data['exam_id'] = exam_id
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
                    await update.message.reply_text(
                        "شما قبلا در این آزمون شرکت کرده‌اید و نمی‌توانید دوباره شرکت کنید.")
                    conn.close()
                    return ConversationHandler.END

            conn.close()

            await update.message.reply_text("""
                سلام و درورد 🖐😁
                صفا اوردی🤩
                لطفا با حفظ خونسردی تمام و کمال نام و نام خانوادگیتو بهمون بگو🤗""")

            return FIRST_NAME
    else:
        await update.message.reply_text("دستور نا معتبر")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


def main() -> None:
    # Replace 'YOUR TOKEN HERE' with your actual bot token
    token = database_password = os.getenv('BOTTOKEN')
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start_create_exam', start_create_exam)],
        states={
            EXAM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_exam_name)],
            EXAM_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_exam_count)],
            EXAM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_exam_time)],
            QUESTION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_text)],
            IMAGE: [
                MessageHandler(filters.PHOTO, receive_image),
                CallbackQueryHandler(skip_image, pattern='skip_image')
            ],
            CASE1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_case1)],
            CASE2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_case2)],
            CASE3: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_case3)],
            CASE4: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_case4)],
            ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_answer)],

        },
        fallbacks=[],

    )

    quiz_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start_exam', start_exam)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_nationalcode)],


        },
        fallbacks=[CommandHandler('cancel', cancel),]
    )
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex('^q[0-9]+$'), handle_question_number))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question_number))

    application.add_handler(conv_handler)
    application.add_handler(quiz_conv_handler)
    application.add_handler(CommandHandler('exam_results', get_exam_results))
    application.add_handler(CommandHandler('eqa', edit_question_answer))
    application.add_handler(CommandHandler('eqc', edit_question_case))
    application.add_handler(CommandHandler('eqt', edit_question_text))
    application.add_handler(CommandHandler('etime', edit_exam_time))
    application.add_handler(CommandHandler('estatus', edit_exam_status))

    picture = ConversationHandler(
        entry_points=[CommandHandler('eqp', edit_question_picture)],
        states={
            SAVE_IMAGE: [MessageHandler(filters.PHOTO & ~filters.COMMAND, save_edit_image)],


        },
        fallbacks=[CommandHandler('cancel', cancel), ]
    )

    application.add_handler(picture)
    application.add_handler(CommandHandler('list_exams', list_exams))
    application.add_handler(CommandHandler('help', help_command))

    application.add_handler(CallbackQueryHandler(show_exam, pattern='^show_exam'))
    application.add_handler(CallbackQueryHandler(handle_send, pattern=r"^send_"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^answer_"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^end_create_"))
    application.add_handler(CallbackQueryHandler(end_examm, pattern='^end_exam$'))

    # application.add_handler(CommandHandler('start', start))
    quiz_conv_handler1 = ConversationHandler(
        entry_points=[CommandHandler('start', start_exam_link)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_nationalcode)],


        },
        fallbacks=[]
    )

    application.add_handler(quiz_conv_handler1)

    application.run_polling()


if __name__ == '__main__':
    main()
