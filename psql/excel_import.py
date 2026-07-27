import pandas as pd
import logging
import sys
import psycopg2
from datetime import datetime, timezone
from db_config import DB_CONFIG

log = logging.getLogger("excel")

EXCEL_FILE = "BXXX_data.xlsx"
#SHEET_NAME = 0  # first sheet
SHEET_NAME = 1  # second sheet +esther_reports'


df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

print("\nExcel rows found:\n")


INSERT_REPORT = (
    "INSERT INTO reports "
    "(id, series_name, shot, chief_engineer_id, researcher_id, cc_pressure_sp, he_sp, h2_sp, o2_sp) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
INSERT_SAMPLE = (
    "INSERT INTO sample "
    "(time_date, short_name, pulse_phase, reports_id, float_val) "
    "VALUES (%s, %s, %s, %s, %s)"
)

selected_indexes = [1, ]
selected_df = df.loc[selected_indexes].copy()

#for index, row in df.iterrows():
#    excel_row_number = index + 2
#    print(f"Excel row {excel_row_number}: {row.to_dict()}")

for index, row in selected_df.iterrows():
    excel_row_number = index + 2
    print(f"Excel row {excel_row_number}: {row.to_dict()}")

column_mapping = {
    "Full Name": "name",
    "Age": "age",
    "Monthly Salary": "salary",
    "Dept": "department"
}
def insert_sample(curs, utc_datetime, key: str, phase: str, shot_number: int, fvalue: float):  #:  pd.DataFrame):
    vals = [utc_datetime, key, phase, shot_number, fvalue]
    print(f"Sample: {vals}")
    curs.execute(INSERT_SAMPLE, vals)
    print(curs.query)  # This will show the full SQL query with parameters

def insert_reports(df:  pd.DataFrame):
    df["shot_number"] = selected_df["shot_number"].astype("Int32")
    df["manager_id"] = df["manager_id"].astype("Int32")
    df["ambient_temperature"] = df["ambient_temperature"].astype(float)
    df["pt901_target"] = df["pt901_target"].astype(float)
    df["He_ratio_sp"] = df["He_ratio_sp"].astype(float)

    df["datetime"] = pd.to_datetime(
        df["start_time"],
        errors="coerce"
    )
# Extract date and time
    df["date_only"] = df["datetime"].dt.date
    df["time_only"] = selected_df["datetime"].dt.time
#date_only = start_time.dt.date
#time_only = start_time.dt.time_only
# print(shot_number)
    print(selected_df[["datetime", "date_only", "time_only"]])
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            for index, row in df.iterrows():
                with conn.cursor() as cur:
                    shot_number= row["shot_number"]
                    researcher_id = row["manager_id"]
                    cc_pressure_sp  = row["pt901_target"]
                    ambient_temperature = row["ambient_temperature"]
                    ambient_pressure = row["ambient_pressure"]
                    ambient_humidity = row["ambient_humidity"]
                    datetime_pd= row["datetime"]
                    n2_bottle_initial = row["N2_bottle_initial"]
                    o2_bottle_initial = row["O2_bottle_initial"]
                    h2_bottle_initial = row["H_bottle_initial"]
                    he1_bottle_initial = row["He1_bottle_initial"]
                    he2_bottle_initial = row["He2_bottle_initial"]
                    n2_command_bottle_initial= row["N2_command_bottle_initial"]
                    #print(f"datetime_pd: {datetime_pd}")

                    if researcher_id == 2: 
                        chief_engineer_id = 1
                    else:
                        chief_engineer_id = 2

                    #datetime_value = pd.to_datetime("2026-07-27 12:00:00")
                    datetime_value = pd.to_datetime(datetime_pd)
                    print(f"datetime_value: {datetime_value}")
                    #Convert to Python datetime and then to UTC
                    utc_datetime = datetime_value.tz_localize('UTC')
#
                    # Convert to Python datetime and then to UTC
                    #

                    vals = [shot_number, 'B', shot_number, chief_engineer_id, researcher_id, cc_pressure_sp, 2.0, 1.2, 1.2]
                    cur.execute(INSERT_REPORT, vals)
                    log.debug(
                        "Inserted row %d (rowcount=%d)", index, cur.rowcount
                    )
                    print(cur.query)  # This will show the full SQL query with parameters
                    print(f"shot_number: {shot_number}, researcher_id: {researcher_id}, ambient_t {ambient_temperature}")
                    print(f"reports: {vals}")
                    insert_sample(cur, utc_datetime, 'ambientTemperature', 'CC_Start', shot_number, ambient_temperature)
                    insert_sample(cur, utc_datetime, 'ambientPressure', 'CC_Start', shot_number, ambient_pressure)
                    insert_sample(cur, utc_datetime, 'ambientHumidity', 'CC_Start', shot_number, ambient_humidity)
                    insert_sample(cur, utc_datetime, 'PT101', 'CC_Start', shot_number, n2_bottle_initial)
                    insert_sample(cur, utc_datetime, 'PT201', 'CC_Start', shot_number, o2_bottle_initial)
                    # Print the full query
    except psycopg2.Error as exc:
        log.error("Database error: %s", exc)


# -----------------------------
# Convert field types
# -----------------------------
#start_time= selected_df["start_time"] 
# selected_df["shot_number"] = selected_df["shot_number"].astype("Int32")
# selected_df["manager_id"] = selected_df["manager_id"].astype("Int32")
# selected_df["ambient_temperature"] = selected_df["ambient_temperature"].astype(float)
# selected_df["pt901_target"] = selected_df["pt901_target"].astype(float)
# selected_df["He_ratio_sp"] = selected_df["He_ratio_sp"].astype(float)
#
selected_df["datetime"] = pd.to_datetime(
    selected_df["start_time"],
    errors="coerce"
)
# # Extract date and time
# selected_df["date_only"] = selected_df["datetime"].dt.date
# selected_df["time_only"] = selected_df["datetime"].dt.time
#date_only = start_time.dt.date
#time_only = start_time.dt.time_only
# print(shot_number)
# print(selected_df[["datetime", "date_only", "time_only"]])
# try:
#     with psycopg2.connect(**DB_CONFIG) as conn:
#         with conn.cursor() as cur:
#             for index, row in selected_df.iterrows():
#                 shot_number= row["shot_number"]
#                 researcher_id = row["manager_id"]
#                 cc_pressure_sp  = row["pt901_target"]
#                 ambient_temperature = row["ambient_temperature"]
#
#                 if researcher_id == 2: 
#                     chief_engineer_id = 1
#                 else:
#                     chief_engineer_id = 2
#
#                 vals = [shot_number, 'B', shot_number, chief_engineer_id, researcher_id, cc_pressure_sp, 2.0, 1.2, 1.2]
#                 cur.execute(INSERT_REPORT, vals)
#                 log.debug(
#                     "Inserted row %d (rowcount=%d)", index, cur.rowcount
#                 )
#                 print(f"shot_number: {shot_number}, researcher_id: {researcher_id}, ambient_t {ambient_temperature}")
#                 print(vals)
# except psycopg2.Error as exc:
#     log.error("Database error: %s", exc)
insert_reports(selected_df)


#print(f"date_only: {date_only}i, time_only: {time_only}")
#print(start_time)
#selected_df["name"] = selected_df["name"].astype(str)
#selected_df["age"] = pd.to_numeric(selected_df["age"], errors="coerce").astype("Int64")
#selected_df["salary"] = pd.to_numeric(selected_df["salary"], errors="coerce")
#selected_df["department"] = selected_df["department"].astype(str)


# Optional: remove rows with missing required values
#selected_df = selected_df.dropna(subset=["name", "age", "salary"])



#df = df.rename(columns=column_mapping)
