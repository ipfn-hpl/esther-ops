#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6 SQL App for signing Esther Checklists
author:  B. Carvalho
email: bernardo.carvalho@tecnico.ulisboa.pt
"""

import sys

# from reportlab.pdfgen import canvas

from PyQt6.QtCore import (
    QSize,
    Qt,
    QSortFilterProxyModel,
)
from PyQt6.QtGui import QFont  # , QHeaderView
from PyQt6.QtSql import (
    QSqlDatabase,
    QSqlTableModel,
    QSqlQuery,
    QSqlQueryModel,
)
from PyQt6.QtWidgets import (
    QButtonGroup,
    QWidget,
    QApplication,
    # QLineEdit,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QDialog,
    QDialogButtonBox,
    # QCheckBox,
    # QComboBox,
    # QGroupBox,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QRadioButton,
    QTabWidget,
    QLabel,
    QHeaderView,
)

# Local module with DB configuration
import config

from makePdfReport import report_pdf

CHECKLINE_LAST_QUERY = (
    "SELECT item_id, item.seq_order, "
    "time_date, "
    "role.short_name AS Resp, complete_status.status, "
    "item.name "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.shot = :shot_no AND "
    # "CheckLineSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = :list_id "
    "ORDER BY time_date DESC LIMIT 5"
)

# "Checklist = :list_id AND CheckBy = :sign_by "
LAST_SIGNED_QRY = (
    "SELECT item_id, item.seq_order "
    "FROM complete "
    "INNER JOIN item ON complete.item_id = item.id "
    "WHERE complete.shot = :shot_no AND "
    "item.role_id= :sign_by AND "
    "item.subsystem_id = :list_id "
    "ORDER BY time_date DESC LIMIT 1"
)

PRECENDENCE_QRY = (
    "SELECT item_id, after_item_id "
    "FROM precedence "
    "INNER JOIN item ON item_id = item.id "
    "WHERE item_id = :line_id "
    "ORDER BY item_id ASC"
)

db = QSqlDatabase("QMARIADB")
db.setHostName(config.host)
db.setDatabaseName(config.database)
db.setUserName(config.username)
db.setPassword(config.password)

db.open()

# General Query for quick selects
queryGlobal = QSqlQuery(db=db)

FONT_NORMAL = QFont("Arial", 12)


class SignDialog(QDialog):
    def __init__(self, parent=None):  # <1>
        super().__init__(parent)
        # print("Pare: " + str(parent.shotNo))
        self.setWindowTitle("Sign Line!")

        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # self.rBv = QRadioButton('No Problem', self)
        self.rBa = QRadioButton("Attention required", self)
        self.rBa.setChecked(True)
        self.rBu = QRadioButton("Urgent Repair", self)
        self.layout = QVBoxLayout()
        message = QLabel("Sure you want to sign this Checkline?")
        self.layout.addWidget(message)
        self.layout.addWidget(self.rBa)
        self.layout.addWidget(self.rBu)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Esther CheckList Manager")
        self.listId = 0
        self.planId = 0
        self.signBy = 0
        self.lastSigned = 0
        self.nextLineId = -1
        self.shotNo = 180
        if queryGlobal.exec("SELECT shot FROM complete ORDER BY shot DESC LIMIT 1"):
            if queryGlobal.first():
                self.shotNo = queryGlobal.value(0)
        list_names = []
        if queryGlobal.exec("SELECT name FROM subsystem ORDER BY id ASC"):
            while queryGlobal.next():
                list_names.append(queryGlobal.value(0))
            print(list_names)

        self.tableLastCL = QTableView()

        self.tableMissingAction = QTableView()
        model = QSqlQueryModel()
        self.tableMissingAction.setModel(model)
        self.tableMissingAction.resizeColumnsToContents()
        self.tableMissingAction.horizontalHeader().setStretchLastSection(True)
        # self.missingActionTable.setColumnWidth(2, 250)
        self.missingActionTableRE = QTableView()
        model = QSqlQueryModel()
        self.missingActionTableRE.setModel(model)

        model = QSqlTableModel(db=db)
        model.setTable("item")
        model.setFilter("subsystem_id = 1")
        idx = model.fieldIndex("seq_order")
        model.setSort(idx, Qt.SortOrder.AscendingOrder)
        # .removeColumns()
        # model.setHeaderData(idx, Qt.Orientation.Horizontal, t)
        model.select()
        self.tableWaitSign = QTableView()
        self.tableWaitSign.setModel(model)
        self.tableWaitSign.resizeColumnsToContents()
        self.tableWaitSign.horizontalHeader().setStretchLastSection(True)

        container = QWidget()

        layoutTables = QVBoxLayout()
        label = QLabel("CheckList Systems")
        label.setFont(FONT_NORMAL)
        layoutTables.addWidget(label)
        self.tabs = QTabWidget()
        for n, lst in enumerate(list_names):
            model = QSqlTableModel(db=db)
            model.setTable("item")

            # model.setFilter(f"subsystem_id = {n} "
            #                "AND day_phase_id = 1")
            # idx = model.fieldIndex("seq_order")
            # model.setSort(idx, Qt.SortOrder.AscendingOrder)
            # model.select()
            columns_to_remove = ["subsystem_id", "long_name"]
            for cn in columns_to_remove:
                idx = model.fieldIndex(cn)
                model.removeColumns(idx, 1)
            column_titles = {
                "name": "Action",
                "day_phase_id": "Phase",
            }
            for n, t in column_titles.items():
                idx = model.fieldIndex(n)
                model.setHeaderData(idx, Qt.Orientation.Horizontal, t)
            tableVw = QTableView()
            tableVw.setModel(model)
            tableVw.resizeColumnsToContents()
            tableVw.setAlternatingRowColors(True)
            # tableVw.setColumnWidth(0, 30)
            mode = QHeaderView.ResizeMode.Interactive
            # tableVw.horizontalHeader().resizeSection(1, 30)
            tableVw.horizontalHeader().setDefaultSectionSize(30)
            tableVw.horizontalHeader().setSectionResizeMode(mode)
            #            tableVw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            tableVw.horizontalHeader().setStretchLastSection(True)
            tableVw.horizontalHeader().resizeSection(0, 60)
            self.tabs.addTab(tableVw, lst)

        self.tabs.currentChanged.connect(self.list_changed)
        layoutTables.addWidget(self.tabs, stretch=3)

        label = QLabel("Actions already completed on this Shot")
        label.setFont(FONT_NORMAL)
        layoutTables.addWidget(label)

        layoutTables.addWidget(self.tableLastCL, stretch=2)
        layoutMaTables = QGridLayout()  # QHBoxLayout()

        self.MAlabel = QLabel("Missing Actions")
        self.MAlabel.setFont(FONT_NORMAL)
        # self.MAlabel.setStyleSheet("background-color: yellow; border: 1px solid black;")
        layoutTables.addWidget(self.MAlabel)
        layoutMaTables.addWidget(QLabel("Chief Engineer"), 0, 0)
        layoutMaTables.addWidget(QLabel("Researcher"), 0, 1)
        layoutMaTables.addWidget(self.tableMissingAction, 1, 0)
        layoutMaTables.addWidget(self.missingActionTableRE, 1, 1)
        layoutTables.addLayout(layoutMaTables, stretch=1)

        label = QLabel("Next Actions to Check")
        label.setFont(FONT_NORMAL)
        layoutTables.addWidget(label)
        layoutTables.addWidget(self.tableWaitSign, stretch=2)

        layoutTools = QVBoxLayout()

        refreshButt = QPushButton("Refresh")
        refreshButt.clicked.connect(self.update_queryLastCL)
        pdfButt = QPushButton("Report PDF")
        pdfButt.clicked.connect(self.make_report_pdf)
        #        refreshButt.clicked.connect(self.refresh_model)

        #        layoutTools.addWidget(add_rec)
        #        self.list = QLineEdit()
        #        self.list.setPlaceholderText("1")
        #        self.list.textChanged.connect(self.update_query)
        layoutTools.addWidget(refreshButt)
        layoutTools.addWidget(pdfButt)
        layoutTools.addWidget(QLabel("Exp. Phase"))
        #         widget = QComboBox()
        #        widget.addItems(["StartOfDay", "Shot", "EndOfDay"])
        #        widget.currentIndexChanged.connect(self.plan_changed)
        #        widget.setCurrentIndex(self.planId)
        #        layoutTools.addWidget(widget)
        # self._button_group = QButtonGroup()
        # _button_group = QButtonGroup(self)
        # _button_group.setExclusive(False)
        # rB = QRadioButton('StartOfDay2', _button_group)
        # _button_group.addButton(rB)
        # layoutTools.addWidget(_button_group)
        # self._button_group.idClicked.connect(self.button_group_clicked)
        # self.groupBox = QGroupBox("Labels", self)
        # layoutTools.addWidget(self.groupBox)

        self.buttonGroupP = QButtonGroup(self)
        self.buttonGroupP.setExclusive(True)

        # self.radioButton1 = QRadioButton("Label 1")
        # self.buttonGroup.addButton(self.radioButton1)

        radiobutton = QRadioButton("StartOfDay", self)
        radiobutton.setChecked(True)
        radiobutton.plan = 0
        radiobutton.toggled.connect(self.change_plan)
        self.buttonGroupP.addButton(radiobutton)
        layoutTools.addWidget(radiobutton)
        radiobutton = QRadioButton("Shot", self)
        radiobutton.plan = 1
        radiobutton.toggled.connect(self.change_plan)
        self.buttonGroupP.addButton(radiobutton)
        layoutTools.addWidget(radiobutton)
        radiobutton = QRadioButton("EndOfDay", self)
        radiobutton.plan = 2
        radiobutton.toggled.connect(self.change_plan)
        self.buttonGroupP.addButton(radiobutton)
        layoutTools.addWidget(radiobutton)

        layoutTools.addWidget(QLabel("Shot"))
        shotSpin = QSpinBox()
        shotSpin.setMinimum(170)
        shotSpin.setMaximum(1000)  # May need to change (hopefully)
        # Or: widget.setRange(-10,3)
        # widget.setPrefix("$")
        # widget.setSuffix("c")
        shotSpin.setSingleStep(1)  # Or e.g. 0.5 for QDoubleSpinBox
        shotSpin.setValue(self.shotNo)
        layoutTools.addWidget(shotSpin)

        #        layoutTools.addWidget(QLabel('Filter Checklist:'))
        #        layoutTools.addWidget(self.list)

        layoutTools.addStretch()
        # .addSpacing(20)
        layoutTools.addWidget(QLabel("Checked By: "))
        self.buttonGroupS = QButtonGroup(self)
        self.buttonGroupS.setExclusive(True)

        radiobutton = QRadioButton("ChiefEngineer", self)
        radiobutton.setChecked(True)
        radiobutton.sign = 0
        radiobutton.toggled.connect(self.update_signBy)
        self.buttonGroupS.addButton(radiobutton)
        layoutTools.addWidget(radiobutton)

        radiobutton = QRadioButton("Researcher", self)
        radiobutton.sign = 1
        radiobutton.toggled.connect(self.update_signBy)
        self.buttonGroupS.addButton(radiobutton)
        layoutTools.addWidget(radiobutton)

        self.checkButtOK = QPushButton("Check Line OK")
        self.checkButtOK.clicked.connect(self.checkLineButtOK_clicked)
        layoutTools.addWidget(self.checkButtOK)
        checkButt = QPushButton("Check Next Line NOK")
        checkButt.clicked.connect(self.checkLineButt_clicked)
        layoutTools.addWidget(checkButt)

        layoutMain = QHBoxLayout()

        layoutMain.addLayout(layoutTools)

        layoutMain.addLayout(layoutTables)
        container.setLayout(layoutMain)

        shotSpin.valueChanged.connect(self.shot_changed)
        # listComb.currentIndexChanged.connect(self.list_changed)
        self.setMinimumSize(QSize(1200, 700))
        self.setCentralWidget(container)
        # menu = self.menuBar()
        # file_menu = menu.addMenu("&File")
        # self.update_panels()
        self.updateMissingActionTables([10, 20])
        self.update_ChkLists()
        self.update_queryLastCL()
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update_panels)
        # self.timer.start(2000)

    # def update_panels(self):
    #    self.update_queryLastCL()

    def change_plan(self):
        rb = self.sender()
        # check if the radio button is checkedDayPlanId
        if rb.isChecked():
            # print("signBy is %s" % (rb.plan))
            self.planId = rb.plan
            self.update_ChkLists(rb.plan)
            self.update_queryLastCL()

    def list_changed(self, lid):
        self.listId = lid
        # self.update_queryCL()
        self.update_queryLastCL()

    def shot_changed(self, s):
        # print('Shot is ' + str(s))
        self.shotNo = s
        self.update_queryLastCL()

    def update_signBy(self):
        # get the radio button the send the signal
        rb = self.sender()
        # check if the radio button is checkedDayPlanId
        if rb.isChecked():
            print("signBy is %s" % (rb.sign))
            self.signBy = rb.sign
            self.update_queryLastCL()

    def updateMissingActionTables(self, missingList):
        model = self.tableMissingAction.model()
        query = QSqlQuery(db=db)
        sql = (
            "SELECT item.id, seq_order, item.name, "
            "subsystem.name AS System, day_phase.short_name AS Phase "
            "FROM item "
            "INNER JOIN subsystem ON subsystem_id = subsystem.id "
            "INNER JOIN day_phase ON day_phase_id = day_phase.id "
            "INNER JOIN role ON role_id = role.id "
            "WHERE item.id IN ("
        )
        sqlQry = sql + ",".join(map(str, missingList))
        sqlStr = sqlQry + ") AND role_id = 0"
        if not query.exec(sqlStr):
            print(f"CE MA {query.executedQuery()}")
        model.setQuery(query)
        # self.missingActionTable.setColumnWidth(0, 30)
        # self.missingActionTable.setColumnWidth(1, 40)
        # self.missingActionTable.setColumnWidth(2, 250)
        # self.missingActionTable.setColumnWidth(3, 50)

        model = self.missingActionTableRE.model()
        sqlStr = sqlQry + ") AND role_id = 1"
        if not query.exec(sqlStr):
            print(f"RE MA {query.executedQuery()}")
        model.setQuery(query)
        self.missingActionTableRE.setColumnWidth(0, 30)
        self.missingActionTableRE.setColumnWidth(1, 40)
        self.missingActionTableRE.setColumnWidth(2, 250)

    def update_ChkLists(self, phaseId=1):
        # print('count is ' + str(self.tabs.count()))
        # query = QSqlQuery(db=db)
        for n in range(self.tabs.count()):
            tabw = self.tabs.widget(n)
            model = tabw.model()
            model.setFilter(f"subsystem_id = {n} AND day_phase_id = {phaseId}")
            idx = model.fieldIndex("seq_order")
            model.setSort(idx, Qt.SortOrder.AscendingOrder)
            model.select()
            # tabw.setColumnWidth(0, 30)
            # tabw.setColumnWidth(1, 30)
            # tabw.setColumnWidth(2, 80)
            # tabw.setColumnWidth(3, 700)

    def update_queryLastCL(self, s=None):
        # print(Qt.CheckState(self.ceChck) == Qt.CheckState.Checked)
        # print(s)
        model = QSqlQueryModel()
        query = QSqlQuery(db=db)
        query.prepare(CHECKLINE_LAST_QUERY)
        # self.tableLastCL.setModel(qryModel)
        query.bindValue(":shot_no", self.shotNo)
        # query.bindValue(":sign_by", self.signBy)
        query.bindValue(":list_id", self.listId)
        # if (not queryLastCL.exec()):
        if not query.exec():
            # print(f"NOT exec(). CL Query i: {i}", end='')
            print(f"NOT exec: {query.executedQuery()}")
            # print(f"{query.executedQuery()} signBy: {self.signBy}")
            # print("Last CL Query: " + query.executedQuery() + " signBy: " + str(self.signBy))
            return
        # print(":shot_no", str(self.shotNo)  + " signBy: " + str(self.signBy))
        # QSqlQueryModel::setQuery() is a member of the model, QSqlQueryModel::query().exec()
        # is just a method on the query. So the model knows about the former and refreshes,
        # but does not know you're doing the latter.
        model.setQuery(query)
        # https://forum.qt.io/topic/13658/qsqltablemodel-qtableview-how-to-sort-by-column/2

        proxyModel = QSortFilterProxyModel(model)
        proxyModel.setSourceModel(model)
        self.tableLastCL.setModel(proxyModel)
        self.tableLastCL.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.tableLastCL.setSortingEnabled(True)
        self.tableLastCL.resizeColumnsToContents()
        self.tableLastCL.horizontalHeader().setStretchLastSection(True)
        # self.tableLastCL.reset()
        # self.tableLastCL.show()
        # self.tableLastCL.setColumnWidth(0, 30)
        # self.tableLastCL.setColumnWidth(1, 40)
        # self.tableLastCL.setColumnWidth(3, 400)
        # self.tableLastCL.resizeColumnsToContents()
        self.tableLastCL.setAlternatingRowColors(True)

        query = QSqlQuery(db=db)
        query.prepare(LAST_SIGNED_QRY)
        query.bindValue(":shot_no", self.shotNo)
        query.bindValue(":sign_by", self.signBy)
        query.bindValue(":list_id", self.listId)
        if query.exec():
            if query.first():
                self.lastSigned = query.value(1)
            else:
                self.lastSigned = 0
            print(f"lastOrder: {self.lastSigned}")
        else:
            print(f"Last signed NOT exec: {query.executedQuery()}")
        #    lastOK  = 0
        #    lastLineId  = 0
        # print(self.queryLastCL.lastQuery())
        # self.update_queryLastCL()
        # self.lastSignedId = lastLineId
        self.update_queryWaitList()

    def update_queryWaitList(self):
        # print(Qt.CheckState(self.ceChck) == Qt.CheckState.Checked)
        # model = self.tableWaitSign.model()
        # query = model.query()

        _model = self.tableWaitSign.model()
        _model.setFilter(
            f"subsystem_id = {self.listId} "
            f"AND day_phase_id = {self.planId} "
            f"AND role_id = {self.signBy} "
            f"AND seq_order > {self.lastSigned}"
        )
        idx = _model.fieldIndex("seq_order")
        _model.setSort(idx, Qt.SortOrder.AscendingOrder)
        _model.select()
        # queryWaitOK = QSqlQuery(db=db)
        # query.bindValue(":l_order", self.lastSigned)
        # query.bindValue(":list_id", self.listId)
        # query.bindValue(":sign_by", self.signBy)
        # query.bindValue(":d_plan", self.planId)
        missLines = []
        nextItem = _model.record(0).value("id")
        if nextItem is not None:
            print(f"Next I: {nextItem}")
            # nextLine = query.value(0)
            missLines = self.getMissingLines(nextItem)
            if not missLines:
                print("No missing Lines")
                self.MAlabel.setStyleSheet("color: black; background-color: white")
                self.MAlabel.setText("Please Continue")
                self.nextLineId = nextItem
            else:
                print("Missing Lines")
                self.MAlabel.setStyleSheet(
                    "color: red; background-color: yellow; border: 1px solid black"
                )
                self.MAlabel.setText(
                    "Please Hold. Some Actions need to be completed first"
                )
                #  print(missLines)
                self.nextLineId = -1
            self.updateMissingActionTables(missLines)
        else:
            self.nextLineId = 0
            print("Not missing Lines")
        # breakpoint()

    """        
        if query.exec():
            if query.first():
            # model.setQuery(query)
            # self.tableWaitSign.setColumnWidth(0, 100)
            # self.tableWaitSign.setColumnWidth(1, 100)
            #self.tableWaitSign.setColumnWidth(2, 400)
        else:
            print(f"Wait List NOT exec: {query.executedQuery()}")
    """

    def getMissingLines(self, nextLineId):
        qryCheckPrecedence = QSqlQuery(db=db)
        qryCheckPrecedence.prepare(PRECENDENCE_QRY)
        qryCheckPrecedence.bindValue(":line_id", nextLineId)
        if not qryCheckPrecedence.exec():
            print(f"Prececence {qryCheckPrecedence.executedQuery()}")

        qryCheckSigned = QSqlQuery(db=db)
        qryCheckSigned.prepare(
            "SELECT item_id, shot, complete_status_id "
            "FROM complete "
            "WHERE item_id = :line AND shot = :shot_no"
        )
        missingList = []
        while qryCheckPrecedence.next():
            lineBefore = qryCheckPrecedence.value(1)
            qryCheckSigned.bindValue(":line", lineBefore)
            qryCheckSigned.bindValue(":shot_no", self.shotNo)
            qryCheckSigned.exec()
            if not qryCheckSigned.first():
                missingList.append(lineBefore)
                print(f"Line Before not Signed: {lineBefore}")
        return missingList

    def insertCheckedLine(self, value):
        insertCLine = QSqlQuery(db=db)
        insertCLine.prepare(
            "INSERT INTO complete VALUES (NULL, :shot_no, "
            "current_timestamp(), :cLine_id, :sign_val, NULL)"
        )
        insertCLine.bindValue(":shot_no", self.shotNo)
        insertCLine.bindValue(":cLine_id", self.nextLineId)
        insertCLine.bindValue(":sign_val", value)
        if insertCLine.exec():
            print("Inserted record")
            self.update_queryLastCL()
        else:
            QMessageBox.critical(None, "Record NOT Inserted ", "SQL Error")
            print(f"Insert failed: {insertCLine.lastQuery()}")
        self.checkButtOK.setEnabled(True)

    def checkLineButtOK_clicked(self):
        if self.nextLineId > 0:
            self.checkButtOK.setEnabled(False)
            self.insertCheckedLine(0)  # 'No Problem
        else:
            print(f"Action Canceled! {self.nextLineId}")

    def checkLineButt_clicked(self):
        if self.nextLineId > 0:
            dlg = SignDialog(self)
            if dlg.exec():
                if dlg.rBa.isChecked():
                    signVal = 1
                elif dlg.rBu.isChecked():
                    signVal = 2
                else:
                    signVal = 255
                print(f"dlg rBx: {signVal}")
                self.insertCheckedLine(signVal)
        else:
            print(f"Insert Cancel! {self.nextLineId}")

    def make_report_pdf(self):
        report_pdf(db, self.shotNo, self.listId)
        dlg = QDialog(self)
        dlg.setWindowTitle("HELLO!")
        dlg.exec()
        # QBtn = QDialogButtonBox.StandardButton.Ok


#    def update_filter(self, s):
#        filter_str = 'Checklist LIKE "{}"'.format(s)
#        self.model.setFilter(filter_str)

#        self.model.setFilter(filter_str)
# def refresh_model(self, s):
#    self.model.select()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
# app.exec()

# vim: syntax=python ts=4 sw=4 sts=4 sr et
