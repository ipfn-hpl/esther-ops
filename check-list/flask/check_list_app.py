from flask import (
    Flask,
    render_template,
    render_template_string,
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

SYSTEM_CHECKLIST = (
    "SELECT item.id, item.seq_order, item.name, role.short_name, "
    "subsystem.name "
    "FROM item "
    "INNER JOIN role ON role_id=role.id "
    "INNER JOIN subsystem ON subsystem_id=subsystem.id "
    "WHERE day_phase_id=? AND subsystem_id=? "
    "ORDER BY seq_order ASC"
)

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

PARAMETERS = "SELECT cc_pressure_sp, He_sp, H2_sp,O2_sp FROM reports WHERE id=?"

# Reverse Order
REPORT_LIST = (
    "SELECT * FROM ("
    "SELECT id, series_name, shot, chief_engineer_id, researcher_id, "
    "cc_pressure_sp, He_sp, H2_sp, O2_sp FROM reports "
    "ORDER BY id DESC LIMIT ?"
    ") as myAlias ORDER BY id ASC"
    )

REPORT_FULL = (
    "SELECT item_id, item.seq_order, "
    "time_date, item.name, "
    "role.short_name AS Resp, complete_status.short_status "
    "FROM complete "
    "INNER JOIN item ON item_id = item.id "
    "INNER JOIN role ON item.role_id = role.id "
    "INNER JOIN complete_status ON "
    "complete_status_id = complete_status.id "
    "WHERE complete.shot = ? "
    "ORDER BY time_date ASC"
)

OPERATOR_ROLES = (
    "SELECT operator_roles.role_id, role.name FROM `operator_roles` "
    "INNER JOIN role ON role_id = role.id "
    "WHERE operator_id=?"
)

app = Flask(__name__)
# app.secret_key = "your-secret-key-random"  # Change this to a random secret key
# app.secret_key = os.urandom(24)
app.secret_key = (
    b"4\xaf\xa4\x05\xc9\xcdQ\x17\x86Q\xb5\x17m\x02\x07\x97b\xcd\xc8s\xdd\x1e\xc3j"
)
# print(f"app.secrte: {app.secret_key}")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=120)


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
    # return 'Welcome to ESTHER! Please <a href="/login">Login</a>'
    # return 'Welcome! <a href="/login">Login</a> | <a href="/register">Register</a>'

    return """
<!DOCTYPE html>
<html>
  <head>
    <title>Flask ESTHER Checklist App - MariaDB</title>
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
    <h1> Esther Checklist Management. </h1>
    <p>Welcome to ESTHER! Please <a href="/login">Login</a></p>
    <p>Show last Shot <a href="/report">Report</a></p>
    <p>(to get report for orher shot Id, add "/shotNumber" to the end of the <a href="/report">Link</a>)</p>
  </body>
</html>
    """


@app.route("/report")
@app.route("/report/<int:shot_id>")
def report(shot_id=None):
    conn = get_db()
    if shot_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        shotId = cursor.fetchone()[0]
        cursor.close()
    else:
        shotId = shot_id

    cursor = conn.cursor()
    cursor.execute(
        REPORT_FULL,
        (shotId,),
    )
    completed = cursor.fetchall()
    return render_template(
        "report.html",
        shotId=shotId,
        completed=completed,
    )


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
                cursor.close()
                cursor = conn.cursor()
                user_id = account[0]
                cursor.execute(
                    OPERATOR_ROLES,
                    (user_id,),
                )
                rls = cursor.fetchall()
                roles = []
                for rl in rls:
                    roles.append(rl)
                print(f"User Roles: {roles}")
                session["user_id"] = user_id
                session["username"] = account[1]
                session["roles"] = roles
                flash("Login successful!")
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


# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, shot FROM reports WHERE series_name IN ('S', 'E')  ORDER BY shot DESC LIMIT 1"
    )
    last = cursor.fetchone()
    shot_id = int(last[0])
    shot = last[1]
    print(f"Last Id: {shot_id}, Shot: {shot},")
    cursor.close()
    if request.method == "POST":
        shot = request.form["shot"]
        cc_pressure_sp = request.form["cc_pressure_sp"]
        he_sp = request.form["He_sp"]
        h2_sp = request.form["H2_sp"]
        o2_sp = request.form["O2_sp"]

        cursor = conn.cursor()
        cursor.execute(
            "SELECT shot FROM reports WHERE series_name='S' AND shot=?", (shot,)
        )
        shot_exist = cursor.fetchone()
        cursor.close()

        #    cursor.execute(
        cursor = conn.cursor()
        try:
            if shot_exist:
                flash("Shot already Exist")
            else:
                sql = "INSERT INTO users (series_name, shot,cc_pressure_sp, He_sp, H2_sp, O2_sp) VALUES ('S',{0:s},{1:s},{2:s},{3:s},{4:s},)"
                print(
                    sql.format(shot, cc_pressure_sp, he_sp, h2_sp, o2_sp),
                )
                sql = "INSERT INTO users (series_name, shot,cc_pressure_sp, He_sp, H2_sp, O2_sp) VALUES ('S',?,?,?,?,?)"
                # Insert new Shot
                # cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                #             (username, email, hashed_password))
                # conn.commit()
        # Check if user already exists
        # cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        # account = cursor.fetchone()

        # if account:
        #    flash('Username or email already exists!')
        # else:
        #    cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
        #                 (username, email, hashed_password))
        #    conn.commit()
        #    flash('Registration successful! Please login.')
        #    return redirect(url_for('login'))
        finally:
            cursor.close()
            # conn.close()

    form_html = """
        <form method="post">
            <h2>Register new Shot</h2>
            <p>Shot: <input type="number" id="shot" name="shot" value="{{ shot }}" required></p><br>
            <p>CC Pressure SP <input type="number" id="CC" name="cc_pressure_sp" value="40.0" min="1.0" max="110.0" step="0.1" > <br/>
            <p>Ratios He_sp <input type="number" id="He" name="He_sp" value="10.0" min="1.0" max="20.0" step="0.1"> /
            H2_sp <input type="number" id="H2" name="H2_sp" value="2.0" min="0.4" max="4.0" step="0.1" > /
            O2_sp <input type="number" id="He_sp" name="O2_sp" value="1.2" min="0.2" max="3.0" step="0.1" ><br>
            <button type="submit">Register</button><br/>
            <a href={{ url_for('dashboard', shot=shot_id) }}>Dashboard / Login</a><br/>
            <a href={{ url_for('report', shot_id=shot_id) }}>Last Shot Report</a>
        </form>
    """
    return render_template_string(form_html, shot=shot, shot_id=shot_id)


# Protected dashboard route
@app.route("/dashboard")
@app.route("/dashboard/<int:shot>")
@login_required
def dashboard(shot=None):
    conn = get_db()
    if shot is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        shotId = cursor.fetchone()[0]
        cursor.close()
    else:
        shotId = shot
    return render_template("dashboard.html", shotId=shotId, roles=session["roles"])


@app.route("/report_list")
@app.route("/report_list/<int:limit>")
def report_list(
    limit=10,
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        REPORT_LIST,
        (limit, ),
    )
    report_list = cursor.fetchall()
    cursor.close()
    print(f"report_list: {report_list}")
    return render_template(
        "report_list.html",
        report_list=report_list,
        lenList=len(report_list),
    )

@app.route("/system_list/<int:phase>/<int:system>")
def system_list(
    phase,
    system,
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        SYSTEM_CHECKLIST,
        (phase, system),
    )
    system_list = cursor.fetchall()
    cursor.close()
    sList = []
    for item in system_list:
        cursor = conn.cursor()
        print(f"Item: {item}")
        cursor.execute(
            "SELECT after_item_id FROM precedence WHERE item_id=?",
            (item[0],),
        )
        precedence_list = cursor.fetchall()
        newItem = []
        for field in item:
            newItem.append(field)
        newItem.append(precedence_list)
        sList.append(newItem)
        cursor.close()

    print(f"sList: {sList}")
    return render_template(
        "system_list.html",
        phase=phase,
        system=system,
        system_list=sList,
        lenList=len(system_list),
    )


@app.route("/list_html/<int:system>/<int:role>")
@app.route("/list_html/<int:system>/<int:role>/<int:shot>")
@login_required
def list_html(system, role, shot=None):
    # conn = get_db_connection()
    conn = get_db()
    if shot is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        shotId = cursor.fetchone()[0]
        cursor.close()
    else:
        shotId = shot

    print(f"Last Shot Id: {shotId}")
    # if lastShot !=0:
    # reset cursor
    cursor = conn.cursor()
    cursor.execute(PARAMETERS, (shotId,))  # ,
    parameters = cursor.fetchone()
    # print(f"roleName : {role}:{roleName}")

    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (shotId, system, role),
    )
    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (shotId, system, role),
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
        (shotId,),
    )
    report = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKLINES,
        (shotId, system),
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
                "SELECT COUNT(*) FROM complete WHERE shot=? AND item_id=?",
                (
                    shotId,
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
        "check_list.html",
        shotId=shotId,
        report=report,
        completed=completed,
        missingItems=missingItems,
        lenMissing=len(missingItems),
        nextItems=nextItems,
        lenNext=len(nextItems),
        roleName=role,
        parameters=parameters,
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
