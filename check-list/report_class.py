#!/usr/bin/env python3
""" """

import argparse
import psycopg2
# import sys

from config_psql_local import DB_CONFIG
from epics import caget  # , caput  # , cainfo

## cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

BOTTLES_CHANNELS = [
    {"name": "PT101", "pv": "Esther:gas:PT101"},
    {"name": "PT201", "pv": "Esther:gas:PT201"},
    {"name": "PT301", "pv": "Esther:gas:PT301"},
    {"name": "PT401", "pv": "Esther:gas:PT401"},
    {"name": "PT501", "pv": "Esther:gas:PT501"},
    {"name": "PT801", "pv": "Esther:gas:PT801"},
]


class EstherReport:
    """ """

    def __init__(self, shotId=None):
        """
        Initializes the DB connection
        """
        self.conn = psycopg2.connect(**DB_CONFIG)

        # self.dictCursor = self.conn.cursor(
        #    cursor_factory=psycopg2.extras.RealDictCursor
        # )
        if shotId is None:
            """
            cursor = self.conn.cursor()
            query = "SELECT id FROM reports ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            """
            result = self.GetLastShot()
            if result is not None:
                self.id = result[0]
        else:
            cursor = self.conn.cursor()
            query = "SELECT id FROM reports WHERE id=%s"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            if result is not None:
                self.id = result[0]
        print(f"Report ID: {self.id}")

    def GetLastShot(self):
        cursor = self.conn.cursor()
        query = "SELECT id FROM reports ORDER BY id DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result

    def InsertRecords(self, insertQuery, params=None):
        cursor = self.conn.cursor()

        try:
            cursor.execute(insertQuery, params)
            # Commit the transaction
            self.conn.commit()
            # print(f"Inserted {iD}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the cursor and connection
            print(f"query {cursor.query}")
            cursor.close()

    def SaveBottlePressures(self, phase):
        cursor = self.conn.cursor()
        for b in BOTTLES_CHANNELS:
            pval = caget(b["pv"])
            query = (
                "INSERT INTO sample "
                "(time_date, reports_id, short_name, pulse_phase, float_val) "
                "VALUES (current_timestamp, %s, %s, %s, %s)"
            )
            par = (
                self.id,
                b["name"],
                phase,
                pval,
            )
            print(f"query {query}")
            print(f"par {par}")
            self.InsertRecords(query, par)
            #    print(c._last_executed)
            # raise ValueError


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Function to manipulated Esther Reports"
    )
    parser.add_argument(
        "-n", "--newReport", action="store_true", help="Insert new Report"
    )
    parser.add_argument("-t", "--test", action="store_true", help="Insert test")
    parser.add_argument(
        "-b", "--bottles", action="store_true", help="Store bottle pressures"
    )
    parser.add_argument(
        "-e", "--bottle_end", action="store_true", help="Store final bottle pressures"
    )
    parser.add_argument("-i", "--import", action="store_true", help="Import Old Shot")
    parser.add_argument("-r", "--report", type=int, default=316, help="Report number")
    parser.add_argument("-s", "--shot", type=int, default=216, help="Shot number")
    parser.add_argument(
        "-p", "--pressure", type=float, default=40.2, help="cc_pressure_sp"
    )

    # Id, shot = dB.GetLastShot()
    # result = dB.GetLastShot(series='S')
    # print(result)
    # print(f"Id {Id}, {shot}")
    args = parser.parse_args()
    if args.newReport:
        # Id, shot = dB.InsertShot("S", args.shot + 1, 3, 1)
        # from config_psql_local import DB_CONFIG
        #
        query = (
            "INSERT INTO reports "
            "(series_name,shot,chief_engineer_id,researcher_id,"
            "cc_pressure_sp,he_sp,h2_sp,o2_sp) "
            "VALUES ('S',%s, %s, %s, %s, %s, %s, %s)"
        )
        dB = EstherReport()
        par = (
            args.shot,
            3,
            1,
            args.pressure,
            8,
            2,
            1.2,
        )
        dB.InsertRecords(query, par)
        """
        cursor = dB.conn.cursor()

        try:
            cursor.execute(
                query,
                (
                    args.shot,
                    3,
                    1,
                    args.pressure,
                    8,
                    2,
                    1.2,
                ),
            )
            dB.conn.commit()
            # iD = cursor.fetchone()[0]
            # print(f"Inserted {iD}")
            # Commit the transaction
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the cursor and connection
            print(f"query {cursor.query}")
            cursor.close()
            # dB.conn.rollback()
        """

        # dB.SaveBottlePressures(Id, 'CC_Start')
        # dB.SaveBottlePressures(Id, 'End')
        exit()
    if args.bottles:
        # result = dB.GetLastShot(series='E')
        # result = dB.GetPulseData(207)
        # result = dB._gBottlePressures(args.shot, "CC_Start")
        report = EstherReport()
        if args.bottle_end:
            report.SaveBottlePressures("CC_End")
        else:
            report.SaveBottlePressures("CC_Start")
