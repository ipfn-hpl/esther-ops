#!/usr/bin/env python3
"""
PyQt6 SQL App for making Esther Report Checklists
https://www.reportlab.com/docs/reportlab-userguide.pdf
"""

import sys

# from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    Image,
    TableStyle,
    SimpleDocTemplate,
)

# from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.rl_config import defaultPageSize
import argparse

import config

from PyQt6.QtWidgets import QApplication
from PyQt6.QtSql import (
    QSqlDatabase,
    QSqlQuery,
)

PAGE_WIDTH = defaultPageSize[0]
PAGE_HEIGHT = defaultPageSize[1]
styleSheet = getSampleStyleSheet()
# ['Title'] ['Heading2'] ['Heading3'] ['Normal'] ['BodyText']
# https://www.programcreek.com/python/example/58583/reportlab.lib.styles.getSampleStyleSheet

CHECKLINE_LIST_QUERY = (
    "SELECT item_id, item.seq_order, "
    "time_date, item.name, "
    "role.short_name AS Resp, complete_status.short_status "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.shot = :shot_no AND "
    # "CheckLineSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = :list_id "
    "ORDER BY time_date ASC"
)

CHECKLINE_FULL_QUERY = (
    "SELECT item_id, item.seq_order, "
    "time_date, item.name, "
    "role.short_name AS Resp, complete_status.short_status "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.shot = :shot_no "
    "ORDER BY time_date ASC"
)

#        "ORDER BY time_date DESC LIMIT 5"


def report_pdf(db, shotNo, listId):
    list_names = []

    query = QSqlQuery(db=db)
    # Create the report
    if query.exec("SELECT name FROM subsystem ORDER BY id ASC"):
        while query.next():
            # print(query.value(0))
            list_names.append(query.value(0))

    listName = ""
    if query.exec(f"SELECT long_name FROM subsystem WHERE id={listId}"):
        if query.first():
            listName = query.value(0)
    query.finish()
    if listId >= len(list_names):
        print(f"List ID {listId} out of range. Max is {len(list_names) - 1}")
        sys.exit(1)
    elif listId < 0:
        query.prepare(CHECKLINE_FULL_QUERY)
        doc = SimpleDocTemplate(f"report_full_{shotNo}.pdf", pagesize=A4)
        p2 = Paragraph("Full List", styleSheet["Heading3"])
    else:
        query.prepare(CHECKLINE_LIST_QUERY)
        query.bindValue(":list_id", listId)
        doc = SimpleDocTemplate(f"report_{shotNo}_{listId}.pdf", pagesize=A4)
        p2 = Paragraph(f"{listName}", styleSheet["Heading3"])

    query.bindValue(":shot_no", shotNo)
    # P0 = Paragraph('A paragraph1', styleSheet["BodyText"])
    # elements = [Spacer(1,1*inch)]
    elements = []
    im = Image("images/logo-IPFN-compact.jpg", 4 * cm, 4.0 * 171.0 / 296.0 * cm)
    im.hAlign = "LEFT"

    elements.append(im)
    styleNormal = styleSheet["Normal"]
    # f"Esther Report. Shot: {shotNo}. Check List: {list_names[listId]}",
    p1 = Paragraph(f"Esther Report. Shot: {shotNo}.", styleSheet["Heading2"])
    # time_format = "yyyy-MM-dd HH:mm:ss"
    time_format = "HH:mm:ss"
    elements.append(p1)
    elements.append(p2)

    elements.append(Spacer(1, 0.2 * inch))
    # elements.append(Paragraph(" ", style))
    styleDesc = ParagraphStyle(
        # name='Normal',
        name="Helvetica",
        fontSize=8,
    )
    line = []
    line.append("#")
    line.append("Test Procedure")
    line.append("Check")
    line.append("Time")
    dataTable = []
    dataTable.append(line)
    dateTime = " "
    if query.exec():
        while query.next():
            # i qn.append(query.next())
            line = []  # clear line
            # line.append(query.value('CheckLine'))
            line.append(f"{query.value('Resp')}{query.value('item.seq_order')}")
            # print(str(query.value('LineStatusDate')))
            # print(query.value('LineDesc'))
            P0 = Paragraph(str(query.value("item.name")), styleDesc)
            # P0 = Paragraph(str(query.value('LineDesc')), styleSheet["BodyText"])
            line.append(P0)
            line.append(query.value("complete_status.short_status"))
            # line.append(query.value('LineStatusDate').toString(time_format))
            dateTime = query.value("time_date")
            line.append(dateTime.toString(time_format))
            dataTable.append(line)

    else:
        print("NOT exec(). Query : " + query.executedQuery())

    if len(dataTable) > 1:
        t1 = Table(dataTable, colWidths=(38, 400, 25, 50))
        t1.setStyle(
            TableStyle(
                [
                    # ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),  # font
                    # ("FONTSIZE", (0, 0), (-1, 0), 12),
                    # ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.blue),
                ]
            )
        )

        elements.append(t1)
        elements.append(Spacer(1, 1 * cm))
        p3 = Paragraph(f"Date: {dateTime.toString('dd-MM-yyyy')}", styleNormal)
        elements.append(p3)
        elements.append(Spacer(1, 1 * cm))
        p3 = Paragraph("Signatures", styleNormal)
        elements.append(p3)
        print(f"Report Completed for Shot: {shotNo}")
    else:
        p3 = Paragraph("NO Checked Lines in this Report", styleNormal)
        elements.append(p3)
        print(f"No actions completed on Shot: {shotNo}")

    # write the document to disk
    doc.build(elements)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    db = QSqlDatabase("QMARIADB")

    db.setHostName(config.host)
    db.setDatabaseName(config.database)
    db.setUserName(config.username)
    db.setPassword(config.password)

    parser = argparse.ArgumentParser(
        description="Script to make ESTHER Operation Pulse Report"
    )

    parser.add_argument(
        "-s", "--shot", type=int, help="ESTHER pulse Number ([1, ...])", default=180
    )
    parser.add_argument(
        "-l", "--list", type=int, help="ESTHER Checklist number ([0, ...])", default=0
    )
    args = parser.parse_args()
    shotNum = args.shot
    listId = args.list
    if db.open():
        report_pdf(db, shotNum, listId)
    else:
        print("Could not open db")

# vim: syntax=python ts=4 sw=4 sts=4 sr et
