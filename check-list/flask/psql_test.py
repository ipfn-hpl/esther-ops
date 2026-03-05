import psycopg2
from config_psql import DB_CONFIG
from sql_queries import (
    REPORT_LIST,
    LAST_CHECKED,
    LAST_CHECKLINES,
    MISSING_ITEM,
    NEXT_CHECKLINES,
)

# "SELECT * FROM ("
#
# ") as myAlias ORDER BY id ASC"
conn = psycopg2.connect(**DB_CONFIG)

cursor = conn.cursor()

# cursor.execute("SELECT * FROM reports WHERE id > 1")
limit = 5
cursor.execute(REPORT_LIST, (limit,))

# cursor.execute(REPORT_LIST3, (5,))

# print(cursor.fetchone())
print(cursor.fetchall())
cursor.close()
cursor = conn.cursor()
cursor.execute(
    LAST_CHECKLINES,
    (
        316,
        0,
    ),
)
print(cursor.fetchall())
cursor.close()

# output
