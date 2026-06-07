import os
import random
import pandas as pd


# --------------------------------
# combinations
# --------------------------------
CYCLE = [
    (1,), (2,), (3,), (4,),
    (1, 2), (1, 3), (1, 4),
    (2, 3), (2, 4), (3, 4),
    (1, 2, 3), (1, 2, 4),
    (1, 3, 4), (2, 3, 4),
    (1, 2, 3, 4)
]


def format_option(c):

    if len(c) == 1:
        return f"({c[0]}) only"

    elif len(c) == 2:
        return f"({c[0]}) and ({c[1]}) only"

    elif len(c) == 3:
        return f"({c[0]}), ({c[1]}) and ({c[2]}) only"

    else:
        return "(1), (2), (3) and (4)"


# --------------------------------
# Generate Questions
# --------------------------------
def generate_questions(
    true_file,
    false_file,
    output_file
):

    true_df = pd.read_csv(true_file)
    false_df = pd.read_csv(false_file)

    # --------------------------------
    # pools
    # --------------------------------

    true_pool = true_df.to_dict("records")
    false_pool = false_df.to_dict("records")
    print("VALIDATION ACTIVE")
    
    # --------------------------------
    # minimum validation
    # --------------------------------

    if len(true_pool) < 30:

        raise ValueError(
            f"Minimum 30 TRUE statements required. "
            f"Found: {len(true_pool)}"
        )

    if len(false_pool) < 30:

        raise ValueError(
            f"Minimum 30 FALSE statements required. "
            f"Found: {len(false_pool)}"
        )

    random.shuffle(true_pool)
    random.shuffle(false_pool)

    used_true = []
    used_false = []

    total_statements = (
        len(true_pool)
        + len(false_pool)
    )

    num_questions = (
        total_statements + 3
    ) // 4

    # --------------------------------
    # balanced combinations
    # --------------------------------

    base = num_questions // len(CYCLE)
    extra = num_questions % len(CYCLE)

    targets = []

    for combo in CYCLE:

        targets.extend(
            [combo] * base
        )

    # maintain order
    targets.extend(
        CYCLE[:extra]
    )

    rows = []

    # --------------------------------
    # generate
    # --------------------------------

    for target in targets:

        statements = []

        used_in_question = set()

        for pos in [1, 2, 3, 4]:

            # ------------------------
            # TRUE SLOT
            # ------------------------

            if pos in target:

                if true_pool:

                    row = true_pool.pop()

                    used_true.append(
                        row
                    )

                else:

                    available = [
                        x
                        for x in used_true
                        if x["id"] not in used_in_question
                    ]

                    row = random.choice(
                        available
                    )

                used_in_question.add(
                    row["id"]
                )

                statements.append(
                    row["statement_text"]
                )

            # ------------------------
            # FALSE SLOT
            # ------------------------

            else:

                if false_pool:

                    row = false_pool.pop()

                    used_false.append(
                        row
                    )

                else:

                    available = [
                        x
                        for x in used_false
                        if x["id"] not in used_in_question
                    ]

                    row = random.choice(
                        available
                    )

                used_in_question.add(
                    row["id"]
                )

                statements.append(
                    row["statement_text"]
                )

        # --------------------------------
        # options
        # --------------------------------

        correct = format_option(
            target
        )

        others = [
            c
            for c in CYCLE
            if c != target
        ]

        random.shuffle(
            others
        )

        options = (
            [correct]
            + [
                format_option(x)
                for x in others[:3]
            ]
        )

        random.shuffle(
            options
        )

        answer_index = (
            options.index(correct)
            + 1
        )

        # --------------------------------
        # question text
        # --------------------------------

        q_text = (
            "பின்வரும் கூற்றுகளில் "
            "சரியானதைத் தேர்வு செய்க"
            " \\n\\n (1) "
            + statements[0]
            + " \\n\\n (2) "
            + statements[1]
            + " \\n\\n (3) "
            + statements[2]
            + " \\n\\n (4) "
            + statements[3]
        )

        rows.append([
            q_text,
            options[0],
            options[1],
            options[2],
            options[3],
            answer_index
        ])

    # --------------------------------
    # save
    # --------------------------------

    df = pd.DataFrame(
        rows,
        columns=[
            "question",
            "option1",
            "option2",
            "option3",
            "option4",
            "answer"
        ]
    )

    os.makedirs(
        os.path.dirname(
            output_file
        ),
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    return (
        output_file,
        len(df)
    )