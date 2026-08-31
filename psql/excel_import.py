import pandas as pd
import logging
import sys
import psycopg2
from datetime import datetime, timezone
from db_config import DB_CONFIG

log = logging.getLogger("excel")

EXCEL_FILE = "BXXX_data.xlsx"
# SHEET_NAME = 0  # first sheet
SHEET_NAME = 1  # second sheet: 'esther_reports'

sheet_df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)

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
# selected_indexes = [1, 2, ]
selected_indexes = range(0, 176)
# selected_indexes = [1, 2, ]
# "selected_indexes = [11, 12, 13,14,15,16,17,18, ]
# selected_indexes = [20,21, 22, 23, 24, 25, 26,27,28,29, ]
df = sheet_df.loc[selected_indexes].copy()

# for index, row in df.iterrows():
#    excel_row_number = index + 2
#    print(f"Excel row {excel_row_number}: {row.to_dict()}")

for index, row in df.iterrows():
    excel_row_number = index + 2
    print(f"Excel row {excel_row_number}: {row.to_dict()}")

column_mapping = {
    "Full Name": "name",
    "Age": "age",
    "Monthly Salary": "salary",
    "Dept": "department",
}


def insert_sample(
    curs, utc_datetime, key: str, phase: str, shot_number: int, fvalue: float
):  #:  pd.DataFrame):
    vals = [utc_datetime, key, phase, shot_number, fvalue]
    print(f"Sample: {vals}")
    curs.execute(INSERT_SAMPLE, vals)
    print(curs.query)  # This will show the full SQL query with parameters


def insert_reports(df: pd.DataFrame):
    df["shot_number"] = df["shot_number"].astype("Int32")
    df["manager_id"] = df["manager_id"].astype("Int32")
    df["ambient_temperature"] = df["ambient_temperature"].astype(float)
    df["pt901_target"] = df["pt901_target"].astype(float)
    df["He_ratio_sp"] = df["He_ratio_sp"].astype(float)

    df["datetime"] = pd.to_datetime(df["start_time"], errors="coerce")
    # Extract date and time
    df["date_only"] = df["datetime"].dt.date
    df["time_only"] = df["datetime"].dt.time
    # date_only = start_time.dt.date
    # time_only = start_time.dt.time_only
    # print(shot_number)
    print(df[["datetime", "date_only", "time_only"]])
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            for index, row in df.iterrows():
                with conn.cursor() as cur:
                    shot_number = row["shot_number"]
                    researcher_id = row["manager_id"]
                    # cc_pressure_sp  = row["pt901_target"]  ## not always used
                    cc_pressure_sp = row["filling_pressure_sp"] - 1.0
                    He_ratio_sp = row["He_ratio_sp"]
                    H2_ratio_sp = row["H2_ratio_sp"]
                    O2_ratio_sp = row["O2_ratio_sp"]

                    ambient_temperature = row["ambient_temperature"]
                    ambient_pressure = row["ambient_pressure"]
                    ambient_humidity = row["ambient_humidity"]
                    datetime_pd = row["datetime"]
                    #'float' object has no attribute 'astype'
                    n2_bottle_initial = row["N2_bottle_initial"]
                    o2_bottle_initial = row["O2_bottle_initial"]
                    h2_bottle_initial = row["H_bottle_initial"]
                    he1_bottle_initial = row["He1_bottle_initial"]
                    he2_bottle_initial = row["He2_bottle_initial"]
                    n2_command_bottle_initial = row["N2_command_bottle_initial"]
                    n2_bottle_final = row["N2_bottle_final"]
                    o2_bottle_final = row["O2_bottle_final"]
                    h2_bottle_final = row["H_bottle_final"]
                    he1_bottle_final = row["He1_bottle_final"]
                    he2_bottle_final = row["He2_bottle_final"]
                    n2_command_bottle_final = row["N2_command_bottle_final"]

                    # pt901_target = row['pt901_target']
                    pt901_end_s1 = row["pt901_end_s1"]
                    pt901_end_o = row["pt901_end_o"]
                    pt901_end_he1 = row["pt901_end_he1"]
                    pt901_end_h = row["pt901_end_h"]
                    pt901_end_he2 = row["pt901_end_he2"]
                    cc_range_kistler = row["range_kistler"]
                    delta_P_kistler = row["delta_P_kistler"]

                    # print(f"datetime_pd: {datetime_pd}")

                    if researcher_id == 2:
                        chief_engineer_id = 1
                    else:
                        chief_engineer_id = 2

                    # datetime_value = pd.to_datetime("2026-07-27 12:00:00")
                    datetime_value = pd.to_datetime(datetime_pd)
                    print(f"datetime_value: {datetime_value}")
                    # Convert to Python datetime and then to UTC
                    utc_datetime = datetime_value.tz_localize("UTC")
                    #
                    # Convert to Python datetime and then to UTC
                    #

                    vals = [
                        shot_number,
                        "B",
                        shot_number,
                        chief_engineer_id,
                        researcher_id,
                        cc_pressure_sp,
                        He_ratio_sp,
                        H2_ratio_sp,
                        O2_ratio_sp,
                    ]
                    cur.execute(INSERT_REPORT, vals)
                    log.debug("Inserted row %d (rowcount=%d)", index, cur.rowcount)
                    print(
                        cur.query
                    )  # This will show the full SQL query with parameters
                    print(
                        f"shot_number: {shot_number}, researcher_id: {researcher_id}, ambient_t {ambient_temperature}"
                    )
                    print(f"reports: {vals}")
                    insert_sample(
                        cur,
                        utc_datetime,
                        "ambient_temperature",
                        "CC_start",
                        shot_number,
                        ambient_temperature,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "ambient_pressure",
                        "CC_start",
                        shot_number,
                        ambient_pressure,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "ambient_humidity",
                        "CC_start",
                        shot_number,
                        ambient_humidity,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT101",
                        "CC_start",
                        shot_number,
                        n2_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT201",
                        "CC_start",
                        shot_number,
                        o2_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT301",
                        "CC_start",
                        shot_number,
                        he1_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT401",
                        "CC_start",
                        shot_number,
                        h2_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT501",
                        "CC_start",
                        shot_number,
                        he2_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT801",
                        "CC_start",
                        shot_number,
                        n2_command_bottle_initial,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT101",
                        "CC_end",
                        shot_number,
                        n2_bottle_final,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT201",
                        "CC_end",
                        shot_number,
                        o2_bottle_final,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT301",
                        "CC_end",
                        shot_number,
                        he1_bottle_final,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT401",
                        "CC_end",
                        shot_number,
                        h2_bottle_final,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT501",
                        "CC_end",
                        shot_number,
                        he2_bottle_final,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT801",
                        "CC_end",
                        shot_number,
                        n2_command_bottle_final,
                    )

                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT901",
                        "CC_purge_end",
                        shot_number,
                        pt901_end_s1,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT901",
                        "CC_o2_end",
                        shot_number,
                        pt901_end_o,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT901",
                        "CC_he1_end",
                        shot_number,
                        pt901_end_he1,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT901",
                        "CC_h2_end",
                        shot_number,
                        pt901_end_h,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "PT901",
                        "CC_he2_end",
                        shot_number,
                        pt901_end_he2,
                    )

                    insert_sample(
                        cur,
                        utc_datetime,
                        "cc_range_kistler",
                        "CC_pulse",
                        shot_number,
                        cc_range_kistler,
                    )
                    insert_sample(
                        cur,
                        utc_datetime,
                        "cc_deltaP_kistler",
                        "CC_pulse",
                        shot_number,
                        delta_P_kistler,
                    )
                    # insert_sample(cur, utc_datetime, 'PT901', 'CC_he1_end', shot_number, pt901_end_)
                    # Print the full query
    except psycopg2.Error as exc:
        log.error("Database error: %s", exc)


# -----------------------------
# Convert field types
# -----------------------------
# start_time= selected_df["start_time"]
# selected_df["shot_number"] = selected_df["shot_number"].astype("Int32")
# selected_df["manager_id"] = selected_df["manager_id"].astype("Int32")
# selected_df["ambient_temperature"] = selected_df["ambient_temperature"].astype(float)
# selected_df["pt901_target"] = selected_df["pt901_target"].astype(float)
# selected_df["He_ratio_sp"] = selected_df["He_ratio_sp"].astype(float)
#
df["datetime"] = pd.to_datetime(df["start_time"], errors="coerce")
# # Extract date and time
# selected_df["date_only"] = selected_df["datetime"].dt.date
# selected_df["time_only"] = selected_df["datetime"].dt.time
# date_only = start_time.dt.date
# time_only = start_time.dt.time_only
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
insert_reports(df)


# print(f"date_only: {date_only}i, time_only: {time_only}")
# print(start_time)
# selected_df["name"] = selected_df["name"].astype(str)
# selected_df["age"] = pd.to_numeric(selected_df["age"], errors="coerce").astype("Int64")
# selected_df["salary"] = pd.to_numeric(selected_df["salary"], errors="coerce")
# selected_df["department"] = selected_df["department"].astype(str)


# Optional: remove rows with missing required values
# selected_df = selected_df.dropna(subset=["name", "age", "salary"])


# df = df.rename(columns=column_mapping)
