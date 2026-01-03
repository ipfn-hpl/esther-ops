from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    g,
)

#    render_template_string,
from werkzeug.security import check_password_hash  # generate_password_hash,
from functools import wraps
from datetime import timedelta
import mariadb
import sys
# import os

# import Secrets
from config import DB_CONFIG
# from werkzeug.security import  generate_password_hash
# hashed_password = generate_password_hash("xxxx", method="pbkdf2:sha256")
# print(hashed_password)

DAYPHASE = 1  # Only this phase Implemented

# Reverse Order
LAST_CHECKLINES = (
    "SELECT * FROM ("
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
    ") as myAlias ORDER BY time_date ASC"
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
# app.secret_key = os.urandom(24)
app.secret_key = (
    b"4\xaf\xa4\x05\xc9\xcdQ\x17\x86Q\xb5\x17m\x02\x07\x97b\xcd\xc8s\xdd\x1e\xc3j"
)
# print(f"app.secrte: {app.secret_key}")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60)


def get_db():
    """Get database connection from Flask's g object (request context)"""
    if "db" not in g:
        try:
            g.db = mariadb.connect(**DB_CONFIG)
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB: {e}")
            sys.exit(1)
    return g.db


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


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
        return f'Welcome to Esther CheckLists, {session["username"]}! <a href="/dashboard">Dashboard</a> | <a href="/logout">Logout</a>'
        # return redirect(url_for("dashboard"))
    return 'Welcome to ESTHER! Please <a href="/login">Login</a>'
    # return 'Welcome! <a href="/login">Login</a> | <a href="/register">Register</a>'


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

    return """
        <form method="post">
            <h2>Login</h2>
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
    """


# Protected dashboard route
@app.route("/dashboard")
@app.route("/dashboard/<int:shot>")
@login_required
def dashboard(shot=None):
    if shot is None:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        shotId = cursor.fetchone()[0]
        cursor.close()
    else:
        shotId = shot
    return render_template("dashboard.html", shotId=shotId)


@app.route("/list_html/<int:system>/<int:role>")
@app.route("/list_html/<int:system>/<int:role>/<int:shot>")
@login_required
def list_html(system, role, shot=None):
    # conn = get_db_connection()
    conn = get_db()
    if shot is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        ShotId = cursor.fetchone()[0]
        cursor.close()
    else:
        ShotId = shot

    print(f"Last Shot Id: {ShotId}")
    # if lastShot !=0:
    # reset cursor
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM role WHERE id = ?", (role,))  # ,
    roleName = cursor.fetchone()[0]
    # print(f"roleName : {role}:{roleName}")

    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (ShotId, system, role),
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
        (ShotId,),
    )
    report = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKLINES,
        (ShotId, system),
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
                    ShotId,
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

    # <a href="{{ url_for('edit', id=nextItems[i][0]) }}" class="btn">Edit</a>
    # {% for line in nextItems %}
    return render_template(
        "list.html",
        shotId=ShotId,
        report=report,
        completed=completed,
        missingItems=missingItems,
        lenMissing=len(missingItems),
        nextItems=nextItems,
        lenNext=len(nextItems),
        roleName=roleName,
    )


# I
@app.route("/attention/<int:shot_id>/<int:item_id>")
@login_required
def attention(shot_id, item_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT subsystem_id,role_id,name FROM item WHERE id = ?",
        (item_id,),
    )
    item = cursor.fetchone()
    system_id = item[0]
    role_id = item[1]
    name = item[2]
    print(f"System: {system_id}, Role: {role_id}")
    return render_template(
        "attention.html",
        name=name,
        shot_id=shot_id,
        item_id=item_id,
        system_id=system_id,
        role_id=role_id,
    )


# INSERT: Complete Action Status
@app.route("/insert/<int:shot_id>/<int:item_id>/<int:status>")
@login_required
def insert(shot_id, item_id, status):
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
            item_id,
            status,
        ),
    )
    # Get Item inserted
    print(
        "INSERT INTO complete VALUES (NULL, %s, current_timestamp(), %s, %s, NULL)"
        % (shot_id, item_id, status)
    )
    cursor.execute("SELECT subsystem_id, role_id FROM item WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    system = item[0]
    role = item[1]
    print(f"System: {system}, Role: {role}")

    conn.commit()
    cursor.close()

    return redirect(url_for("list_html", system=system, role=role))
    # return redirect(url_for("list_html", system=system, role=role, shot=shotId))


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
