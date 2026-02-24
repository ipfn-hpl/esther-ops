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

# import mariadb
import psycopg2
import sys
# import os

# import Secrets
from config_psql import DB_CONFIG
from sql_queries import (
    LAST_CHECKED,
    LAST_CHECKLINES,
    MISSING_ITEM,
    NEXT_CHECKLINES,
    OPERATOR_ROLES,
    PARAMETERS,
    PRECENDENCE,
    REPORT_LIST,
    REPORT_FULL,
    SYSTEM_CHECKLIST,
)
# from werkzeug.security import  generate_password_hash
# hashed_password = generate_password_hash("xxxx", method="pbkdf2:sha256")
# print(hashed_password)

DAYPHASE = 1  # Only this phase Implemented


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
            # g.db = mariadb.connect(**DB_CONFIG)
            g.db = psycopg2.connect(**DB_CONFIG)
        except psycopg2.Error as e:
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
    <p>(to get report for other shot Id, add "/report_id Number" to the end of the <a href="/report">Link</a>)</p>
  </body>
</html>
    """


@app.route("/report")
@app.route("/report/<int:report_id>")
def report(report_id=None):
    conn = get_db()
    if report_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        reportId = cursor.fetchone()[0]
        cursor.close()
    else:
        reportId = report_id

    cursor = conn.cursor()
    cursor.execute(
        REPORT_FULL,
        (reportId,),
    )
    completed = cursor.fetchall()
    return render_template(
        "report.html",
        reportId=reportId,
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
                "SELECT id, username, password FROM operator WHERE username = %s",
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
        "SELECT id, shot FROM reports WHERE series_name IN ('S', 'E')  ORDER BY id DESC LIMIT 1"
    )
    last = cursor.fetchone()
    report_id = int(last[0])
    shot = last[1]
    print(f"Last Id: {report_id}, Shot: {shot},")
    cursor.close()
    if request.method == "POST":
        reportId = request.form["reportId"]
        cc_pressure_sp = request.form["cc_pressure_sp"]
        he_sp = request.form["he_sp"]
        h2_sp = request.form["h2_sp"]
        o2_sp = request.form["o2_sp"]

        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM reports WHERE series_name='S' AND id=%s", (reportId,)
        )
        report_exist = cursor.fetchone()
        cursor.close()

        #    cursor.execute(
        cursor = conn.cursor()
        if report_exist:
            flash("Shot already Exist")
        else:
            try:
                sql = "INSERT INTO reports (series_name, shot,cc_pressure_sp, he_sp, h2_sp, o2_sp) VALUES ('S',{0:s},{1:s},{2:s},{3:s},{4:s},)"
                print(
                    sql.format(shot, cc_pressure_sp, he_sp, h2_sp, o2_sp),
                )
                sql = (
                    "INSERT INTO reports (series_name, shot,cc_pressure_sp, he_sp, h2_sp, o2_sp) "
                    "VALUES ('S',%s,%s,%s,%s,%s)"
                )
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

    form_html = """
        <form method="post">
            <h2>Register new Shot</h2>
            <p>Shot: <input type="number" id="shot" name="shot" value="{{ shot }}" required></p><br>
            <p>CC Pressure SP <input type="number" id="CC" name="cc_pressure_sp" value="40.0" min="1.0" max="110.0" step="0.1" > <br/>
            <p>Ratios He_sp <input type="number" id="He" name="He_sp" value="10.0" min="1.0" max="20.0" step="0.1"> /
            H2_sp <input type="number" id="H2" name="H2_sp" value="2.0" min="0.4" max="4.0" step="0.1" > /
            O2_sp <input type="number" id="He_sp" name="O2_sp" value="1.2" min="0.2" max="3.0" step="0.1" ><br>
            <button type="submit">Register</button><br/>
            <a href={{ url_for('dashboard', reportId=report_id) }}>Dashboard / Login</a><br/>
            <a href={{ url_for('report', shot_id=report_id) }}>Last Shot Report</a>
        </form>
    """
    return render_template_string(form_html, shot=shot, shot_id=report_id)


# Protected dashboard route
@app.route("/dashboard")
@app.route("/dashboard/<int:report_id>")
@login_required
def dashboard(report_id=None):
    conn = get_db()
    if report_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        reportId = cursor.fetchone()[0]
        cursor.close()
    else:
        reportId = report_id
    return render_template("dashboard.html", reportId=reportId, roles=session["roles"])


@app.route("/report_list")
@app.route("/report_list/<int:limit>")
def report_list(
    limit=10,
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        REPORT_LIST,
        (limit,),
    )
    report_list = cursor.fetchall()
    cursor.close()
    timeDate = []
    for rprt in report_list:
        cursor = conn.cursor()
        print(f"Report: {rprt}")
        cursor.execute(
            "SELECT time_date FROM complete WHERE report_id=%s ORDER BY time_date ASC LIMIT 1",
            (rprt[0],),
        )
        timeDate.append(cursor.fetchone()[0])
        cursor.close()
    print(f"timeD: {timeDate}")

    # print(f"report_list: {report_list}")
    return render_template(
        "report_list.html",
        report_list=report_list,
        lenList=len(report_list),
        timeDate=timeDate,
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
            "SELECT after_item_id FROM precedence WHERE item_id=%s",
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
@app.route("/list_html/<int:system>/<int:role>/<int:report_id>")
@login_required
def list_html(system, role, report_id=None):
    # conn = get_db_connection()
    conn = get_db()
    if report_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        reportId = cursor.fetchone()[0]
        cursor.close()
    else:
        reportId = report_id

    print(f"Last Report Id: {reportId}")
    # if lastShot !=0:
    # reset cursor
    cursor = conn.cursor()
    cursor.execute(PARAMETERS, (reportId,))  # ,
    parameters = cursor.fetchone()
    # print(f"roleName : {role}:{roleName}")

    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (reportId, system, role),
    )
    cursor.close()
    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKED,
        (reportId, system, role),
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
        "SELECT id, shot, chief_engineer_id, researcher_id, cc_pressure_sp, he_sp, h2_sp, o2_sp FROM reports WHERE id = %s",
        (reportId,),
    )
    reportItems = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute(
        LAST_CHECKLINES,
        (reportId, system),
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
                "SELECT COUNT(*) FROM complete WHERE report_id=%s AND item_id=%s",
                (
                    reportId,
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
        reportId=reportId,
        reportItems=reportItems,
        completed=completed,
        missingItems=missingItems,
        lenMissing=len(missingItems),
        nextItems=nextItems,
        lenNext=len(nextItems),
        roleName=role,
        parameters=parameters,
    )


# I
@app.route("/attention/<int:report_id>/<int:item_id>")
@login_required
def attention(report_id, item_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT subsystem_id,role_id,name FROM item WHERE id = %s",
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
        report_id=report_id,
        item_id=item_id,
        system_id=system_id,
        role_id=role_id,
    )


# INSERT: Complete Action Status
@app.route("/insert/<int:report_id>/<int:item_id>/<int:status>")
@login_required
def insert(report_id, item_id, status):
    # conn = get_db_connection()
    conn = get_db()
    cursor = conn.cursor()
    INSERT_LINE = (
        "INSERT INTO complete (report_id, time_date, item_id, complete_status_id) "
        "VALUES (%s, current_timestamp, %s, %s)"
    )
    try:
        cursor.execute(
            INSERT_LINE,
            (
                report_id,
                item_id,
                status,
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"executed query {cursor.query}")

    # Get Item inserted
    # print(
    # "INSERT INTO complete VALUES (NULL, %s, current_timestamp, %s, %s, NULL)"
    # % (report_id, item_id, status)
    # )
    cursor.close()
    cursor = conn.cursor()
    try:
        select_query = "SELECT subsystem_id, role_id FROM item WHERE id = %s"
        cursor.execute(select_query, (item_id,))
        # cursor.execute("SELECT subsystem_id, role_id FROM item WHERE id = %s", (item_id,))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"executed query {cursor.query}")
    item = cursor.fetchone()
    system = item[0]
    role = item[1]
    print(f"System: {system}, Role: {role}")

    # conn.commit()
    cursor.close()

    return redirect(url_for("list_html", system=system, role=role))
    # return redirect(url_for("list_html", system=system, role=role, shot=shotId))


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
