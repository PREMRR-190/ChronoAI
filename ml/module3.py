# ==========================================
# CHRONOAI - ML MODULE 3
# Productivity Recommendation System
# ==========================================

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import joblib


# ==========================================
# STEP 1: CREATE SAMPLE CHRONOAI DATA
# ==========================================

data = {
    "sleep_hours": [
        5, 6, 7, 8, 6, 7, 5, 8, 7, 6,
        7, 8, 5, 6, 7, 8, 6, 7, 5, 8
    ],

    "screen_time": [
        8, 6, 4, 3, 7, 5, 9, 2, 4, 6,
        5, 3, 8, 7, 4, 2, 6, 5, 9, 3
    ],

    "tasks_planned": [
        8, 7, 6, 5, 8, 6, 9, 5, 6, 8,
        7, 5, 9, 8, 6, 5, 7, 6, 9, 5
    ],

    "tasks_completed": [
        3, 4, 5, 4, 5, 5, 3, 5, 5, 4,
        6, 5, 3, 4, 5, 4, 5, 5, 2, 5
    ],

    "study_hours": [
        2, 3, 4, 5, 3, 4, 2, 6, 4, 3,
        4, 5, 2, 3, 4, 5, 3, 4, 2, 6
    ]
}


df = pd.DataFrame(data)


# ==========================================
# STEP 2: CREATE PRODUCTIVITY SCORE
# ==========================================

df["completion_rate"] = (
    df["tasks_completed"] / df["tasks_planned"]
) * 100


# Productivity score formula

df["productivity_score"] = (
    (df["sleep_hours"] / 8) * 25
    +
    ((10 - df["screen_time"]) / 10) * 20
    +
    (df["completion_rate"] / 100) * 35
    +
    (df["study_hours"] / 6) * 20
)


# Keep score between 0 and 100

df["productivity_score"] = df["productivity_score"].clip(0, 100)


# Save dataset

df.to_csv(
    "data/chronoai_data.csv",
    index=False
)

print("\nDataset created successfully!")
print(df.head())


# ==========================================
# STEP 3: SELECT INPUT AND OUTPUT
# ==========================================

X = df[
    [
        "sleep_hours",
        "screen_time",
        "tasks_planned",
        "tasks_completed",
        "study_hours"
    ]
]

y = df["productivity_score"]


# ==========================================
# STEP 4: TRAIN TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# ==========================================
# STEP 5: TRAIN RANDOM FOREST MODEL
# ==========================================

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)


print("\nModel training completed!")


# ==========================================
# STEP 6: MODEL PREDICTION
# ==========================================

y_pred = model.predict(X_test)


# ==========================================
# STEP 7: MODEL EVALUATION
# ==========================================

mae = mean_absolute_error(y_test, y_pred)

rmse = np.sqrt(
    mean_squared_error(y_test, y_pred)
)

r2 = r2_score(y_test, y_pred)


print("\n========== MODEL EVALUATION ==========")

print("MAE :", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2 Score:", round(r2, 2))


# ==========================================
# STEP 8: SAVE MODEL
# ==========================================

joblib.dump(
    model,
    "models/productivity_model.pkl"
)

print("\nModel saved successfully!")

print(
    "Location: models/productivity_model.pkl"
)


# ==========================================
# STEP 9: PRODUCTIVITY RECOMMENDATION
# ==========================================

def generate_recommendation(
    sleep_hours,
    screen_time,
    tasks_planned,
    tasks_completed,
    study_hours
):

    input_data = pd.DataFrame(
        [[
            sleep_hours,
            screen_time,
            tasks_planned,
            tasks_completed,
            study_hours
        ]],
        columns=[
            "sleep_hours",
            "screen_time",
            "tasks_planned",
            "tasks_completed",
            "study_hours"
        ]
    )

    predicted_score = model.predict(
        input_data
    )[0]

    predicted_score = round(
        max(0, min(100, predicted_score)),
        2
    )

    recommendations = []


    # Screen time recommendation

    if screen_time > 6:
        recommendations.append(
            "Reduce mobile/screen time by at least 1 hour."
        )

    elif screen_time > 4:
        recommendations.append(
            "Try to reduce unnecessary screen time."
        )

    else:
        recommendations.append(
            "Your screen time is under control."
        )


    # Sleep recommendation

    if sleep_hours < 6:
        recommendations.append(
            "Increase your sleep duration. Aim for 7-8 hours."
        )

    elif sleep_hours < 7:
        recommendations.append(
            "Try to get at least 7 hours of sleep."
        )

    else:
        recommendations.append(
            "Your sleep duration is good."
        )


    # Task completion recommendation

    completion_rate = (
        tasks_completed / tasks_planned
    ) * 100

    if completion_rate < 50:
        recommendations.append(
            "Reduce the number of daily tasks and focus on high-priority tasks."
        )

    elif completion_rate < 75:
        recommendations.append(
            "Focus on completing your highest-priority tasks first."
        )

    else:
        recommendations.append(
            "Excellent task completion rate!"
        )


    # Study recommendation

    if study_hours < 3:
        recommendations.append(
            "Try adding another focused study session."
        )

    else:
        recommendations.append(
            "Your study time is good. Maintain consistent sessions."
        )


    return predicted_score, recommendations


# ==========================================
# STEP 10: TEST CHRONOAI
# ==========================================

print("\n========== CHRONOAI RECOMMENDATION ==========")

score, recommendations = generate_recommendation(
    sleep_hours=6,
    screen_time=7,
    tasks_planned=8,
    tasks_completed=4,
    study_hours=2
)


print("\nPredicted Productivity Score:", score)


print("\nChronoAI Recommendations:")

for i, recommendation in enumerate(
    recommendations,
    start=1
):
    print(f"{i}. {recommendation}")