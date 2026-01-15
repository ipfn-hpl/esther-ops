#!/home/esther/.local/venvs/python-epics/bin/python3
#
#!/usr/bin/env python3
"""
https://stackoverflow.com/questions/8241099/executing-tasks-in-parallel-in-python


https://mysqlclient.readthedocs.io/user_guide.html

Detect Mode:
        This mode allows you to determine the IP addresses that are in the network in streaming mode. By default, the search takes 5 seconds.

ssh -X -t golem 'cd /home/esther/git-repos/esther-ops/reports; zsh -l'

"""

import argparse
import MySQLdb

# import numpy as np
import pandas as pd

# Local module with DB configuration
import config

from getMeteoLisbon import readMeteo

BOTTLES_CHANNELS = [
    {"name": "PT101", "pv": "Esther:gas:PT101"},
    {"name": "PT201", "pv": "Esther:gas:PT201"},
    {"name": "PT301", "pv": "Esther:gas:PT301"},
    {"name": "PT401", "pv": "Esther:gas:PT401"},
    {"name": "PT501", "pv": "Esther:gas:PT501"},
    {"name": "PT801", "pv": "Esther:gas:PT801"},
]

PT901_VALS = [
    {"name": "PP_initial", "channel": "PT901", "phase": "CC_Step1_End"},
    {"name": "PP_O2", "channel": "PT901", "phase": "CC_Step3_End"},
    {"name": "PP_He1", "channel": "PT901", "phase": "CC_Step4_End"},
    {"name": "PP_H2", "channel": "PT901", "phase": "CC_Step6_End"},
    {"name": "PP_He2", "channel": "PT901", "phase": "CC_Step7_End"},
]

PULSE_VALS = [
    {"name": "Room T", "channel": "ambientTemperature", "phase": "CC_Start"},
    {"name": "Room P", "channel": "ambientPressure", "phase": "CC_Start"},
    {"name": "PP_initial", "channel": "PT901", "phase": "CC_Step1_End"},
    {"name": "PP_O2", "channel": "PT901", "phase": "CC_Step3_End"},
    {"name": "PP_He1", "channel": "PT901", "phase": "CC_Step4_End"},
    {"name": "PP_H2", "channel": "PT901", "phase": "CC_Step6_End"},
    {"name": "PP_He2", "channel": "PT901", "phase": "CC_Step7_End"},
    {"name": "Post Shot dP", "channel": "CC_DeltaP_Kistler", "phase": "CC_Ignition"},
    {"name": "Range Kistler", "channel": "CC_Range_Kistler", "phase": "CC_Ignition"},
]

VOLUME_DRIVER = 50.35
TEMPERATURE_REF = 273.15  # K
INV_FLOW_He_MAX = 0.9 / 50 + 0.1 / 10  # mn / ln
FLOW_O2_MAX = 2000 / 60  # ln / mn
FLOW_H2_MAX = 2000 / 60  # ln / mn


class EstherDB:
    """ """

    def __init__(self):
        """
        Initializes the DB connection
        """
        db = MySQLdb.connect(
            host=config.host,
            user=config.username,
            password=config.password,
            database=config.database,
        )
        self.db = db
        self.cursor = db.cursor()
        self.curDict = db.cursor(MySQLdb.cursors.DictCursor)
        self.lastShotId = 300
        self.lastShotNo = 100
        self.PrepPLC = []
        self.GetLastShot()
        self.pulseData = {}

    def ImportOldShot(self, shot, series="S"):
        dbOld = MySQLdb.connect(
            host="localhost", user="archive", password="$archive", database="archive"
        )

        co = dbOld.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM esther_reports WHERE shot_number = %s"
        co.execute(query, (shot,))
        reportO = co.fetchone()
        if reportO is not None:
            c = self.db.cursor()
            query = (
                "INSERT INTO reports "
                "(id, series_name,shot,chief_engineer_id,researcher_id,"
                "cc_pressure_sp,He_sp,H2_sp,O2_sp) "
                "VALUES (%s,%s,%s, %s, %s, %s, %s, %s, %s)"
            )
            vals = (
                reportO["shot_number"],
                "S",
                reportO["shot_number"] - 200,
                reportO["manager_id"],
                "1",
                reportO["filling_pressure_sp"],
                reportO["He_ratio_sp"],
                reportO["H2_ratio_sp"],
                reportO["O2_ratio_sp"],
            )
            try:
                c.execute(query, vals)
            except MySQLdb._exceptions.IntegrityError:
                print("Import, Duplicate entry ")
            queryStart = (
                "INSERT INTO complete "
                "(id,shot,time_date,item_id,complete_status_id) "
                "VALUES (NULL, %s, %s, 1, 0)"
            )
            valStart = (
                reportO["shot_number"],
                reportO["start_time"],
            )
            try:
                c.execute(queryStart, valStart)
                # MySQLdb._exceptions.IntegrityError
            except MySQLdb._exceptions.IntegrityError:
                print("Start  Duplicate entry ")
            querySamples = (
                "INSERT INTO sample "
                "(time_date,short_name,pulse_phase,reports_id,float_val) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            colsOld = [
                "ambient_temperature",
                "ambient_pressure",
                "ambient_humidity",
                "pt901_end_s1",
                "pt901_end_o",
                "pt901_end_he1",
                "pt901_end_h",
                "pt901_end_he2",
                "delta_P_kistler",
                "range_kistler",
                "rest_time",
            ]
            phase = [
                "CC_Start",
                "CC_Start",
                "CC_Start",
                "CC_Step1_End",
                "CC_Step3_End",
                "CC_Step4_End",
                "CC_Step6_End",
                "CC_Step7_End",
                "CC_Ignition",
                "CC_Ignition",
                "CC_Ignition",
            ]
            cols = [
                "ambientTemperature",
                "ambientPressure",
                "ambientHumidity",
                "PT901",
                "PT901",
                "PT901",
                "PT901",
                "PT901",
                "CC_DeltaP_Kistler",
                "CC_Range_Kistler",
                "CC_Rest_Time",
            ]
            for count, cOld in enumerate(colsOld):
                valS = (
                    reportO["start_time"],
                    cols[count],
                    phase[count],
                    reportO["shot_number"],
                    reportO[cOld],
                )
                print(valS)
                try:
                    c.execute(querySamples, valS)
                    # MySQLdb._exceptions.IntegrityError
                except MySQLdb._exceptions.IntegrityError:
                    print("Sample  Duplicate entry ")
            colsOld = [
                "N2_bottle_initial",
                "O2_bottle_initial",
                "He1_bottle_initial",
                "H_bottle_initial",
                "He2_bottle_initial",
                "N2_command_bottle_initial",
            ]
            cols = [
                "PT101",
                "PT201",
                "PT301",
                "PT401",
                "PT501",
                "PT801",
            ]
            for count, cOld in enumerate(colsOld):
                valS = (
                    reportO["start_time"],
                    cols[count],
                    "CC_Start",
                    reportO["shot_number"],
                    reportO[cOld],
                )
                # print(valS)
                try:
                    c.execute(querySamples, valS)
                except MySQLdb._exceptions.IntegrityError:
                    print("Sample  Duplicate entry ")
            colsOld = [
                "N2_bottle_final",
                "N2_bottle_final",
                "He1_bottle_final",
                "H_bottle_final",
                "He2_bottle_final",
                "N2_command_bottle_final",
            ]
            for count, cOld in enumerate(colsOld):
                valS = (
                    reportO["start_time"],
                    cols[count],
                    "End",
                    reportO["shot_number"],
                    reportO[cOld],
                )
                # print(valS)
                try:
                    c.execute(querySamples, valS)
                except MySQLdb._exceptions.IntegrityError:
                    print("Sample  Duplicate entry ")
            self.db.commit()
            # print(vals)
        return co.fetchone()

    def GetShotId(self, shot, series="S"):
        c = self.cursor
        query = "SELECT id FROM reports WHERE shot = %s AND series_name = %s"
        c.execute(query, (shot, series))
        fo = c.fetchone()
        if fo is not None:
            return fo[0]
        # return c.fetchone()

    def PrepShot(self, shot_id, heRatio=0.66):
        # curDict = self.db.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM reports WHERE id = %s"
        self.curDict.execute(query, (shot_id,))
        fo = self.curDict.fetchone()
        # ambient = readMeteo()

        meteoLisbon = readMeteo()
        # ambient['T'] = 20  # Celsius
        # ambient['P'] = 1013  # mBar
        if fo is not None:
            cols = ["He0", "O2", "He1", "H2", "He2", "Sum"]
            data = []
            sumSp = fo["O2_sp"] + fo["He_sp"] + fo["H2_sp"]
            ppHe0 = meteoLisbon["PressureLisbon"] / 1000.0
            mfHe0 = ppHe0 / fo["cc_pressure_sp"]  #
            mfO2 = fo["O2_sp"] / sumSp
            mfHe1 = heRatio * fo["He_sp"] / sumSp - mfHe0
            mfH2 = fo["H2_sp"] / sumSp
            mfHe2 = (1.0 - heRatio) * fo["He_sp"] / sumSp
            sumMf = mfHe0 + mfO2 + mfHe1 + mfH2 + mfHe2
            # "Molar Fraction Setpoint",
            row = [
                mfHe0,
                mfO2,
                mfHe1,
                mfH2,
                mfHe2,
                sumMf,
            ]
            data.append(row)
            #
            # "P_partial (amb)",
            row = [ppHe0]
            ppO2 = mfO2 * fo["cc_pressure_sp"]
            row.append(ppO2)
            ppHe1 = mfHe1 * fo["cc_pressure_sp"]
            # ppHe1 = (1.0 - heRatio) * fo['He_sp'] / sumSp * \
            #    fo['cc_pressure_sp'] + ppO2
            row.append(ppHe1)
            ppH2 = mfH2 * fo["cc_pressure_sp"]
            row.append(ppH2)
            ppHe2 = mfHe2 * fo["cc_pressure_sp"]
            # ppHe2 = heRatio * fo['He_sp'] / sumSp * \
            #    fo['cc_pressure_sp'] + ppH2
            row.append(ppHe2)
            sumPp = ppHe0 + ppO2 + ppHe1 + ppH2 + ppHe2
            # row.append(fo['cc_pressure_sp'])
            row.append(sumPp)
            # fo['cc_pressure_sp'])
            data.append(row)
            #
            # "P_partial (ref)",
            Tcorr = TEMPERATURE_REF / (
                meteoLisbon["TemperatureLisbon"] + TEMPERATURE_REF
            )
            ppHe0ref = ppHe0 * Tcorr
            row = [ppHe0ref]
            ppO2ref = ppO2 * Tcorr
            row.append(ppO2ref)
            # row.append(ppO2ref)
            ppHe1ref = ppHe1 * Tcorr
            row.append(ppHe1ref)
            ppH2ref = ppH2 * Tcorr
            row.append(ppH2ref)
            ppHe2ref = ppHe2 * Tcorr  # // ambient['T'] * TEMPERATURE_REF
            row.append(ppHe2ref)
            data.append(row)
            #
            # "Liter (ambient)"
            row = [VOLUME_DRIVER]
            volO2 = ppO2 * VOLUME_DRIVER
            row.append(volO2)
            volHe1 = ppHe1 * VOLUME_DRIVER
            row.append(volHe1)
            volH2 = ppH2 * VOLUME_DRIVER
            row.append(volH2)
            volHe2 = ppHe2 * VOLUME_DRIVER
            row.append(volHe2)
            data.append(row)
            #
            # "Liter (ref)",
            row = [VOLUME_DRIVER * Tcorr]
            volO2ref = ppO2ref * VOLUME_DRIVER
            row.append(volO2ref)
            volHe1ref = ppHe1ref * VOLUME_DRIVER
            row.append(volHe1ref)
            volH2ref = ppH2ref * VOLUME_DRIVER
            row.append(volH2ref)
            volHe2ref = ppHe2ref * VOLUME_DRIVER
            row.append(volHe2ref)
            data.append(row)

            TimeHe0 = 10  # min
            row = [TimeHe0]
            TimeO2 = volO2ref / FLOW_O2_MAX
            row.append(TimeO2)
            TimeHe1 = volHe1ref * INV_FLOW_He_MAX
            row.append(TimeHe1)
            TimeH2 = volH2ref / FLOW_O2_MAX
            row.append(TimeH2)
            TimeHe2 = volHe2ref * INV_FLOW_He_MAX
            row.append(TimeHe2)
            SumTime = TimeHe0 + TimeO2 + TimeHe1 + TimeH2 + TimeHe2
            row.append(SumTime)
            data.append(row)
            #
            # "P_acum (amb)"
            row = [ppHe0]
            ppO2acum = ppHe0 + ppO2
            row.append(ppO2acum)
            ppHe1acum = ppO2acum + ppHe1
            row.append(ppHe1acum)
            ppH2acum = ppHe1acum + ppH2
            row.append(ppH2acum)
            ppHe2acum = ppH2acum + ppHe2
            row.append(ppHe2acum)
            row.append(fo["cc_pressure_sp"])
            data.append(row)
            # "P_acum (amb)"
            row = [0.0]
            ppO2acum = ppO2
            row.append(ppO2acum)
            ppHe1acum = ppO2acum + ppHe1
            row.append(ppHe1acum)
            ppH2acum = ppHe1acum + ppH2
            row.append(ppH2acum)
            ppHe2acum = ppH2acum + ppHe2
            row.append(ppHe2acum)
            row.append(fo["cc_pressure_sp"] - ppHe0)
            data.append(row)
            self.PrepPLC = row
            #
            df = pd.DataFrame(
                data,
                columns=cols,
            )
            # breakpoint()
            df.index = [
                "Molar Fraction Setpoint",
                "P_partial (amb)",
                "P_partial (ref)",
                "Liter (ambient)",
                "Liter (ref)",
                "Fill Time / min",
                "P_acum (amb)",
                "P_acum (relative)",
            ]
            self.pulseDf = df
            return df

    def GetLastShot(self, series="S"):
        # c = self.cursor
        curDict = self.db.cursor(MySQLdb.cursors.DictCursor)
        query = "SELECT * FROM reports WHERE series_name = %s ORDER BY id DESC LIMIT 1"
        curDict.execute(query, series)
        fo = curDict.fetchone()
        if fo is not None:
            # print(result)
            self.lastShotId = fo["id"]
            self.lastShotNo = fo["shot"]
        return fo

    def InsertShot(self, series, shot, ce, re):
        # ALTER TABLE reports AUTO_INCREMENT=301;
        # c = self.db.cursor()
        c = self.cursor
        query = (
            "INSERT INTO reports "
            "(id, series_name, shot, chief_engineer_id, researcher_id) "
            "VALUES (NULL, %s, %s, %s, %s)"
        )
        try:
            c.execute(
                query,
                (
                    series,
                    shot,
                    ce,
                    re,
                ),
            )
        except MySQLdb._exceptions.IntegrityError:
            print("1062, Duplicate entry ")
            #  print("1062, Duplicate entry 'S-101' for key 'esther_series_name'")
            # print(query)
            raise ValueError

        # new_id, shot =
        self.GetLastShot()
        new_id = self.lastShotId
        meteoLisbon = readMeteo()
        # breakpoint()
        query = (
            "INSERT INTO sample "
            "(time_date, reports_id, short_name, pulse_phase, float_val) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        if meteoLisbon is not None:
            try:
                c.executemany(
                    query,
                    [
                        (
                            meteoLisbon["TimeLisbon"],
                            new_id,
                            "ambientTemperature",
                            "CC_Start",
                            meteoLisbon["TemperatureLisbon"],
                        ),
                        (
                            meteoLisbon["TimeLisbon"],
                            new_id,
                            "ambientPressure",
                            "CC_Start",
                            meteoLisbon["PressureLisbon"],
                        ),
                        (
                            meteoLisbon["TimeLisbon"],
                            new_id,
                            "ambientHumidity",
                            "CC_Start",
                            meteoLisbon["HumidityLisbon"],
                        ),
                    ],
                )
                # MySQLdb._exceptions.IntegrityError
            except MySQLdb._exceptions.IntegrityError:
                print("1062, Duplicate entry ")
        query = (
            "INSERT INTO complete VALUES (NULL, %s, current_timestamp(), 1 , 0, NULL)"
        )
        try:
            c.execute(query, (new_id,))
        except MySQLdb._exceptions.IntegrityError:
            print("Item complete, Duplicate entry ")

        self.db.commit()
        # return self.GetLastShot(series)
        return new_id, self.lastShotNo

    def GetPulsePlot(self, shot_id):
        c = self.cursor
        query = "SELECT name FROM plot_file WHERE reports_id = %s "
        c.execute(query, (shot_id,))
        fo = c.fetchone()
        if fo is not None:
            return fo[0]
        else:
            print(c._last_executed)

    def FetchPulseData(self, shot_id):
        # c = self.db.cursor()
        c = self.cursor

        ddict = {}
        for p in PULSE_VALS:
            query = (
                "SELECT float_val FROM sample "
                "WHERE reports_id = %s "
                "AND short_name = %s "
                "AND pulse_phase = %s"
            )
            c.execute(
                query,
                (
                    shot_id,
                    p["channel"],
                    p["phase"],
                ),
            )
            fo = c.fetchone()
            if fo is not None:
                ddict[p["name"]] = fo[0]
            else:
                print("No ddict data: ", end="")
                print(c._last_executed)
                return None
                #  ddict[p['name']] = fv[0]
        # dict_keys(['Room T', 'Room P', 'PP_initial', 'PP_O2', 'PP_He1', 'PP_H2', 'PP_He2', 'Post Shot dP', 'Range Kistler', 'Measured P', 'Final P', 'Mf_O2'])
        if len(ddict) == 9:
            try:
                ddict["Measured P"] = (
                    ddict["Room P"] / 1000.0 - ddict["PP_initial"] + ddict["PP_He2"]
                )
                ddict["Final P"] = ddict["Measured P"] + ddict["Post Shot dP"]
                ddict["Mf_O2"] = (ddict["PP_O2"] - ddict["PP_initial"]) / ddict[
                    "Measured P"
                ]
            except TypeError:
                print("unsupported operand type(s) for /: 'NoneType' and 'float'")
                # breakpoint()
        self.pulseData = ddict
        # breakpoint()
        return ddict

    def GetPulseData(self, shot_id):
        # c = self.db.cursor()
        c = self.cursor
        data = []
        cols = []

        for p in PULSE_VALS:
            query = (
                "SELECT float_val FROM sample "
                "WHERE reports_id = %s "
                "AND short_name = %s "
                "AND pulse_phase = %s"
            )
            c.execute(
                query,
                (
                    shot_id,
                    p["channel"],
                    p["phase"],
                ),
            )
            fo = c.fetchone()
            if fo is None:
                data.append(None)
                cols.append(None)
                print("No data: ", end="")
                print(c._last_executed)
                return None
            else:
                data.append(fo[0])
                cols.append(p["name"])
                #  ddict[p['name']] = fv[0]

        if len(cols) == 9:
            try:
                data.append(data[1] / 1000.0 - data[2] + data[6])
                cols.append("Measured P")  # 9
                data.append(data[9] + data[7])  # 10
                cols.append("Final P")
                # except TypeError:
                #    print(f'Len data : {len(data)}')

                # Tot_Gas = data[6] - data[2]
                # Molar Fraction
                Mf_O2 = (data[3] - data[2]) / data[9]
                Mf_H2 = (data[5] - data[4]) / data[9]
                Mf_He = 1.0 - Mf_O2 - Mf_H2
                # Stoichiometric Ratios
                Sr_H2 = 2.0  # Definition
                Sr_O2 = Mf_O2 * Sr_H2 / Mf_H2
                Sr_He = Mf_He * Sr_H2 / Mf_He
                print(f"Mf_O2: {Mf_O2}, Mf_H2 {Mf_H2}, Mf_He {Mf_He}")
                cols.append("Ratio O2")
                data.append(Sr_O2)
                cols.append("Ratio H2")
                data.append(Sr_H2)
                cols.append("Ratio He")
                data.append(Sr_He)  # 10
                print(f"Sr_O2: {Sr_O2:.2f}, Sr_He {Sr_He:.2f}")
            except TypeError:
                print("unsupported operand type(s) for /: 'NoneType' and 'float'")
                # breakpoint()

        # print(c._last_executed)
        df = pd.DataFrame(
            [data],
            columns=cols,
        )
        df.index = [
            f"Pulse Id {shot_id}",
        ]
        return df

    def _gBottlePressures(self, shot_id, phase):
        c = self.cursor
        query = (
            "SELECT short_name, float_val FROM sample "
            "WHERE reports_id = %s "
            "AND short_name REGEXP 'PT[1-8]01' "
            "AND pulse_phase = %s"
        )
        c.execute(
            query,
            (
                shot_id,
                phase,
            ),
        )
        fvs = c.fetchmany(16)
        # print(f"len {len(fvs)}")
        if len(fvs) == 6:
            return fvs
        return None

    def GetBottlePressures(self, shot_id):
        # c = self.cursor
        # c = self.db.cursor()
        data = []
        # PHS = ['CC_Start', 'End']
        fvals = self._gBottlePressures(shot_id, "CC_Start")
        if fvals is None:
            return None

        bvals = []
        cols = []
        for r in fvals:
            cols.append(r[0])
            bvals.append(r[1])
        data.append(bvals)
        fvals = self._gBottlePressures(shot_id, "End")
        if fvals is None:
            # Only Initial Values
            df = pd.DataFrame(
                data,
                columns=cols,
            )
            df.index = [
                "Initial",
            ]
            return df

        bvals = []
        for r in fvals:
            bvals.append(r[1])
        data.append(bvals)
        df = pd.DataFrame(
            data,
            columns=cols,
        )
        ddiff = df.diff()
        df = pd.concat([df, ddiff.iloc[[1]]], ignore_index=True)
        df.index = ["Initial", "Final", "Difference"]
        return df
        """
        for ph in PHS:
            bvals = []
            cols = []
            query = ("SELECT short_name, float_val FROM sample "
                     "WHERE reports_id = %s "
                     "AND short_name REGEXP 'PT[1-8]01' "
                     "AND pulse_phase = %s")
            c.execute(query, (shot_id, ph,))
            fvs = c.fetchmany(10)
            print(f"len {len(fvs)}")
            while True:
                fv = c.fetchone()
                if fv is None:
                    # make an empty DataFrame
                    #cols.append(None)
                    #bvals.append(None)
                    break
                cols.append(fv[0])
                bvals.append(fv[1])
            # print(c._last_executed)
            pvals.append(bvals)
        df = pd.DataFrame(
                pvals,
                columns=cols,
        )
        ddiff = df.diff()
        df = pd.concat([df, ddiff.iloc[[1]]], ignore_index=True)
        df.index = ["Initial", "Final", "Difference"]
        # breakpoint()
        return df
        # return np.array(pvals)
        # for b in BOTTLES_CHANNELS:
        #    cols.append(b['name'])
        # bData = {'columns': cols, 'data': np.array(pvals)}
        # bData = {'columns': cols, 'data': pvals}
        # return bData  # np.array(pvals)
        """

    def SaveBottlePressures(self, shot_id, phase):
        from epics import caget  # , caput  # , cainfo

        # c = self.db.cursor()
        c = self.cursor
        for b in BOTTLES_CHANNELS:
            pval = caget(b["pv"])
            query = (
                "INSERT INTO sample "
                "(time_date, reports_id, short_name, pulse_phase, float_val) "
                "VALUES (current_timestamp(), %s, %s, %s, %s)"
            )
            try:
                c.execute(query, (shot_id, b["name"], phase, pval))
            except MySQLdb._exceptions.IntegrityError:
                print("(1062, Duplicate entry ")
                # Print the actual query executed
                print(c._last_executed)
                # raise ValueError
        self.db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Function to manipulated Esther Reports"
    )
    parser.add_argument(
        "-n", "--newReport", action="store_true", help="Insert new Report"
    )
    parser.add_argument("-t", "--test", action="store_true", help="Insert test")
    parser.add_argument("-i", "--imprt", action="store_true", help="Import Old Shot")
    parser.add_argument("-s", "--shot", type=int, default=102, help="Shot number")

    dB = EstherDB()
    # Id, shot = dB.GetLastShot()
    # result = dB.GetLastShot(series='S')
    # print(result)
    # print(f"Id {Id}, {shot}")
    args = parser.parse_args()
    if args.newReport:
        Id, shot = dB.InsertShot("S", args.shot + 1, 3, 1)
        print(f"Inserted {Id}")
        # dB.SaveBottlePressures(Id, 'CC_Start')
        # dB.SaveBottlePressures(Id, 'End')
        exit()
    if args.test:
        # result = dB.GetLastShot(series='E')
        # result = dB.GetPulseData(207)
        result = dB._gBottlePressures(args.shot, "CC_Start")
        if result is not None:
            print(result)
        result = dB.GetBottlePressures(args.shot)
        if result is not None:
            print(result)
        # bottle_pressures(db, 303, 'CC_Start')
        exit()
    if args.imprt:
        result = dB.ImportOldShot(args.shot, series="S")
        if result is not None:
            print(result)
        print("Pulse Data")
        result = dB.GetPulseData(args.shot)
        print(result)
        exit()

    # args = parse_args()
# vim: syntax=python ts=4 sw=4 sts=4 sr et
"""
# print(queryStart)
# print(valStart)
#INSERT INTO `sample` (`time_date`, `short_name`, `pulse_phase`, `reports_id`, `float_val`) VALUES (current_timestamp(), 'ambientPressure', 'CC_Start', '300', '20') 
valSamples = (reportO['start_time'],
                'ambientTemperature',
                'CC_Start',
                reportO['shot_number'],
                reportO['ambient_temperature'],)
print(querySamples)
{'shot_number': 102, 'manager_id': 2, 'start_time': datetime.datetime(2016, 6, 1, 19, 21, 57), 'end_time': datetime.datetime(2016, 6, 1, 19, 40, 53), 'ambient_temperature': Decimal('20.00'), 'ambient_pressure': Decimal('1016.00'), 'ambient_humidity': Decimal('20.00'), 'N2_bottle_initial': 130.163, 'N2_bottle_final': 130.163, 'O2_bottle_initial': 175.447, 'O2_bottle_final': 175.447, 'He1_bottle_initial': 90.3772, 'He1_bottle_final': 90.3772, 'H_bottle_initial': 142.162, 'H_bottle_final': 142.162, 'He2_bottle_initial': 93.5059, 'He2_bottle_final': 93.5059, 'N2_command_bottle_initial': 149.649, 'N2_command_bottle_final': 149.649, 'pt901_end_s1': 0.115, 'pt901_target': 9.0, 'pt901_end_o': 0.94, 'pt901_end_he1': 4.22, 'pt901_end_h': 5.26, 'pt901_end_he2': 7.13, 'wire_voltage': 0, 'wire_time': 0, 'delta_P_kistler': Decimal('0.000'), 'PLC_SW_Version': 'v3.13 He', 'anomalies': 'Filling test only, no ignition', 'mfc_201_O_sp': 1.99, 'mfc_401_H_sp': 3.32, 'mfc_601_HE1_sp': 7.0, 'mfc_601_HE2_sp': 4.43, 'rest_time': 5, 'range_kistler': 50, 'bombe_volume': Decimal('1.860'), 'filling_pressure_sp': Decimal('10.000'), 'He_ratio_sp': Decimal('8.000'), 'H2_ratio_sp': Decimal('2.000'), 'O2_ratio_sp': Decimal('1.200'), 'ignition_source_id': 1, 'ignition_regime_id': 2, 'lens_focal_length': None, 'experiment_number': 0, 'series_id': 0}


db = MySQLdb.connect(host=config.host,
                     user=config.username,
                     password=config.password,
                     database=config.database)

def get_last_shot(db):
    c = db.cursor()
    query = ("SELECT id, shot FROM reports "
             "ORDER BY id DESC LIMIT 1")
    c.execute(query)
    return c.fetchone()


    # c.executemany(
"""
