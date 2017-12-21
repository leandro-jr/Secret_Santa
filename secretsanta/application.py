from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import random

# Email https://github.com/kootenpv/yagmail#no-more-password-and-username
import yagmail

# Obtain Time
from datetime import datetime
from pytz import timezone

from helpers import *

# login email
MY_ADDRESS = 'xxxxx@gmail.com'
PASSWORD = '*****'

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response


# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///santa.db")

#setting the time
sao_paulo = timezone('America/Sao_Paulo')
now = datetime.now(sao_paulo).strftime("%d/%m/%y - %H:%M")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Main page with wishlist and data of the party."""

    rows_user = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    # verify if user is on a group
    group = rows_user[0]["grupo"]
    # obtain group's participants names
    rows_users = db.execute("SELECT username FROM users WHERE grupo = :grupo", grupo=group)

    # obtain username
    user = rows_user[0]["username"]
    session["username"] = user
    # set username_secret as blank while secret santa assignement wasn't done
    username_secret = ""
    username_secret_email = ""
    username_lottery = ""
    username_lottery_email =""

    # obtain user's secret friend username
    rows_friends = db.execute("SELECT * FROM friends WHERE username = :username", username=user)
    if rows_friends:
        username_secret = rows_friends[0]["username_secret"]
        # obtain user's secret friend email
        rows_users_secret = db.execute("SELECT * FROM users WHERE username = :username", username=username_secret)
        username_secret_email = rows_users_secret[0]["email"]

        # obtain user's secret friend wishlist from database
        rows_wishlist_secret = db.execute("SELECT * FROM wishlist WHERE username = :username", username=username_secret)

    # save username_secret/username_secret_email to be used on messenger
    session["username_secret"] = username_secret
    session["username_secret_email"] = username_secret_email

    # obtain username from who draw the user
    rows_friends_secret = db.execute("SELECT * FROM friends WHERE username_secret = :username_secret", username_secret=user)
    if rows_friends_secret:
        username_lottery = rows_friends_secret[0]["username"]
        session["username_lottery"] = username_lottery
        # obtain email from who who draw the user
        rows_users_lottery = db.execute("SELECT * FROM users WHERE username = :username", username=username_lottery)
        username_lottery_email = rows_users_lottery[0]["email"]
        session["username_lottery_email"] = username_lottery_email

    # save username_secret/username_secret_email to be used on messenger
    session["username_lottery"] = username_lottery
    session["username_lottery_email"] = username_lottery_email

    # obtain user's wishlist from database
    rows_wishlist = db.execute("SELECT * FROM wishlist WHERE username = :username", username=user)
    # count rows frm the select
    count_rows_wish = 0
    for n in rows_wishlist:
        count_rows_wish = count_rows_wish + 1

    # declaring variable before the randon assigment
    date = "date not defined"
    gift_value = "0,00"
    local = "location not defined"

    # obtain gift_value, location and party's date from the database
    rows_party = db.execute("SELECT * FROM party WHERE grupo = :grupo", grupo = group)
    if rows_party:
        date = rows_party[0]["date"]
        gift_value = rows_party[0]["gift_value"]
        local = rows_party[0]["local"]


    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # add wishlist provided by the user to the database
        if request.form.get("wishlist"):
            db.execute("INSERT INTO wishlist(username, item) VALUES(:username, :item)",
                        username=user, item=request.form.get("wishlist"))
            return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        # return templates with different values if secret santa assignement was executed or not
        if username_secret == "":
            return render_template("index.html", user=user, username_secret="undefined", date=date, gift_value=gift_value, local = local)
        else:
            return render_template("index.html", user=user, username_secret=username_secret, wishlist=rows_wishlist,
                                    wishlist_secret=rows_wishlist_secret, date=date, gift_value=gift_value, local = local, group=group)


@app.route("/delete", methods=["POST"])
@login_required
def delete_wishlist():
    """Delete item from wishlist table."""
    id = request.form.get("delete_wishlist")
    db.execute("DELETE FROM wishlist WHERE Id = :id", id=id)
    # redirect user to home page
    return redirect(url_for("index"))

@app.route("/help")
def help():
    """Provide the user with a explanation on how the Secret Santa site works"""
    return render_template("help.html")


@app.route("/send_wishlist", methods=["POST"])
@login_required
def send_wishlist():
    """Send wishlist to secret friend by email."""

    # obtain user's wishlist
    rows_wishlist = db.execute("SELECT * FROM wishlist WHERE username = :username", username=session["username"])
    # create list to place the wishlist from database
    wish_list = []
    count_rows_wish = 0
    for n in rows_wishlist:
        count_rows_wish = count_rows_wish + 1
    for k in range(count_rows_wish):
        wish_list.append(rows_wishlist[k]["item"])

    # preper email
    message = wish_list
    subject = "Wishlist from Your Secret Santa: "+session["username"]
    to = session["username_lottery_email"]
    email(message, subject, to)

    # redirect user to home page
    return redirect(url_for("index"))


@app.route("/messenger", methods=["GET", "POST"])
@login_required
def messenger():
    """Provide anonymous messenger like WhatsApp+email between secret santas."""

    # get user's information from index
    username_secret = session["username_secret"]
    username_secret_email = session["username_secret_email"]
    username_lottery = session["username_lottery"]
    username_lottery_email = session["username_lottery_email"]

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #sending email to secret friend the person got on lottery
        if request.form.get("msg_to_friend"):
            message = request.form.get("msg_to_friend")
            subject = "Message from who draw you on Secret Santa"
            to = username_secret_email
            email(message, subject, to)

            # saving messages to sql
            now = datetime.now(sao_paulo).strftime("%d/%m/%y - %H:%M")
            db.execute("INSERT INTO messenger(username, msg_to_friend, time) VALUES(:username, :message, :time)", username=session["username"], message=message, time=now)


        #sending email to secret friend who got the person on lottery
        if request.form.get("msg_to_secret"):
            message = request.form.get("msg_to_secret")
            subject = "Message to who you draw on Secret Santa"
            to = username_lottery_email
            email(message, subject, to)

            # saving messages to sql
            now = datetime.now(sao_paulo).strftime("%d/%m/%y - %H:%M")
            db.execute("INSERT INTO messenger(username, msg_to_secret, time) VALUES(:username, :message, :time)", username=session["username"], message=message, time=now)

        # loading messages from sql
        rows_msg_friend = db.execute("SELECT * FROM messenger WHERE username = :username OR username = :username_secret",
                                    username=session["username"], username_secret=username_secret )
        rows_msg_lottery = db.execute("SELECT username, msg_to_secret, time FROM messenger WHERE username = :username UNION SELECT username, msg_to_friend, time FROM messenger WHERE username = :username_lottery ORDER BY time",
                                    username=session["username"], username_lottery=username_lottery)

        return render_template("messenger.html", username=session["username"], username_secret=session["username_secret"],
                                   username_lottery=username_lottery, message_friend=rows_msg_friend, message_lottery=rows_msg_lottery)

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        if username_secret == "":
            return render_template("messenger.html", username_secret="undefined")
        else:
            # selecting messages to messenger.html
            rows_msg_friend = db.execute("SELECT * FROM messenger WHERE username = :username OR username = :username_secret",
                                        username=session["username"], username_secret=username_secret)

            # limiting the messages to 200 per conversation
            count_rows_friend = 0
            for n in rows_msg_friend:
                count_rows_friend = count_rows_friend + 1

            if count_rows_friend > 200:
                row_id = db.execute("SELECT min(id) FROM messenger WHERE username = :username OR username = :username_secret",
                                    username=session["username"], username_secret=username_secret)
                id = row_id[0]["min(id)"]
                db.execute("DELETE FROM messenger WHERE id = :id", id=id)

            # selecting messages to messenger.html
            rows_msg_lottery = db.execute("SELECT username, msg_to_secret, time FROM messenger WHERE username = :username UNION SELECT username, msg_to_friend, time FROM messenger WHERE username = :username_lottery ORDER BY time",
                                        username=session["username"], username_lottery=username_lottery)

            # render template with messages:
            return render_template("messenger.html", username=session["username"], username_secret=session["username_secret"],
                                   username_lottery=username_lottery, message_friend=rows_msg_friend, message_lottery=rows_msg_lottery)

@app.route("/lottery", methods=["POST"])
@login_required
def lottery():
    """Randomly assign Secret Santa users"""

    # obtain group name and if user is group's manager
    row_manager = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    group = row_manager[0]["grupo"]
    manager = row_manager[0]["manager"]

    # obtain usernames database
    rows = db.execute("SELECT username FROM users WHERE grupo = :grupo", grupo=group)
    #calculate how many line(users) there are on the rows select
    count_rows = 0
    for n in rows:
        count_rows = count_rows + 1

    """Perform group's random assignment if user is manager"""
    if manager == 1:

        if request.form.get("lottery") == "1":
            #create user_names/user_names_del list to be used on the random assignment
            users_names = []
            users_names_del = []
            for x in range(count_rows):
                users_names.append(rows[x]["username"])
                users_names_del.append(rows[x]["username"])

            #create user_dic dictionary to save the user's pairs obatined on the lottery
            users_dic = {}
            aleat1 = random.choice(users_names)
            first_name = aleat1

            # Perform random assignment avoiding loop. Eg.: if users are A, B, C so that A->B, B->C, C->A
            while len(users_names) >= 1:
                if len(users_names) == 1:
                    users_names.remove(aleat1)
                    users_names.append(first_name)
                    aleat2 = random.choice(users_names)
                    users_dic[aleat1]=aleat2
                    users_names.remove(first_name)
                else:
                    users_names.remove(aleat1)
                    aleat2 = random.choice(users_names)
                    users_dic[aleat1]=aleat2
                    users_names.remove(aleat2)

                    if len(users_names) == 0:
                        users_names.append(first_name)
                        aleat1 = random.choice(users_names)
                        users_dic[aleat2]=aleat1
                        users_names.remove(aleat1)
                    else:
                        aleat1 = random.choice(users_names)
                        users_dic[aleat2]=aleat1

            # delete previous lottery
            for x in users_names_del:
                db.execute("DELETE FROM friends WHERE username = :username", username=x)

            # insert lottery results on database
            for user, friend in users_dic.items():
                username = user
                username_secret = friend
                db.execute("INSERT INTO friends(username, username_secret) VALUES(:username, :username_secret)",
                        username=username, username_secret=username_secret)

            # set up the SMTP server
            yag = yagmail.SMTP({MY_ADDRESS: 'Papai Noel'}, PASSWORD)

            #send msg to all group's participants
            rows_users = db.execute("SELECT email FROM users WHERE grupo = :group", group=group)
            count_users = 0
            for n in rows_users:
                count_users = count_users + 1
            for i in range(count_users):
                message = "Your Secret Santa was already randomly assigned. Go to the site and checkout!"
                subject = "Your Secret Santa was drawn"
                to = rows_users[i]["email"]
                yag.send(to = to, subject = subject, contents = message)

        return redirect(url_for("manager"))

    else:
        return redirect(url_for("manager"))

@app.route("/manager", methods=["GET", "POST"])
@login_required
def manager():
    """Manage the Secret Santa"""

    # obtain group name and if user is group's manager
    row_manager = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    group = row_manager[0]["grupo"]
    manager = row_manager[0]["manager"]
    user = row_manager[0]["username"]

    # obtain usernames database
    rows = db.execute("SELECT username FROM users WHERE grupo = :grupo", grupo=group)
    #calculate how many line(users) there are on the rows table
    count_rows = 0
    for n in rows:
        count_rows = count_rows + 1

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        """Perform group's lottery if user is manager"""

        # obtain party information
        gift_value = request.form.get("gift_value")
        date = request.form.get("date")
        local = request.form.get("local")

        # declaring the variables
        orig_gift_value = 0
        orig_date = 0
        orig_local = 0

        # verify if gift_value, local and date already exist in database
        row_party = db.execute("SELECT * FROM party WHERE grupo = :grupo", grupo=group)
        if row_party:
            orig_gift_value = row_party[0]["gift_value"]
            orig_date = row_party[0]["date"]
            orig_local = row_party[0]["local"]

        # if it is the first time party information is been provided, insert on the database
        if orig_gift_value == 0 and  orig_date == 0 and orig_local == 0:
            db.execute("INSERT INTO party(date, gift_value, grupo, local) VALUES(:date, :gift_value, :grupo, :local)",
                        date=date, gift_value=gift_value, grupo = group, local=local)
        # otherwise, update the database
        else:
            if not gift_value:
                gift_value = orig_gift_value
            if not date:
                date = orig_date
            if not local:
                local = orig_local
            db.execute("UPDATE party SET date = :date, gift_value = :gift_value, local = :local WHERE grupo = :grupo",
                        date=date, gift_value=gift_value, grupo = group, local=local)


        # return template
        rows_friends = db.execute("SELECT * FROM friends WHERE username = :username", username=user)
        if rows_friends:
            lottery_text = "already happened"
        else:
            lottery_text = "didn't happen yet"

        return render_template("manager.html", group=group, lottery=lottery_text, num_members=count_rows)


    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        rows_friends = db.execute("SELECT * FROM friends WHERE username = :username", username=user)
        if rows_friends:
            lottery_text = "already happened"
        else:
            lottery_text = "didn't happen yet"

        # direct users to different page's depending if he/she is group's manager
        if manager == 1:
            return render_template("manager.html", group=group, lottery=lottery_text, num_members=count_rows, users=rows)
        else:
            return render_template("manager_read.html", group=group, lottery=lottery_text, num_members=count_rows, users=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("Username and/or password invalids")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure password and confirm password are the same
        if not request.form.get("password") == request.form.get("confirm_password"):
            return apology("The password provided are not the same")

        # ensure user select a group or create a new one
        elif request.form["group"] == "" and request.form["new_group"] == "":
            return apology("You must either create a group or join one")

        elif request.form["group"] != "" and request.form["new_group"] != "":
            return apology("You must either create a group or join one")

        # save the group selected/created
        # create group
        elif request.form["group"] == "" and request.form["new_group"] != "":
            group = request.form.get("new_group")
            manager = "yes"

        # enter a group
        elif request.form["group"] != "" and request.form["new_group"] == "":
            group = request.form.get("group")
            manager = "no"

        # ensure username is unique
        result = db.execute("SELECT username FROM users WHERE username = :username", username=request.form.get("username"))
        if result:
            return apology("Username already in use" "Try a new one")

        # hash passowrd
        hash = pwd_context.hash(request.form.get("password"))

        # insert username, password, email, group and if is manager in the database
        if manager == "yes":
            db.execute("INSERT INTO users(username, hash, email, grupo, manager) VALUES(:username, :hash, :email, :grupo, :manager)",
                        username=request.form.get("username"), hash=hash, email=request.form.get("email"), grupo=group, manager=1)
        else:
            db.execute("INSERT INTO users(username, hash, email, grupo, manager) VALUES(:username, :hash, :email, :grupo, :manager)",
                        username=request.form.get("username"), hash=hash, email=request.form.get("email"), grupo=group, manager=0)

        # now that is registered, let's log in
        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page if user is a regular one or to manager.html if it is the manager
        if manager == "no":
            return redirect(url_for("index"))
        else:
            return redirect(url_for("manager"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        # provide group options
        rows_groups = db.execute("SELECT grupo FROM users GROUP BY  grupo")
        return render_template("register.html", group=rows_groups)

@app.route("/unregister", methods=["GET", "POST"])
@login_required
def unregister():
    """Unregister user."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # obtain manager email
        user = session["username"]
        row_user = db.execute("SELECT * FROM users WHERE username = :username", username=user)
        group = row_user[0]["grupo"]
        row_user_manager = db.execute("SELECT * FROM users WHERE grupo = :grupo AND manager = :manager", grupo=group, manager="1")
        email_manager = row_user_manager[0]["email"]

        # delete user from database
        db.execute("DELETE FROM users WHERE username = :username", username=user)
        db.execute("DELETE FROM wishlist WHERE username = :username", username=user)
        db.execute("DELETE FROM messenger WHERE username = :username", username=user)
        db.execute("DELETE FROM friends WHERE username = :username", username=user)

        # inform group manager to perform new secret santa random assignement
        msg1 = "The user "
        msg2 = " unregistered. Perform a new Secret Santa draw."
        message = msg1+user+msg2
        subject = "Message to Secret Santa Group Manager"
        to = email_manager
        email(message, subject, to)

        """Log user out."""

        # forget any user_id
        session.clear()

        # redirect user to login form
        return redirect(url_for("login"))

    else:
        return render_template("unregister.html")

def email(message, subject, to):

    # use yagmail to send email
    yag = yagmail.SMTP({MY_ADDRESS: 'Papai Noel'}, PASSWORD)
    yag.send(to = to, subject = subject, contents = message)

