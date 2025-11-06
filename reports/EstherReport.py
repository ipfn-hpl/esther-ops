#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 SQL App for Esther Reports
Python version of http://esther.tecnico.ulisboa.pt/esther-php/show_report.php

 ssh -X -t golem 'cd /home/esther/git-repos/esther-python/sql; zsh -l'
"""

import os
import sys

from PyQt6.QtCore import QSize, QDate, Qt
# from PyQt6 import QtCore

from PyQt6.QtGui import QAction, QIcon, QPixmap  # QFont

from PyQt6.QtSql import (
    QSqlDatabase,
    QSqlRelation,
    # QSqlRelationalDelegate,
    QSqlRelationalTableModel,
    QSqlTableModel,
    QSqlQuery,
    QSqlQueryModel,
)
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QLineEdit, QDateEdit,
    QMainWindow,
    QTableView,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QDialog,
    QDialogButtonBox, QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QRadioButton,
    QLabel,
    QTableWidget, QTableWidgetItem,
    QStatusBar,
    QSlider,
    QToolBar,
    QTabWidget,
    # QSizePolicy,
    QAbstractScrollArea,
)

from ReportFunctions import EstherDB
# import pandas as pd
from TableModels import SimpleModel, PandasModel

import config as cfg
# from epics import caget  # , caput  # , cainfo

# import os

# os.environ['EPICS_CA_ADDR_LIST'] = '10.10.136.128'
# os.environ['EPICS_CA_ADDR_LIST'] = 'localhost 192.168.1.110'
# os.environ['EPICS_CA_AUTO_ADDR_LIST'] = 'NO'

# basedir = os.path.dirname(__file__)

# db = QSqlDatabase("QSQLITE")
#  d b.setDatabaseName(os.path.join(basedir, "chinook.sqlite"))

basedir = os.path.dirname(__file__)

CENTIG_ZERO = 273.15  # K
BAR_TO_ATM = 1.013
# IMAGE_PATH = "/home/esther/git-repos/esther-ops/reports/icons"
IMAGE_PATH = "/home/esther/git-repos/esther-ops/red-pitaya/"

ADJUSTTOCONTENTS_POL = QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents

db = QSqlDatabase("QMARIADB")
db.setHostName(cfg.host)
db.setDatabaseName(cfg.database)
db.setUserName(cfg.username)
db.setPassword(cfg.password)
# db.setPassword("xxx")
# db.open()


def partial_volume(pBar, tempC, chambVolL):
    tempK = tempC + CENTIG_ZERO
    parVol = pBar / BAR_TO_ATM / tempK * CENTIG_ZERO * chambVolL
    return parVol


class NewShotDialog(QDialog):
    def __init__(self, parent=None):  # <1>
        super().__init__(parent)

        # print("Pare: " + str(parent.shotNo))
        self.setWindowTitle("Insert New Shot!")

        buttons = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class SignDialog(QDialog):
    def __init__(self, parent=None):  # <1>
        super().__init__(parent)

        # print("Pare: " + str(parent.shotNo))
        self.setWindowTitle("Sign Line!")

        buttons = (
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.eDb = EstherDB()
        combo = QComboBox()
        combo.addItems(['B', 'S', 'E'])
        combo.setCurrentIndex(1)
        self.series = 'S'
        self.HeRatio = 2 / 3.0
        # combo.currentIndexChanged.connect(self.combo_changed)
        combo.currentTextChanged.connect(self.seriesChanged)
        # shotId, shotNo = self.eDb.GetLastShot()
        self.shotId = self.eDb.lastShotId
        self.lastShotNo = self.eDb.lastShotNo
        self.shotNo = self.lastShotNo
        # self.shotId = 311  # self.lastShotId
        # self.shotNo = 111  # self.lastShotNo
        # self.tableReports = QTableView()
        container = QWidget()
        layoutMain = QHBoxLayout()
        # layoutTools = QVBoxLayout()
        layoutTables = QVBoxLayout()
        if not db.open():
            print("DB not openned")
            sys.exit(-1)
        # model = QSqlTableModel(db=db)
        model = QSqlRelationalTableModel(db=db)
        model.setTable('reports')
        # model.setFilter("shot > 100")
        idx = model.fieldIndex("id")
        model.setSort(idx, Qt.SortOrder.AscendingOrder)
        model.setHeaderData(1, Qt.Orientation.Horizontal, 'Series')
        model.setRelation(3, QSqlRelation("operator", "id", "name"))
        model.setHeaderData(3, Qt.Orientation.Horizontal, 'CE')
        model.setRelation(4, QSqlRelation("operator", "id", "name"))
        model.setHeaderData(4, Qt.Orientation.Horizontal, 'RE')
        model.select()
        self.tableViewReports = QTableView()
        self.tableViewReports.setModel(model)

        # self.search = QLineEdit()

        # add_rec = QPushButton("Add record")
        # add_rec.clicked.connect(self.add_row)

        refreshButt = QPushButton("Refresh")
        refreshButt.clicked.connect(self.updateTables)

#        layoutTools.addWidget(add_rec)
#        self.list = QLineEdit()
#        self.list.setPlaceholderText("1")
#        self.list.textChanged.connect(self.update_query)
        shotSpin = QSpinBox()
        shotSpin.setMinimum(0)
        shotSpin.setMaximum(1000)  # May need to change (hopefully)
# Or: widget.setRange(-10,3)
# widget.setPrefix("$")
# widget.setSuffix("c")
        shotSpin.setSingleStep(1)  # Or e.g. 0.5 for QDoubleSpinBox
        shotSpin.setValue(self.shotNo)
        shotSpin.valueChanged.connect(self.shotChanged)
        # layoutTools.addWidget(shotSpin)

        # tableModelReports = QSqlTableModel(db=db)
        # tableModelReports.setTable('esther_reports')
        self.tabs = QTabWidget()
        summary = QWidget()
        layout = QVBoxLayout()
        layoutF = QFormLayout()
        layoutF.addRow('First Name:', QLineEdit())
        layoutF.addRow('Last Name:', QLineEdit())
        layoutF.addRow('DOB:', QDateEdit(QDate.currentDate()))
        layout.addLayout(layoutF)
        self.labelPlot = QLabel()

        # Add the label to the layout
        layout.addWidget(self.labelPlot)

        summary.setLayout(layout)
        """
        layoutGrd = QGridLayout()
        self.Date = QLabel('Date 11-10-2021 ')
        layoutGrd.addWidget(self.Date, 0, 0)
        self.Manager = QLabel('Manager: Mário Lino da Silva')
        layoutGrd.addWidget(self.Manager, 1, 0)
        self.STime = QLabel('Start Time: 14:21:48')
        layoutGrd.addWidget(self.STime, 2, 0)
        self.RTime = QLabel('Rest Time 00:34:00')
        layoutGrd.addWidget(self.RTime, 3, 0)
        self.AmbTemp = QLabel('Amb. Temp')
        layoutGrd.addWidget(self.AmbTemp, 4, 0)
        """
        self.tabs.addTab(summary, 'Pulse Summary')
        self.tableBottles = QTableView()
        self.tabs.addTab(self.tableBottles, 'Bottle Pressures')
        page = QWidget()
        vlayout = QVBoxLayout()
        self.tablePulseData = QTableView()
        vlayout.addWidget(self.tablePulseData)
        self.tablePulseData2 = QTableView()
        vlayout.addWidget(self.tablePulseData2)
        page.setLayout(vlayout)
        self.tabs.addTab(page, 'Pulse Data')
        # Pulse Preparation
        layout = QVBoxLayout()
        model = QSqlTableModel(db=db)
        model.setTable('reports')
        self.tablePrep = QTableView()
        self.tablePrep2 = QTableView()
        self.tablePrep.setModel(model)
        model.setFilter("id = 207")
        model.select()
        # removeColumns(int column, int count,
        model.removeColumns(0, 1)
        model.removeColumns(2, 2)
        model.setHeaderData(0, Qt.Orientation.Horizontal, 'Series')
        calc_page = QWidget()
        calc_page.setLayout(layout)
        layout.addWidget(self.tablePrep)
        heSlider = QSlider(Qt.Orientation.Horizontal, self)
        heSlider.setRange(0, 100)
        heSlider.setValue(60)
        heSlider.valueChanged.connect(self.heSlider_changed)
        # heSlider.setMaximum(10)
        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel('Amb. Temp'))
        tempEdit = QLineEdit("21.3")
        tempEdit.setMaxLength(10)
        hlayout.addWidget(tempEdit)
        hlayout.addWidget(QLabel('He 1/2 Ratio: '))
        hlayout.addWidget(heSlider, stretch=3)
        layout.addLayout(hlayout)
        layout.addWidget(self.tablePrep2, stretch=2)
        self.tabs.addTab(calc_page, 'Pulse Preparation')

        layoutTables.addWidget(self.tabs, stretch=3)
        layoutTables.addWidget(self.tableViewReports)
#        layoutMain.addLayout(layoutTools)
        layoutMain.addLayout(layoutTables)

        toolbar = QToolBar("Main toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        toolbar.addSeparator()
        button_action = QAction(
            QIcon(os.path.join(basedir, "icons/rocket--plus.png")),
            "Insert",
            self,
        )
        button_action.setStatusTip("Insert new Shot Report")
        button_action.triggered.connect(self.onInsertShotButtonClick)
        button_action.setCheckable(True)
        toolbar.addWidget(combo)
        toolbar.addWidget(shotSpin)
        toolbar.addWidget(refreshButt)
        toolbar.addAction(button_action)
        toolbar.addSeparator()
        bot_start = QAction(
            QIcon(os.path.join(basedir, "icons/battery-full.png")),
            "Bottles Start",
            self,
        )
        bot_start.setStatusTip("Save Start Bottle Pressures")
        bot_start.setCheckable(True)
        bot_start.triggered.connect(self.onBottStartClick)
        toolbar.addAction(bot_start)
        bot_end = QAction(
            QIcon(os.path.join(basedir, "icons/battery-low.png")),
            "Bottles End",
            self,
        )
        bot_end.setStatusTip("Save End Bottle Pressures")
        bot_end.setCheckable(True)
        bot_end.triggered.connect(self.onBottEndClick)
        toolbar.addAction(bot_end)

        self.setStatusBar(QStatusBar(self))

        container.setLayout(layoutMain)
        self.setMinimumSize(QSize(1200, 700))
        self.setCentralWidget(container)
        # self.updateTables()

    # def combo_changed(self, i):
    #    print(i)

    def heSlider_changed(self, i):
        self.HeRatio = i / 100.0
        print(f"HeRatio: {self.HeRatio}")

    def clearTable(self, table, data):
        model = SimpleModel(data)
        table.setModel(model)

    def clearTables(self):
        self.clearPulseDataTable()
        self.clearBottleTable()

    def clearBottleTable(self):
        # self.tableBottles.model.resetInternalData()
        data = [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [2, 1, 5, 3, 9], ]
        self.clearTable(self.tableBottles, data)

    def clearPulseDataTable(self):
        data = [
            [0, 0, 0, 0, 0],]
        self.clearTable(self.tablePulseData, data)
        # self.tableBottles.reset()
        # self.tablePulseData.setModel(model)
        self.tablePulseData.reset()

    def updateTables(self):
        _model = self.tableViewReports.model()
        _model.setQuery(_model.query())

        _model = self.tablePrep.model()
        _model.setFilter(f"id = {self.shotId:d}")
        # _model.select()
        # _model.setQuery(_model.query())
        # breakpoint()
        df = self.eDb.GetBottlePressures(self.shotId)
        if df is None:
            self.clearBottleTable()
            # _model.resetInternalData()
            # self.tableBottles.reset()
        else:
            # self.clearPulseDataTable()
            model = PandasModel(df)
            self.tableBottles.setModel(model)

        df = self.eDb.FetchPulseData(self.shotId)
        df = self.eDb.GetPulseData(self.shotId)
        if df is None:
            # self.tablePulseData.model.resetInternalData()
            # self.tablePulseData.reset()
            self.clearPulseDataTable()
            # model = QtCore.QAbstractTableModel()
            # self.tablePulseData.setModel(model)
        else:
            model = PandasModel(df)
            self.tablePulseData.setModel(model)
        df = self.eDb.PrepShot(self.shotId, self.HeRatio)
        if df is None:
            pass
            # self.clearBottleTable()
        else:
            model = PandasModel(df)
            self.tablePrep2.setModel(model)

        plot = self.eDb.GetPulsePlot(self.shotId)
        if plot is None:
            print("NO plot file")
            # file = IMAGE_PATH + '/data_file_2024-12-26_18-01-03.png'
            pixmap = QPixmap()
            # pixmap.swap(QPixmap())
        else:
            file = IMAGE_PATH + plot
            print(f"{self.shotId}, plot file: {file}")
            pixmap = QPixmap(file)
        self.labelPlot.setPixmap(pixmap)
        self.labelPlot.setScaledContents(True)
        # breakpoint()

    def seriesChanged(self, ser):  # s is a str
        print(ser)
        # shotId, shotNo = self.eDb.GetLastShot(series=ser)
        # print(f"Id {shotId}, {shotNo}")
        result = self.eDb.GetLastShot(series=ser)
        if result is not None:
            print(result)
            self.series = ser

    def onInsertShotButtonClick(self, s):
        # print("click", s)
        dlg = NewShotDialog(self)
        if dlg.exec():
            print("dlg Insert")
            result = self.eDb.InsertShot('S', self.lastShotNo + 1, 3, 1)
            if result is not None:
                print(result)
                self.shotId = result[0]
                self.shotNo = result[1]
                self.lastShotNo = result[1]
                self.updateTables()
            else:
                print("Error Insert")

    def onBottStartClick(self, s):
        self.eDb.SaveBottlePressures(self.shotId, 'CC_Start')
        self.updateTables()

    def onBottEndClick(self, s):
        self.eDb.SaveBottlePressures(self.shotId, 'End')
        self.updateTables()

    def shotChanged(self, i):
        result = self.eDb.GetShotId(i, self.series)

        if result is None:
            print('No shot report at ' + str(i))
            self.clearTables()
        else:
            print('shot is ' + str(i) + ' ' + str(result))
            self.shotNo = i
            self.shotId = result
            self.updateTables()

    def setTableCell(self, qR, table, name, lin, col):
        val = qR.value(name)
        item = QTableWidgetItem(f'{val:0.2f}')
        table.setItem(lin, col, item)

    def setBottleCells(self, qR, table, bottle, col):
        name = bottle + '_initial'
        valI = qR.value(name)
        item = QTableWidgetItem(f'{valI:0.2f}')
        table.setItem(0, col, item)
        name = bottle + '_final'
        valF = qR.value(name)
        item = QTableWidgetItem(f'{valF:0.2f}')
        table.setItem(1, col, item)
        item = QTableWidgetItem(f'{valI-valF:0.2f}')
        table.setItem(2, col, item)

    def set_table_val(self, table, val, lin, col):
        item = QTableWidgetItem(f'{val:0.2f}')
        table.setItem(lin, col, item)

    def update_queryReports(self, s=None):
        # print(Qt.CheckState(self.ceChck) == Qt.CheckState.Checked)
        # print(s)
        queryReports = QSqlQuery(db=db)
        queryReports.prepare(
            "SELECT shot_number, esther_reports.manager_id, "
            "esther_managers.manager_name, start_time, end_time "
            "FROM esther_reports "
            "INNER JOIN esther_managers ON esther_reports.manager_id = esther_managers.manager_id "
            # "WHERE =shot_number :list_id AND DayPlan = :plan_id "
            "WHERE shot_number  > 160 "
            # "WHERE shot_number  = :shot_no "
            # "ORDER BY LineOrder ASC"
        )
        # query = QSqlQuery("SELECT * FROM 'ChecklistLines' ORDER BY 'ChecklistLines'.'LineOrder' ASC", db=db)
        # query = QSqlQuery("SELECT * FROM ChecklistLines", db=db)

        queryReports.bindValue(":shot_no", self.shotNo)
        queryReports.exec()
        # print(queryReports.lastQuery()) #  + "; Line Before: " + str(lineBefore))
        model = QSqlQueryModel()
        model.setQuery(queryReports)
        self.tableReports.setModel(model)
        self.tableReports.setColumnWidth(0, 60)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
# sys.exit(app.exec())
app.exec()

# vim: syntax=python ts=4 sw=4 sts=4 sr et
"""
    def updateTables2(self, shotNo):
        queryTables = QSqlQuery(db=db)
        queryTables.prepare(
            "SELECT *, esther_managers.manager_name "
            "FROM esther_reports "
            "INNER JOIN esther_managers ON esther_reports.manager_id = "
            "esther_managers.manager_id "
            "WHERE shot_number  = :shot_no "
        )

        queryTables.bindValue(":shot_no", shotNo)
        queryTables.exec()
        if queryTables.first():
            # val  = queryReport.value(2)
            self.Date.setText(
                    'Date: ' + queryTables.value('start_time').toString('dd-MM-yyyy'))
            self.Manager.setText('Manager: ' + queryTables.value('manager_name'))
            self.STime.setText('Start Time: ' + queryTables.value('start_time').toString('hh:mm:ss'))
            ratioStr = (
                    f"He/H2/O2 Ratio: {queryTables.value('He_ratio_sp')}/"
                    f"{queryTables.value('H2_ratio_sp')}/"
                    f"{queryTables.value('O2_ratio_sp')}  ")
            self.Ratio.setText(ratioStr)
            dKStr = (
                    u'Δ PKistler/ Range'
                    # "delta_P_kistler / Range: "
                    f"{queryTables.value('delta_P_kistler')} / "
                    f"{queryTables.value('range_kistler')} Bar.")
            self.DKistler.setText(dKStr)
            qRep = queryTables
            tB = self.tableBottles
            self.setBottleCells(qRep, tB, 'O2_bottle', 0)
            # self.setTableCell(qRep, tB, 'O2_bottle_initial', 0, 0)
            # self.setTableCell(qRep, tB, 'O2_bottle_final', 1, 0)
            self.setBottleCells(qRep, tB, 'He1_bottle', 1)
            self.setBottleCells(qRep, tB, 'H_bottle', 2)
            self.setBottleCells(qRep, tB, 'He2_bottle', 3)
            self.setBottleCells(qRep, tB, 'N2_bottle', 4)
            self.setTableCell(qRep, tB, 'N2_command_bottle_initial', 0, 5)
            self.setTableCell(qRep, tB, 'N2_command_bottle_final', 1, 5)
            self.tableBottles.setColumnWidth(5, 100)
#            self.tableBottles.setAlternatingRowColors(True)
            # lastOK      = queryReport.value(1)
            # item = QTableWidgetItem(f'{val:0.2f}')
            # #item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            # self.tableBottles.setItem(0,4, item)
            # self.setTableCell(queryReport, self.tablePartial, 'pt901_end_s1', 0, 0)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_s1', 0, 0)
            tB = self.tablePartial
            pS1 = qRep.value('pt901_end_s1')
            self.set_table_val(tB, pS1, 0, 0)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_o', 0, 1)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_o', 0, 1)
            pO = qRep.value('pt901_end_o')
            self.set_table_val(tB, pO, 0, 1)
            pHe1 = qRep.value('pt901_end_he1')
            self.set_table_val(tB, pHe1, 0, 2)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_he1', 0, 2)
            pH = qRep.value('pt901_end_h')
            self.set_table_val(tB, pH, 0, 3)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_h', 0, 3)
            pHe2 = qRep.value('pt901_end_he2')
            self.set_table_val(tB, pHe2, 0, 4)
            # self.setTableCell(qRep, self.tablePartial, 'pt901_end_he2', 0, 4)
            self.setTableCell(qRep, tB, 'pt901_target', 0, 5)

            mfcSpHe1 = qRep.value('mfc_601_He1_sp')
            mfcSpHe2 = qRep.value('mfc_601_He2_sp')
            self.setTableCell(qRep, self.tableVolumes, 'bombe_volume', 0, 0)
            self.setTableCell(qRep, self.tableVolumes, 'mfc_201_O_sp', 0, 1)
            # self.set_table_val(self.tableVolumes, mfcSpHe2, 0, 2)
            # self.setTableCell(qRep, self.tableVolumes, 'mfc_601_He1_sp', 0, 2)
            self.set_table_val(self.tableVolumes, mfcSpHe1, 0, 2)
            self.setTableCell(qRep, self.tableVolumes, 'mfc_401_H_sp', 0, 3)
            self.set_table_val(self.tableVolumes, mfcSpHe2, 0, 4)
            chVol = qRep.value('bombe_volume')
            tAmb = qRep.value('ambient_temperature')
            pAmb = qRep.value('ambient_pressure') / 1000.0
            # pS1 = pS1 + pAmb
# def partial_volume(pBar, tempC, chambVolL):
            vHe0 = partial_volume(pS1 + pAmb, tAmb, chVol)
            vO = partial_volume(pO - pS1, tAmb, chVol)
            vHe1 = partial_volume(pHe1 - pO, tAmb, chVol)
            vH = partial_volume(pH - pHe1, tAmb, chVol)
            vHe2 = partial_volume(pHe2 - pH, tAmb, chVol)
            vHeTotal = vHe0 + vHe1 + vHe2
            # vTotal = partial_volume(pHe2 + pAmb, tAmb, chVol)
            self.set_table_val(self.tableVolumes, vHe0, 1, 0)
            self.set_table_val(self.tableVolumes, vO, 1, 1)
            self.set_table_val(self.tableVolumes, vHe1, 1, 2)
            self.set_table_val(self.tableVolumes, vH, 1, 3)
            self.set_table_val(self.tableVolumes, vHe2, 1, 4)

            self.set_table_val(self.tableVolumes, 1.0, 2, 1)
            if vO > 0:
                self.set_table_val(self.tableVolumes, vH / vO, 2, 3)
                self.set_table_val(self.tableVolumes, vHeTotal / vO, 2, 5)
            self.set_table_val(self.tableVolumes, vH / vO, 2, 3)
            self.set_table_val(self.tableVolumes, vHeTotal / vO, 2, 5)
            if vH > 0:
                self.set_table_val(self.tableVolumes, vO / vH * 2.0, 3, 1)
                self.set_table_val(self.tableVolumes, vHeTotal / vH * 2.0, 3, 5)
            self.set_table_val(self.tableVolumes, 2.0, 3, 3)
            # print('PP ' + str(chVol) + ' pAmb:' + str(pAmb))
        else:
            val = 0
            lastLineId = 0
            print('No Report')
        # print(queryReport.lastQuery() + str(val))

#    def update_Report(self, s=None):
#        self.updateTables(self.shotNo)

"""
