from flask import Flask
from flask import render_template
from flask import request, redirect, url_for
from flask import jsonify
import sqlite3
import uuid
import database

app = Flask(__name__)

# db Instanz
db = database.Database()

# Dictionary which safes the information for the new project
new_project_info = dict(
    project_name="", project_description="", project_member=[], project_funder=[]
)


def create_dbs():
    # Öffne eine Verbindung zur Datenbank
    conn_user_data = db.create_connection(db.login_db)
    conn_all_users = db.create_connection(db.all_users_db)
    conn_project = db.create_connection(db.project_db)

    user_table = """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id TEXT PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL,
                mail TEXT VARCHAR NOT NULL,
                passwort_hash TEXT NOT NULL
            )"""

    # Erstelle die Nutzertabelle mit allen Nutzern fürs login & registrieren
    db.create_table(conn_user_data, user_table)

    all_users_table = """CREATE TABLE IF NOT EXISTS all_users (
                user_id TEXT PRIMARY KEY,
                username VARCHAR UNIQUE NOT NULL
            )"""

    # Erstelle eine Nutzertabell mit allen Nutzern, um auf id & username zugreifen zu können
    db.create_table(conn_all_users, all_users_table)

    project_table = """CREATE TABLE IF NOT EXISTS PROJECT (
                      PID VARCHAR(40) PRIMARY KEY,
                      NAME VARCHAR(30) NOT NULL,
                      DESCRIPTION TEXT NOT NULL,
                      ADMIN VARCHAR(40) NOT NULL,
                      FUNDER TEXT
                ); """

    # Erstelle ein Projekttabelle für alle Projekte
    db.create_table(conn_project, project_table)


@app.route("/")
def starting_page():

    """
    ### TEST ###
    create_dbs()

    con_login = db.create_connection(db.login_db)
    db.register_user(con_login, "LukasB", "wasgeht@Email.com", "Test123")
    db.register_user(con_login, "LukasD", "wasgeht@Email.com", "Test2")
    """
    return redirect("login")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login/check", methods=["POST"])
def check_login():
    # username vom input Field bekommen
    username = request.form["username"]

    # password vom input Field bekommen
    password = request.form["password"]

    # wenn eins der beiden leer: erneuter Versuch
    if username == "" or password == "":
        return redirect(url_for("login"))

    # conection zur login Datenbank
    login_conn = db.create_connection(db.login_db)

    # wenn Passwort & Nutzername inkorrekt
    if db.login_user(login_conn, username, password) == False:
        return redirect(url_for("login"))

    else:
        # id des nutzer aus der DB anfragen
        cursor = login_conn.cursor()
        id = cursor.execute(
            "SELECT user_id FROM user_data WHERE username = ?",
            (username,),
        )

        # id aus der Anfrage ziehen
        row = cursor.fetchone()
        if row is not None:
            # Tupel entpacken
            id = row[0]

        # id auf den eingelogten Nutzer setzten
        db.set_id(id)

        return redirect(url_for("dashboard", username=username))


@app.route("/dashboard/<username>")
def dashboard(username):

    # wenn der übergebene Nutzer nicht mit dem angemeldeten Nutzer übereinstimmt, zurück zu login
    if db.get_id() != db.get_from_name_id(username):
        return redirect(url_for("login"))

    # Erstellt eine Liste von Projektdaten für 19 Projekte mit formatierten Details
    projects = []

    for i in range(1, 20):
        if i < 10:
            i = "0" + str(i)

        new_project = [
            "name" + str(i),
            "open",
            "writer",
            "namen + " + str(i) + " member",
            str(i) + ".06.2024",
        ]
        projects.append(new_project)

    return render_template("dashboard.html", text_for_column=projects)


@app.route("/NewProject")
def new_project():
    # rendering the NewProject page with project_user and project_funding as parameters
    return render_template(
        "NewProjectUI.html",
        name_value=new_project_info["project_name"],
        description_value=new_project_info["project_description"],
        user=new_project_info["project_member"],
        funder=new_project_info["project_funder"],
    )


# function to add a new Member to a newProject
@app.route("/NewProject/add_user", methods=["POST"])
def add_user():
    # request from the html where forms have the name name. Because this is an input the typed name of the new member is selected.
    user = request.form["name"]
    # the new Member is appended to the project_user list
    new_project_info["project_member"].append(user)
    # with redirect(url_for) we directly get back to the NewProject page
    return redirect(url_for("new_project"))


# Function to save the projectname and the project description
@app.route("/NewProject/save_data", methods=["POST"])
def save_data():
    # request the json data which contains the projectname and the projectdescription
    data = request.json
    # set variables to save the project_name and the project_description
    project_name = data.get("project_name")
    project_description = data.get("project_description")

    # if Project_name data or project_description data were correctly transfered save the data in the dictionary
    if project_name or project_description:
        new_project_info["project_name"] = project_name
        new_project_info["project_description"] = project_description
        # return successmessage
        return (
            jsonify(
                {
                    "message": "Project data saved successfully",
                    "projects": new_project_info,
                }
            ),
            200,
        )
    # if data was not transfered correctly
    else:
        # return error message
        return jsonify({"message": "Invalid data"}), 400


@app.route("/NewProject/add_funding", methods=["POST"])
def add_funding():
    # request from the html where forms have the name name. Because this is an input the typed name of the new funder is selected
    funder = request.form["name"]
    # the new funder is added to the project_funder list
    new_project_info["project_funder"].append(funder)
    # redirect to the NewProject page
    return redirect(url_for("new_project"))


# Nach dem Entwurf eines Projekts werden die Daten in der Datenbank gespeichert
@app.route("/NewProject/create_project")
def create_project():

    # Objekt der Datenbank erzeugen und connecten

    nid = db.get_id()
    conn = db.create_connection(db.project_db)

    project_table = """CREATE TABLE IF NOT EXISTS PROJECT (
                      PID VARCHAR(40) PRIMARY KEY,
                      NAME VARCHAR(30) NOT NULL,
                      DESCRIPTION TEXT NOT NULL,
                      ADMIN VARCHAR(40) NOT NULL,
                      FUNDER TEXT
                ); """

    user_table = f"""
                CREATE TABLE IF NOT EXISTS {nid} (
                      PID VARCHAR(40) NOT NULL,
                      ROLE VARCHAR(5) NOT NULL,
                      FOREIGN KEY (PID) REFERENCES PROJECT(PID)
                );
            """

    # User Tabelle erstellen
    db.create_table(conn, user_table)

    # PID erstellen
    pid = str(uuid.uuid4())

    # Die NID des Admins vom Projekt
    user_admin = nid

    # Tupel erstellen
    user_values = (pid, "admin")

    # Tupel in Tabelle einfügen
    db.insert_user(conn, user_values)

    # Drucke User Tabelle
    print_table(conn, nid)

    # die benötigten Daten aus dem Dictionary holen
    project_name = new_project_info["project_name"]
    project_description = new_project_info["project_description"]
    project_funder = new_project_info["project_funder"]
    project_funder_str = ",".join(project_funder)

    # Projekt Tabelle erstellen
    db.create_table(conn, project_table)

    # Tupel erstellen
    project_values = (
        pid,
        project_name,
        project_description,
        user_admin,
        project_funder_str,
    )

    # Tupel in Projekt Tabelle einfügen
    db.insert_project(conn, project_values)

    # Plan: Die PID zu den einzelnen Member Tabellen einfügen
    for member in new_project_info["project_member"]:
        member_id = db.get_from_name_id(conn, member)
        db.add_values_to_member(conn, member_id, (pid, "read"))

    # drucke PROJKET Tabelle
    print_table(conn, "PROJECT")

    # Das Dictonary nach dem eingeben wieder leeren
    new_project_info["project_name"] = ""
    new_project_info["project_description"] = ""
    new_project_info["project_funder"] = []
    new_project_info["project_member"] = []

    return redirect(url_for("dashboard"))


# Druckt die Tabelle
def print_table(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        print(f"Data from {table_name}:")
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        print(f"Error reading from table {table_name}: {e}")


if __name__ == "__main__":
    app.run(debug=True)
