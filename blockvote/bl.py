from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
import hashlib
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "blockvote_secret"

USER_FILE = "users.json"
CANDIDATE_FILE = "candidates.json"
ELECTION_FILE = "elections.json"
FRAUD_FILE = "fraud_logs.json"

UPLOAD_FOLDER = "static/uploads"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_json(file, default):
    if not os.path.exists(file):
        return default

    with open(file, "r") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        wallet = request.form["wallet"].strip()

        users = load_json(USER_FILE, {})

        if username in users:
            return render_template(
                "register.html",
                error="Username already exists"
            )

        for user in users.values():

            if user["wallet"].lower() == wallet.lower():

                return render_template(
                    "register.html",
                    error="Wallet already registered"
                )

        users[username] = {
            "password": hash_password(password),
            "wallet": wallet,
            "has_voted": False
        }

        save_json(USER_FILE, users)

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        users = load_json(USER_FILE, {})

        if username not in users:

            return render_template(
                "login.html",
                error="Invalid username"
            )

        if users[username]["password"] != hash_password(password):

            return render_template(
                "login.html",
                error="Wrong password"
            )

        session["username"] = username

        return redirect("/vote")

    return render_template("login.html")


@app.route("/vote")
def vote():

    if "username" not in session:
        return redirect("/login")

    election = load_json(
        ELECTION_FILE,
        {"active": False, "link_code": ""}
    )

    if not election["active"]:

        return """
        <h1>Voting is not active</h1>
        <a href='/login'>Go Back</a>
        """

    users = load_json(USER_FILE, {})
    candidates = load_json(CANDIDATE_FILE, [])

    username = session["username"]

    return render_template(
        "vote.html",
        username=username,
        wallet=users[username]["wallet"],
        candidates=candidates
    )


@app.route("/check_vote", methods=["POST"])
def check_vote():

    if "username" not in session:

        return jsonify({
            "allowed": False,
            "message": "Login required"
        })

    data = request.json
    wallet = data["wallet"]

    users = load_json(USER_FILE, {})
    username = session["username"]

    if users[username]["wallet"].lower() != wallet.lower():

        return jsonify({
            "allowed": False,
            "message": "Fake identity blocked"
        })

    if users[username]["has_voted"]:

        return jsonify({
            "allowed": False,
            "message": "You already voted"
        })

    return jsonify({"allowed": True})


@app.route("/mark_voted", methods=["POST"])
def mark_voted():

    if "username" not in session:
        return jsonify({"success": False})

    users = load_json(USER_FILE, {})
    username = session["username"]

    users[username]["has_voted"] = True

    save_json(USER_FILE, users)

    return jsonify({"success": True})


@app.route("/result")
def result():

    candidates = load_json(CANDIDATE_FILE, [])

    return render_template(
        "result.html",
        candidates=candidates
    )


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Invalid admin login"
        )

    return render_template("admin_login.html")


@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    candidates = load_json(CANDIDATE_FILE, [])

    election = load_json(
        ELECTION_FILE,
        {"active": False, "link_code": ""}
    )

    vote_link = ""

    if election["link_code"]:

        vote_link = (
            request.host_url
            +
            "election/"
            +
            election["link_code"]
        )

    return render_template(
        "admin.html",
        candidates=candidates,
        election=election,
        vote_link=vote_link
    )


@app.route("/save_candidate", methods=["POST"])
def save_candidate():

    if "admin" not in session:
        return redirect("/admin_login")

    name = request.form["name"]

    photo = request.files["photo"]

    filename = secure_filename(photo.filename)

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    photo.save(filepath)

    candidates = load_json(CANDIDATE_FILE, [])

    candidates.append({
        "name": name,
        "photo": "/static/uploads/" + filename
    })

    save_json(CANDIDATE_FILE, candidates)

    return redirect("/admin")


@app.route("/generate_link")
def generate_link():

    if "admin" not in session:
        return redirect("/admin_login")

    election = {
        "active": False,
        "link_code": str(uuid.uuid4())[:8]
    }

    save_json(ELECTION_FILE, election)

    return redirect("/admin")


@app.route("/start_election")
def start_election():

    if "admin" not in session:
        return redirect("/admin_login")

    election = load_json(
        ELECTION_FILE,
        {"active": False, "link_code": ""}
    )

    election["active"] = True

    save_json(ELECTION_FILE, election)

    return redirect("/admin")


@app.route("/end_election")
def end_election():

    if "admin" not in session:
        return redirect("/admin_login")

    election = load_json(
        ELECTION_FILE,
        {"active": False, "link_code": ""}
    )

    election["active"] = False

    save_json(ELECTION_FILE, election)

    return redirect("/admin")


@app.route("/election/<code>")
def election_link(code):

    election = load_json(
        ELECTION_FILE,
        {"active": False, "link_code": ""}
    )

    if code != election["link_code"]:

        return "<h1>Invalid Voting Link</h1>"

    if not election["active"]:

        return "<h1>Voting has not started or has ended</h1>"

    if "username" not in session:
        return redirect("/login")

    return redirect("/vote")


@app.route("/reset_demo")
def reset_demo():

    save_json(USER_FILE, {})
    save_json(CANDIDATE_FILE, [])
    save_json(FRAUD_FILE, {})

    save_json(
        ELECTION_FILE,
        {
            "active": False,
            "link_code": ""
        }
    )

    session.clear()

    return """
    <h1>Demo Reset Done</h1>
    <a href='/admin_login'>
    Go to Admin Login
    </a>
    """


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)