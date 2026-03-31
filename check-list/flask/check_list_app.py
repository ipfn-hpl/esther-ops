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

import psycopg2
import psycopg2.extras
import sys
# import os

# Import Secrets
from config_psql import DB_CONFIG
# from werkzeug.security import  generate_password_hash
# hashed_password = generate_password_hash("xxxx", method="pbkdf2:sha256")
# print(hashed_password)


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
    query = "SELECT * FROM get_complete_report(%s)"
    cursor.execute(
        query,
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
                query = "SELECT * FROM get_operator_roles(%s)"
                cursor.execute(
                    query,
                    # OPERATOR_ROLES,
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
        "SELECT id, shot FROM reports WHERE series_name IN ('S', 'H')  ORDER BY id DESC LIMIT 1"
    )
    rec = cursor.fetchone()
    if rec:
        # last = cursor.fetchone()
        report_id = int(rec[0])
        shot = rec[1]
        print(f"Last Id: {report_id}, Shot: {shot},")
    cursor.close()
    if request.method == "POST":
        reportId = request.form["reportId"]
        cc_pressure_sp = request.form["cc_pressure_sp"]
        he_sp = request.form["he_sp"]
        h2_sp = request.form["h2_sp"]
        o2_sp = request.form["o2_sp"]

        cursor = conn.cursor()
        # "SELECT id FROM reports WHERE series_name='S' AND id=%s", (reportId,)
        cursor.execute("SELECT id FROM reports WHERE id=%s", (reportId,))
        report_exist = cursor.fetchone()
        cursor.close()

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
            <a href={{ url_for('report', report_id=report_id) }}>Last Shot Report</a>
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
        rec = cursor.fetchone()
        if rec:
            reportId = rec[0]
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
    query = "SELECT * FROM get_last_reports(%s)"
    cursor.execute(
        query,
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
        rec = cursor.fetchone()
        if rec:
            timeDate.append(rec[0])
        cursor.close()
    print(f"timeD: {timeDate}")

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
    query = "SELECT * FROM get_system_list(%s, %s)"
    cursor.execute(
        query,
        (phase, system),
    )
    system_list = cursor.fetchall()
    cursor.close()
    sList = []
    for item in system_list:
        newItem = []
        for field in item:
            newItem.append(field)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT after_item_id FROM precedence WHERE item_id=%s",
            (item[0],),
        )
        precedence_list = cursor.fetchall()
        if precedence_list:
            # print(f"Item: {item}")
            newItem.append(precedence_list)

        sList.append(newItem)
        cursor.close()

    print(f"sList: {sList}")
    return render_template(
        "system_list.html",
        phase=phase,
        system=system,
        system_list=sList,
    )


@app.route("/list_html/<int:phase>/<int:system>/<int:role>")
@app.route("/list_html/<int:phase>/<int:system>/<int:role>/<int:report_id>")
@login_required
def list_html(phase, system, role, report_id=None):
    # conn = get_db_connection()
    conn = get_db()
    if report_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        reportId = cursor.fetchone()[0]
        cursor.close()
    else:
        reportId = report_id

    session["phase"] = phase
    print(f"Last Report Id: {reportId} Phase: {phase}")
    # if lastShot !=0:
    # reset cursor
    cursor = conn.cursor()
    query = "SELECT cc_pressure_sp, he_sp, h2_sp, o2_sp FROM reports WHERE id=%s"
    cursor.execute(query, (reportId,))  # ,
    parameters = cursor.fetchone()
    # print(f"roleName : {role}:{roleName}")

    cursor.close()
    cursor = conn.cursor()
    query = "SELECT item_id, seq_order FROM last_signed(%s,%s,%s,%s)"
    cursor.execute(
        # LAST_CHECKED,
        query,
        (
            reportId,
            phase,
            system,
            role,
        ),
    )
    # lastComplete = cursor.fetchone()
    lastItem, lastOrder = cursor.fetchone()
    cursor.close()
    cursor = conn.cursor()
    if lastOrder is None:
        lastOrder = 0
    print(f"Last item, {lastItem}, Order: {lastOrder}")
    cursor.execute(
        "SELECT id, shot, chief_engineer_id, researcher_id, cc_pressure_sp, he_sp, h2_sp, o2_sp FROM reports WHERE id = %s",
        (reportId,),
    )
    reportItems = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    query = "SELECT * FROM get_signed_items(%s, %s)"
    cursor.execute(
        query,
        # LAST_CHECKLINES,
        (
            reportId,
            system,
        ),
    )
    completed = cursor.fetchall()
    # print("Completed")

    cursor.close()
    cursor = conn.cursor()
    query = "SELECT * FROM get_next_items(%s,%s,%s,%s, 3)"
    cursor.execute(
        # NEXT_CHECKLINES,
        query,
        (
            phase,
            system,
            role,
            lastOrder,
        ),
    )
    nextItems = cursor.fetchall()
    cursor.close()
    if not nextItems:
        # print("No results found")
        missingItems = []
    else:
        # print(f"Found {len(nextItems)} rows")
        nextItem2Sign = nextItems[0][0]
        print(f"Next item to sign: {nextItem2Sign}")
        # for row in nextItems:
        #    print(row)
        cursor = conn.cursor()
        query = "SELECT * FROM check_missing_items(%s,%s)"
        cursor.execute(
            # NEXT_CHECKLINES,
            query,
            (
                reportId,
                nextItem2Sign,
            ),
        )
        precedenceItems = cursor.fetchall()
        cursor.close()
        missingItems = []
        failedItems = []
        if not precedenceItems:
            print("No precedenceItems found")
            # missingItems = []
        else:
            print("Checking items for next to sign: ")
            for row in precedenceItems:
                print(row)
                if row[3] is False:
                    cursor = conn.cursor()
                    query = (
                        "SELECT * FROM missing_item(%s) AS "
                        "(r_short_name TEXT, i_id INT,  i_seq_order SMALLINT, "
                        "i_name TEXT, s_name TEXT, d_short_name TEXT)"
                    )
                    cursor.execute(
                        query,
                        (row[0],),
                    )
                    rec = cursor.fetchone()
                    if rec:
                        missingItems.append(rec)
                    cursor.close()
                elif row[2] != 0:
                    failedItems.append(row)
                    print(f"Failed item: {row}")

    cursor.close()
    cursor = conn.cursor()
    query = "SELECT name FROM subsystem WHERE id=%s"
    cursor.execute(
        # NEXT_CHECKLINES,
        query,
        (system,),
    )
    systemName = cursor.fetchone()[0]
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
        # lenNext=len(nextItems),
        roleName=role,
        systemName=systemName,
        phase=phase,
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
    rec = cursor.fetchone()
    if rec:
        # item = rec
        system_id = rec[0]
        role_id = rec[1]
        name = rec[2]
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

    cursor.close()
    cursor = conn.cursor()
    try:
        select_query = (
            "SELECT subsystem_id, day_phase_id, role_id FROM item WHERE id = %s"
        )
        cursor.execute(select_query, (item_id,))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print(f"executed query {cursor.query}")
    rec = cursor.fetchone()
    if rec:
        system = rec[0]
        phase = rec[1]
        role = rec[2]
    # print(f"System: {system}, Role: {role}")

    cursor.close()

    return redirect(url_for("list_html", system=system, phase=phase, role=role))


@app.route("/item_details")
@app.route("/item_details/<int:item_id>")
def item_details(item_id=None):
    conn = get_db()
    if item_id is None:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM item ORDER BY id DESC LIMIT 1")
        item_id = cursor.fetchone()[0]
        cursor.close()

    cursor = conn.cursor()
    query = (
        "SELECT * FROM item_details(%s) AS "
        "(d_short_name TEXT, s_name TEXT, r_short_name TEXT, i_id INT, i_seq_order SMALLINT, i_name TEXT)"
    )
    # "SELECT * FROM item_details(%s) AS (r_short_name TEXT, i_id INT,  i_seq_order SMALLINT, i_name TEXT, s_name TEXT, d_short_name TEXT);"
    cursor.execute(
        query,
        (item_id,),
    )
    item_details = cursor.fetchone()
    if item_details:
        lenPrec = len(item_details[5])
        print(f"Prec: {item_details[5]}, len:{lenPrec}")
    else:
        lenPrec = 0
    return render_template(
        "item_details.html",
        lenPrec=lenPrec,
        item_details=item_details,
    )


if __name__ == "__main__":
    # init_db()
    app.run(debug=True)
