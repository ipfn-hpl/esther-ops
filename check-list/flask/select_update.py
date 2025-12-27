from flask import Flask, render_template_string, request, redirect, url_for
import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG

LAST_CHECKLINES = (
    "SELECT item_id, item.seq_order, "
    "time_date, "
    "role.short_name AS Resp, complete_status.status, "
    "item.name "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.shot = %s AND "
    # "CheckLineSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = %s "
    "ORDER BY time_date DESC LIMIT 5"
)

LAST_CHECKED = (
    "SELECT item_id, item.seq_order "
    "FROM complete "
    "INNER JOIN item ON complete.item_id = item.id "
    "WHERE complete.shot = %s AND "
    "item.role_id= %s AND "
    "item.subsystem_id = %s "
    "ORDER BY time_date DESC LIMIT 1"
)

NEXT_CHECKLINES = (
    "SELECT id, seq_order, name "
    "FROM item "
    "WHERE day_phase_id = %s AND subsystem_id = %s AND "
    "role_id = %s AND seq_order > %s "
    "ORDER BY seq_order ASC LIMIT 2"
)
app = Flask(__name__)


# Get database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None


@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask CRUD Example - MariaDB</title>
        <style>
            body { font-family: Arial; margin: 50px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            .btn { padding: 5px 10px; margin: 2px; text-decoration: none; 
                   background-color: #008CBA; color: white; border-radius: 3px; }
            .btn:hover { background-color: #005f7a; }
        </style>
    </head>
    <body>
        <h1>Esther Checklist Management (MariaDB)</h1>
        <table>
            <tr>
                <th>Master List</th>
                <th>Combustion</th>
                <th>Vacuum</th>
            </tr>
            <tr>
                <td>
                    <a href="{{ url_for('list_html', system=1) }}" class="btn">Master</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=2) }}" class="btn">Combustion</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=3) }}" class="btn">Vacuum</a>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return render_template_string(html)


def index2():
    html = list_html(1)
    return html


@app.route("/list_html/<int:system>")
def list_html(system):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
    lastShotId = cursor.fetchone()[0]
    print(f"Last Id: {lastShotId}")
    # if lastShot !=0:
    # rsor.fetchone()[0] != 0:
    # cursor.execute("SELECT id, name, email FROM users")  # SELECT query
    # reset cursor
    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (lastShotId, 0, system),
    )
    lastComplete = cursor.fetchone()
    lastLine = lastComplete[0]
    lastOrder = lastComplete[1]
    print(f"Last Line, Order: {lastLine}, {lastOrder}")
    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, shot, chief_engineer_id, researcher_id, cc_pressure_sp, He_sp, H2_sp, O2_sp FROM reports WHERE id = %s",
        (lastShotId,),
    )
    report = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKLINES,
        (lastShotId, system),
    )
    completed = cursor.fetchall()
    # print("Completed")
    # print(completed)

    cursor.close()
    cursor = conn.cursor()
    dayPhase = 1
    role = 0
    cursor.execute(
        NEXT_CHECKLINES,
        (
            dayPhase,
            system,
            role,
            lastOrder,
        ),
    )
    nextLines = cursor.fetchall()
    print("NEXT_CHECKLINES")
    print(nextLines)
    cursor.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask CRUD Example - MariaDB</title>
        <style>
            body { font-family: Arial; margin: 50px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            .btn { padding: 5px 10px; margin: 2px; text-decoration: none; 
                   background-color: #008CBA; color: white; border-radius: 3px; }
            .btn:hover { background-color: #005f7a; }
        </style>
    </head>
    <body>
        <h1>Esther Checklist Management Shot Id {{shotId}} (MariaDB) </h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Shot</th>
                <th>Actions</th>
            </tr>
            {% for rprt in report %}
            <tr>
                <td>{{ rprt[0] }}</td>
                <td>{{ rprt[1] }}</td>
                <td>{{ rprt[2] }}</td>
                <td>
                    <a href="{{ url_for('edit', id=rprt[0]) }}" class="btn">Edit</a>
                </td>
            </tr>
            {% endfor %}
        </table>
        <h2>Completed Actions in Shot {{shotId}}</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Order</th>
                <th>Date/Time</th>
                <th>Resp</th>
                <th>name</th>
                <th>Status</th>
            </tr>
            {% for action in completed %}
            <tr>
                <td>{{ action[0] }}</td>
                <td>{{ action[1] }}</td>
                <td>{{ action[2] }}</td>
                <td>{{ action[3] }}</td>
                <td>{{ action[5] }}</td>
                <td>{{ action[4] }}</td>
            </tr>
            {% endfor %}
        </table>
        <h2>Next Actions</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Order</th>
                <th>name</th>
                <th>Actions</th>
            </tr>
            {% for line in nextLines %}
            <tr>
                <td>{{ line[0] }}</td>
                <td>{{ line[1] }}</td>
                <td>{{ line[2] }}</td>
                <td>
                    <a href="{{ url_for('edit', id=line[0]) }}" class="btn">Edit</a>
                    <a href="{{ url_for('edit', id=line[0]) }}" class="btn">OK</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(
        html, shotId=lastShotId, report=report, completed=completed, nextLines=nextLines
    )


# SELECT: Get single user for editing
@app.route("/edit/<int:id>")
def edit(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = %s", (id,)
    )  # SELECT with WHERE
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit User</title>
        <style>
            body { font-family: Arial; margin: 50px; }
            input { padding: 8px; margin: 5px 0; width: 300px; }
            .btn { padding: 10px 20px; background-color: #4CAF50; 
                   color: white; border: none; cursor: pointer; }
            .btn:hover { background-color: #45a049; }
        </style>
    </head>
    <body>
        <h1>Edit User</h1>
        <form method="POST" action="{{ url_for('update', id=user[0]) }}">
            <div>
                <label>Name:</label><br>
                <input type="text" name="name" value="{{ user[1] }}" required>
            </div>
            <div>
                <label>Email:</label><br>
                <input type="email" name="email" value="{{ user[2] }}" required>
            </div>
            <br>
            <button type="submit" class="btn">Update</button>
            <a href="{{ url_for('index') }}">Cancel</a>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, user=user)


# UPDATE: Update user data
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    name = request.form["name"]
    email = request.form["email"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name = %s, email = %s WHERE id = %s",  # UPDATE query
        (name, email, id),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
