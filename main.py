import os
import re

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from drive import (
    get_subject_folders,
    get_or_create_subject_folder,
    upload_file
)

from config import BOT_TOKEN

from generators.type1 import generate_mcq
from generators.type2 import generate_questions


# --------------------------------
# GLOBALS
# --------------------------------

user_states = {}
user_data = {}

TYPE1_FOLDER = "data/type1"
TYPE2_FOLDER = "data/type2"

os.makedirs(TYPE1_FOLDER, exist_ok=True)
os.makedirs(TYPE2_FOLDER, exist_ok=True)


# --------------------------------
# START
# --------------------------------

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        ["Quiz Type 1"],
        ["Quiz Type 2"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Select Quiz Type",
        reply_markup=reply_markup
    )


# --------------------------------
# RECEIVE DOCUMENT
# --------------------------------

async def handle_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    document = update.message.document

    if not document.file_name.endswith(".csv"):

        await update.message.reply_text(
            "Only CSV allowed"
        )

        return

    file = await document.get_file()

    state = user_states.get(chat_id)

    # ----------------------------
    # TYPE 1 CSV
    # ----------------------------

    if state == "waiting_type1_csv":

        file_path = os.path.join(
            TYPE1_FOLDER,
            document.file_name
        )

        await file.download_to_drive(
            file_path
        )

        folders = get_subject_folders()

        keyboard = []

        for folder in folders:

            subject_name = folder["name"]

            keyboard.append(
                [subject_name]
            )

            os.makedirs(
                os.path.join(
                    "output",
                    subject_name
                ),
                exist_ok=True
            )

        keyboard.append(
            ["Add New Subject"]
        )

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        user_states[
            chat_id
        ] = "waiting_subject_type1"

        await update.message.reply_text(
            "Select Subject",
            reply_markup=reply_markup
        )

        return

    # ----------------------------
    # TYPE 2 TRUE FILE
    # ----------------------------

    elif state == "waiting_true_file":

        file_path = os.path.join(
            TYPE2_FOLDER,
            "true.csv"
        )

        await file.download_to_drive(
            file_path
        )

        base_name = re.sub(
        r"\s+(true|false)\.csv$",
        "",
        document.file_name,
        flags=re.IGNORECASE
        )

        user_data[chat_id] = {
            "base_name": base_name
        }

        user_states[
            chat_id
        ] = "waiting_false_file"

        await update.message.reply_text(
            "Send FALSE CSV"
        )

        return

    # ----------------------------
    # TYPE 2 FALSE FILE
    # ----------------------------

    elif state == "waiting_false_file":

        file_path = os.path.join(
            TYPE2_FOLDER,
            "false.csv"
        )

        await file.download_to_drive(
            file_path
        )

        folders = get_subject_folders()

        keyboard = []

        for folder in folders:

            keyboard.append(
                [folder["name"]]
            )

        keyboard.append(
            ["Add New Subject"]
        )

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        user_states[
            chat_id
        ] = "waiting_subject_type2"

        await update.message.reply_text(
            "Select Subject",
            reply_markup=reply_markup
        )

        return
        # --------------------------------
# HANDLE TEXT
# --------------------------------

async def handle_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.effective_chat.id

    text = update.message.text.strip()

    # ----------------------------
    # QUIZ TYPE 1
    # ----------------------------

    if text == "Quiz Type 1":

        user_states[
            chat_id
        ] = "waiting_type1_csv"

        await update.message.reply_text(
            "Send CSV File"
        )

        return

    # ----------------------------
    # QUIZ TYPE 2
    # ----------------------------

    elif text == "Quiz Type 2":

        user_states[
            chat_id
        ] = "waiting_true_file"

        await update.message.reply_text(
            "Send TRUE CSV"
        )

        return
        
    # ----------------------------
    # ADD SUBJECT
    # ----------------------------

    elif text == "Add New Subject":

        user_states[
            chat_id
        ] = "waiting_subject_name"

        await update.message.reply_text(
            "Send Subject Name"
        )

        return    

    # ----------------------------
    # TYPE 1 SUBJECT
    # ----------------------------

    elif user_states.get(
    chat_id
    ) == "waiting_subject_type1":

        subject_name = text

        output_files, count = generate_mcq(
            subject_name
        )

        folder_id = get_or_create_subject_folder(
            subject_name
        )

        uploaded_count = 0

        for file_path in output_files:

            upload_file(
                file_path,
                folder_id
            )

            uploaded_count += 1

            # delete output file after upload
            if os.path.exists(file_path):
                os.remove(file_path)

        # delete all input csv files
        for f in os.listdir(TYPE1_FOLDER):

            if f.endswith(".csv"):

                os.remove(
                    os.path.join(
                        TYPE1_FOLDER,
                        f
                    )
                )

        await update.message.reply_text(
            f"{count} MCQs generated and "
            f"{uploaded_count} files uploaded ✅"
        )

        user_states[
            chat_id
        ] = None

        return

    # ----------------------------
    # TYPE 2 SUBJECT
    # ----------------------------

    elif user_states.get(
        chat_id
    ) == "waiting_subject_type2":

        subject_name = text

        base_name = user_data[
            chat_id
        ]["base_name"]

        output_file = os.path.join(
            "output",
            subject_name,
            f"{base_name}.csv"
        )
        try:

            output_path, count = generate_questions(
                os.path.join(
                    TYPE2_FOLDER,
                    "true.csv"
                ),
                os.path.join(
                    TYPE2_FOLDER,
                    "false.csv"
                ),
                output_file
            )

        except ValueError as e:

            await update.message.reply_text(
                str(e)
            )

            return
        
        folder_id = get_or_create_subject_folder(
            subject_name
        )

        upload_file(
            output_path,
            folder_id
        )
        # delete generated output
        if os.path.exists(output_path):
            os.remove(output_path)

        # delete true.csv and false.csv
        for f in os.listdir(TYPE2_FOLDER):

            if f.endswith(".csv"):

                os.remove(
                    os.path.join(
                        TYPE2_FOLDER,
                        f
                    )
                )

        await update.message.reply_text(
            f"{count} Questions Generated ✅\n"
            f"{base_name}.csv uploaded to Google Drive ✅"
        )

        user_states[
            chat_id
        ] = None

        return

  
    # ----------------------------
    # CREATE SUBJECT
    # ----------------------------

    elif user_states.get(
        chat_id
    ) == "waiting_subject_name":

        subject_name = text

        os.makedirs(
            os.path.join(
                "output",
                subject_name
            ),
            exist_ok=True
        )

        get_or_create_subject_folder(
            subject_name
        )

        folders = get_subject_folders()

        keyboard = []

        for folder in folders:

            keyboard.append(
                [folder["name"]]
            )

        keyboard.append(
            ["Add New Subject"]
        )

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        await update.message.reply_text(
            f"{subject_name} created successfully ✅\nSelect Subject",
            reply_markup=reply_markup
        )

        user_states[
    chat_id
    ] = "waiting_subject_type2"

        return

# --------------------------------
# BOT
# --------------------------------

app = ApplicationBuilder().token(
    BOT_TOKEN
).build()

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    MessageHandler(
        filters.Document.ALL,
        handle_document
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    )
)

print(
    "Bot Running..."
)

app.run_polling()