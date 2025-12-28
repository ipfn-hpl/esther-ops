from flask import Flask, render_template_string, request, redirect, url_for
import mysql.connector
from mysql.connector import Error

from config import DB_CONFIG

DAYPHASE = 1  # Only Implemented

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
    # "CheckItemSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = %s "
    "ORDER BY time_date DESC LIMIT 5"
)

LAST_CHECKED = (
    "SELECT item_id, item.seq_order "
    "FROM complete "
    "INNER JOIN item ON complete.item_id = item.id "
    "WHERE complete.shot = %s AND "
    "item.subsystem_id = %s AND "
    "item.role_id= %s "
    "ORDER BY time_date DESC LIMIT 1"
)

NEXT_CHECKLINES = (
    "SELECT id, seq_order, name "
    "FROM item "
    "WHERE day_phase_id = %s AND subsystem_id = %s AND "
    "role_id = %s AND seq_order > %s "
    "ORDER BY seq_order ASC LIMIT 3"
)

PRECENDENCE = (
    "SELECT item_id, after_item_id "
    "FROM precedence "
    "INNER JOIN item ON item_id = item.id "
    "WHERE item_id = %s "
    "ORDER BY item_id ASC"
)

MISSING_ITEM = (
    "SELECT role.short_name, item.id, seq_order, item.name, "
    "subsystem.name AS System, day_phase.short_name AS Phase "
    "FROM item "
    "INNER JOIN subsystem ON subsystem_id = subsystem.id "
    "INNER JOIN day_phase ON day_phase_id = day_phase.id "
    "INNER JOIN role ON role_id = role.id "
    "WHERE item.id =%s"
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
                <th>Role</th>
                <th>Master List</th>
                <th>Combustion</th>
                <th>Vacuum</th>
            </tr>
            <tr>
                <td>Chief Engineer</td>
                <td>
                    <a href="{{ url_for('list_html', system=0, role=0) }}" class="btn">Master</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=1, role=0) }}" class="btn">Combustion</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=2, role=0) }}" class="btn">Vacuum</a>
                </td>
            </tr>
            <tr>
                <td>Researcher</td>
                <td>
                    <a href="{{ url_for('list_html', system=0, role=1) }}" class="btn">Master</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=1, role=1) }}" class="btn">Combustion</a>
                </td>
                <td>
                    <a href="{{ url_for('list_html', system=2, role=1) }}" class="btn">Vacuum</a>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/list_html/<int:system>/<int:role>")
def list_html(system, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
    lastShotId = cursor.fetchone()[0]
    print(f"Last Shot Id: {lastShotId}")
    # if lastShot !=0:
    # rsor.fetchone()[0] != 0:
    # cursor.execute("SELECT id, name, email FROM users")  # SELECT query
    # reset cursor
    cursor.close()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM role WHERE id = %s", (role,))  # ,
    #        (role),
    # )
    roleName = cursor.fetchone()[0]
    # print(f"roleName : {role}:{roleName}")

    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (lastShotId, system, role),
    )
    lastComplete = cursor.fetchone()
    if lastComplete is None:
        print("No completed items. Returning")
        return redirect(url_for("index"))

    lastItem = lastComplete[0]
    lastOrder = lastComplete[1]
    print(f"Last item, Order: {lastItem}, {lastOrder}")
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
    cursor.execute(
        NEXT_CHECKLINES,
        (
            DAYPHASE,
            system,
            role,
            lastOrder,
        ),
    )
    nextItems = cursor.fetchall()
    print(f"NEXT_CHECKLINES {nextItems}, len: {len(nextItems)}")
    missingItems = []
    if len(nextItems) > 0:
        item2Sign = nextItems[0][0]
        cursor.close()
        cursor = conn.cursor()
        cursor.execute(
            PRECENDENCE,
            (item2Sign,),
        )
        precendenceItems = cursor.fetchall()
        for item in precendenceItems:
            befItem = item[1]
            cursor.execute(
                "SELECT COUNT(*) FROM complete WHERE shot = %s AND item_id = %s",
                (
                    lastShotId,
                    befItem,
                ),
            )
            if cursor.fetchone()[0] == 0:
                cursor.close()
                cursor = conn.cursor()
                cursor.execute(
                    MISSING_ITEM,
                    (befItem,),
                )
                missingItems.append(cursor.fetchone())
        print(f"precendenceItems: {precendenceItems}, missingItems:{missingItems}")

    cursor.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask ESTHER Checklist Wen App - MariaDB</title>
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
        <h1> {{roleName}} Esther Checklist Management. Shot Id {{shotId}} </h1>
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
        {% if lenMissing > 0 %}
        <h2>Missing Actions</h2>
        <table>
            <tr>
                <th>Resp</th>
                <th>ID</th>
                <th>Order</th>
                <th>Action</th>
                <th>System</th>
            </tr>
            {% for item in missingItems %}
            <tr>
                <td>{{ item[0] }}</td>
                <td>{{ item[1] }}</td>
                <td>{{ item[2] }}</td>
                <td>{{ item[3] }}</td>
                <td>{{ item[4] }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}
        <h2>Next Actions</h2>
        {% if lenNext > 0 %}
        <table>
            <tr>
                <th>ID</th>
                <th>Order</th>
                <th>name</th>
                <th>Actions</th>
            </tr>
            <tr>
                <td>{{ nextItems[0][0] }}</td>
                <td>{{ nextItems[0][1] }}</td>
                <td>{{ nextItems[0][2] }}</td>
                {% if lenMissing == 0 %}
                <td>
                    <a href="{{ url_for('insert', shot_id=shotId, id=nextItems[0][0], status=0) }}" class="btn">OK</a>
                </td>
                <td>
                    <a href="{{ url_for('insert', shot_id=shotId, id=nextItems[0][0], status=1) }}" class="btn">NOK</a>
                </td>
                {% endif %}
            </tr>
            {% for i in range(1, lenNext) %}
            <tr>
                <td>{{ nextItems[i][0] }}</td>
                <td>{{ nextItems[i][1] }}</td>
                <td>{{ nextItems[i][2] }}</td>
                <td></td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}

        <h2><a href="{{ url_for('index') }}">Select List</a></h2>
    </body>
    </html>
    """
    # <a href="{{ url_for('edit', id=nextItems[i][0]) }}" class="btn">Edit</a>
    # {% for line in nextItems %}
    return render_template_string(
        html,
        shotId=lastShotId,
        report=report,
        completed=completed,
        missingItems=missingItems,
        lenMissing=len(missingItems),
        nextItems=nextItems,
        lenNext=len(nextItems),
        roleName=roleName,
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


# INS: Update user data
@app.route("/insert/<int:shot_id>/<int:id>/<int:status>")
def insert(shot_id, id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    INSERT_LINE = (
        "INSERT INTO complete VALUES (NULL, %s, current_timestamp(), %s, %s, NULL)"
    )
    cursor.execute(
        INSERT_LINE,
        (
            shot_id,
            id,
            status,
        ),
    )
    # Get Item insertted
    print(INSERT_LINE % (shot_id, id, status))
    cursor.execute("SELECT subsystem_id, role_id FROM item WHERE id = %s", (id,))
    item = cursor.fetchone()
    system = item[0]
    role = item[1]
    print(f"System: {system}, Role: {role}")

    #     "UPDATE users SET name = %s, email = %s WHERE id = %s",  # UPDATE query
    #     (name, email, id),
    # )
    conn.commit()
    cursor.close()
    conn.close()

    # return redirect(url_for("index"))
    return redirect(url_for("list_html", system=system, role=role))


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
