import csv
import random
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_FOLDER = os.path.join(
    BASE_DIR,
    "data",
    "type1"
)
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 🔹 Get all CSV files
def get_data_files():
    return [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]


# 🔹 Read CSV
def read_data(data_path):
    with open(data_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 🔹 Generate balanced answer positions
def generate_balanced_positions(total_questions):

    base = total_questions // 4
    remainder = total_questions % 4

    positions = (
        [1] * base +
        [2] * base +
        [3] * base +
        [4] * base
    )

    # distribute remaining randomly
    if remainder > 0:
        extra = random.sample([1, 2, 3, 4], remainder)
        positions.extend(extra)

    random.shuffle(positions)
    return positions


# 🔹 Generate MCQs for all files
# 🔹 Generate MCQs for all files
def generate_mcq(subject_name):

    files = get_data_files()

    if not files:
        return [], 0

    output_files = []
    total_questions = 0

    for file_name in files:

        data_path = os.path.join(
            DATA_FOLDER,
            file_name
        )

        subject_folder = os.path.join(
            OUTPUT_FOLDER,
            subject_name
        )

        os.makedirs(
            subject_folder,
            exist_ok=True
        )

        output_path = os.path.join(
            subject_folder,
            file_name
        )

        data = read_data(data_path)

        random.shuffle(data)

        question_count = len(data)

        # ✅ Balanced distribution
        answer_positions = generate_balanced_positions(
            question_count
        )

        questions = []

        for i, row in enumerate(data):

            correct = row["correct"]

            wrong = [
                row["wrong1"],
                row["wrong2"],
                row["wrong3"]
            ]

            random.shuffle(wrong)

            target_position = answer_positions[i]

            options = []

            wrong_index = 0

            for pos in range(1, 5):

                if pos == target_position:

                    options.append(correct)

                else:

                    options.append(
                        wrong[wrong_index]
                    )

                    wrong_index += 1

            questions.append([
                row["question"],
                options[0],
                options[1],
                options[2],
                options[3],
                target_position
            ])

        # WRITE OUTPUT
        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "question",
                "option1",
                "option2",
                "option3",
                "option4",
                "answer"
            ])

            writer.writerows(questions)

        output_files.append(output_path)

        total_questions += len(questions)

    return output_files, total_questions