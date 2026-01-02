# from flask import Flask, render_template_string, request, redirect, url_for
from flask import (
    Flask,
    render_template_string,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g,
)
from werkzeug.security import check_password_hash  # generate_password_hash,

# import mysql.connector
import mariadb
import sys
import os
# from mysql.connector import Error

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
    "WHERE complete.shot = ? AND "
    # "CheckItemSigned.SignedBy = :sign_by AND "
    "item.subsystem_id = ? "
    "ORDER BY time_date DESC LIMIT 5"
)

LAST_CHECKED = (
    "SELECT item_id, item.seq_order "
    "FROM complete "
    "INNER JOIN item ON complete.item_id = item.id "
    "WHERE complete.shot = ? AND "
    "item.subsystem_id = ? AND "
    "item.role_id= ? "
    "ORDER BY time_date DESC LIMIT 1"
)

NEXT_CHECKLINES = (
    "SELECT id, seq_order, name "
    "FROM item "
    "WHERE day_phase_id = ? AND subsystem_id = ? AND "
    "role_id = ? AND seq_order > ? "
    "ORDER BY seq_order ASC LIMIT 3"
)

PRECENDENCE = (
    "SELECT item_id, after_item_id "
    "FROM precedence "
    "INNER JOIN item ON item_id = item.id "
    "WHERE item_id = ? "
    "ORDER BY item_id ASC"
)

MISSING_ITEM = (
    "SELECT role.short_name, item.id, seq_order, item.name, "
    "subsystem.name AS System, day_phase.short_name AS Phase "
    "FROM item "
    "INNER JOIN subsystem ON subsystem_id = subsystem.id "
    "INNER JOIN day_phase ON day_phase_id = day_phase.id "
    "INNER JOIN role ON role_id = role.id "
    "WHERE item.id = ?"
)

app = Flask(__name__)
# app.secret_key = "your-secret-key-random"  # Change this to a random secret key
app.secret_key = os.urandom(24)


def get_db():
    """Get database connection from Flask's g object (request context)"""
    if "db" not in g:
        try:
            g.db = mariadb.connect(**DB_CONFIG)
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB: {e}")
            sys.exit(1)
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection at the end of request"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Home route
@app.route("/")
def home():
    if "user_id" in session:
        # return f'Welcome to Esther CheckLists. Please Login {session["username"]}! <a href="/logout">Logout</a>'
        flash(f"Welcome to Esther CheckLists. {session['username']}!")
        return redirect(url_for("dashboard"))
    return 'Welcome! <a href="/login">Login</a> | <a href="/register">Register</a>'


# Logout route
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("home"))


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # conn = get_db_connection()
        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id, username, password FROM operator WHERE username = ?",
                (username,),
            )
            account = cursor.fetchone()

            if account and check_password_hash(
                account[2], password
            ):  # account[3] is password column
                session["user_id"] = account[0]
                session["username"] = account[1]
                flash("Login successful!")
                # return redirect(url_for("home"))
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid username or password!")
        finally:
            cursor.close()
            # conn.close()

    return """
        <form method="post">
            <h2>Login</h2>
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
    """


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/list_html/<int:system>/<int:role>")
def list_html(system, role):
    # conn = get_db_connection()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
    lastShotId = cursor.fetchone()[0]
    print(f"Last Shot Id: {lastShotId}")
    # if lastShot !=0:
    # reset cursor
    cursor.close()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM role WHERE id = ?", (role,))  # ,
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
        print("No completed items. ")
        lastItem = 0
        lastOrder = 0
        # return redirect(url_for("index"))
    else:
        lastItem = lastComplete[0]
        lastOrder = lastComplete[1]
    print(f"Last item, Order: {lastItem}, {lastOrder}")
    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, shot, chief_engineer_id, researcher_id, cc_pressure_sp, He_sp, H2_sp, O2_sp FROM reports WHERE id = ?",
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
                "SELECT COUNT(*) FROM complete WHERE shot = ? AND item_id = ?",
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
    # conn.close()

    # <a href="{{ url_for('edit', id=nextItems[i][0]) }}" class="btn">Edit</a>
    # {% for line in nextItems %}
    return render_template(
        "list.html",
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
    # conn = get_db_connection()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = ?", (id,)
    )  # SELECT with WHERE
    user = cursor.fetchone()
    cursor.close()
    # conn.close()

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
            <a href="{{ url_for('dashboard') }}">Cancel</a>
        </form>
    </body>
    </html>
    """
    return render_template_string(html, user=user)


# INS: Update user data
@app.route("/attention/<int:shot_id>/<int:id>/<int:status>")
def attention(shot_id, id, status):
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
    </body>
    </html>
    """
    return render_template_string(html, user=user)


# INS: Update user data
@app.route("/insert/<int:shot_id>/<int:id>/<int:status>")
def insert(shot_id, id, status):
    # conn = get_db_connection()
    conn = get_db()
    cursor = conn.cursor()
    INSERT_LINE = (
        "INSERT INTO complete VALUES (NULL, ?, current_timestamp(), ?, ?, NULL)"
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
    # conn.close()

    # return redirect(url_for("index"))
    return redirect(url_for("list_html", system=system, role=role))


# UPDATE: Update user data
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    name = request.form["name"]
    email = request.form["email"]

    # conn = get_db_connection()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name = %s, email = %s WHERE id = %s",  # UPDATE query
        (name, email, id),
    )
    conn.commit()
    cursor.close()
    # conn.close()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
