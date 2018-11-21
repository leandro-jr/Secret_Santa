import os

import requests

from datetime import datetime


from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

channels = {0: "general"}
contacts_list = []
messages_list = []
directs_list = []
message_channel = {}
count = 1
count_msg = 0

@app.route("/")
def index():
    return render_template("index.html", channels=channels, contacts_list=contacts_list)


@app.route('/memento', methods = ['POST'])
def memento():
    # obtain the last channel visited by user from the browser and send
    # jsonnifyed list with messages fro that channel
    remember_channel = request.form.get("remember_channel")
    data = message_channel[remember_channel]
    size = len(data)

    return jsonify({"success": True, "msg": data, "size": size})


@app.route("/display_name")
def display_name():
    return render_template("display_name.html", channels=channels, contacts_list=contacts_list)


@app.route("/messages")
def messages():
    # obtain channel by get and send message list for that channel to html page
    if request.method == 'GET':
        selected_channel = request.args.get('channel')
        if selected_channel:
            message = message_channel[selected_channel]
            return render_template("messages.html", selected_channel=selected_channel, messages=message)
        else:
            return render_template("messages.html", selected_channel='error')


@app.route('/direct', methods = ['GET','POST'])
def direct():
    # obtain contact by get and send selected_contact to html page
    if request.method == 'GET':
        selected_contact = request.args.get('to')
        return render_template("direct.html", selected_contact=selected_contact)

    # Try to find direct messages on message_channel using key=display_name + '_' + selected_contact
    # if key not found use key=selected_contact + '_' + display_name
    if request.method == 'POST':
        display_name = request.form.get("display_name")
        selected_contact = request.form.get("selected_contact")
        print(display_name)
        print(selected_contact)

        contact_key = display_name + '_' + selected_contact
        if not contact_key in message_channel.keys():
            inverted_contact_key = selected_contact + '_' + display_name
            messages = message_channel[inverted_contact_key]
            size = len(messages)
        else:
            messages= message_channel[contact_key]
            size = len(messages)

        return jsonify({"success": True, "msg": messages, "size": size, "selected_contact": selected_contact})

@socketio.on("submit channel")
def channel(data):
    new_channel = data["new_channel"]
    global count

    # verify if channel was already created and emit the channels
    channel_repeated = 1
    if new_channel in channels.values():
        for value in channels.values():
            if value == new_channel:
                channel_repeated = 0
                new_channel = value
                emit("channels", {"new_channel": value, "channel_repeated": channel_repeated}, broadcast=True)
    else:
        channels[count] = new_channel
        count += 1
        messages_list = []
        message_channel[new_channel] = messages_list
        emit("channels", {"new_channel": new_channel, "channel_repeated": channel_repeated}, broadcast=True)


@socketio.on("submit contact")
def contact(data):
    new_contact = data["new_contact"]

    # add first user to contacts_list
    if len(contacts_list) == 0:
        contacts_list.append(new_contact)
        emit("contacts", {"new_contact": new_contact}, broadcast=True)

   # starting from second user, create a pair user_new_contact to be the keys
   # for the dict where the direct messages will be stored
    else:
        for user in contacts_list:
            new_key = user + "_" + new_contact
            directs_list = []
            message_channel[new_key] = directs_list

        contacts_list.append(new_contact)
        emit("contacts", {"new_contact": new_contact}, broadcast=True)


@socketio.on("submit message")
def channel(data):
    # add time to the message
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_message = time + ", " + data["new_message"]
    selected_channel = data["selected_channel"]
    author = data["author"]

    # retrieve channels's list of messages and append new message
    messages_list = message_channel[selected_channel]
    messages_list.append(new_message)

    # erase earlist message if list size is bigger the 100 messages
    if len(messages_list) >= 101:
        messages_list.pop(0)

    # update dictionary with message list updated and emit to users
    message_channel[selected_channel] = messages_list
    emit("messages", {"new_message": new_message, 'author': author, 'selected_channel': selected_channel}, broadcast=True)

@socketio.on("submit direct")
def direct(data):
    # add time to the message
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_message = time + ", " + data["new_message"]
    selected_contact = data["selected_contact"]
    author = data["author"]

    # creat contact_key
    contact_key = selected_contact + "_" + author

    # add direct message to message_channel. Try to add using key=selected_contact + "_" + author
    # if key not found use key=author + "_" + selected_contact
    if not contact_key in message_channel.keys():
        inverted_contact_key = author + "_" + selected_contact
        directs_list = message_channel[inverted_contact_key]
        directs_list.append(new_message)
        # erase earlist message if list size is bigger the 100 messages
        if len(directs_list) >= 101:
            directs_list.pop(0)

        message_channel[inverted_contact_key] = directs_list
        emit("messages", {"new_message": new_message, 'author': author, 'selected_contact': selected_contact}, broadcast=True)

    elif contact_key in message_channel.keys():
        directs_list = message_channel[contact_key]
        directs_list.append(new_message)
        # erase earlist message if list size is bigger the 100 messages
        if len(directs_list) >= 101:
            directs_list.pop(0)

        message_channel[contact_key] = directs_list
        emit("messages", {"new_message": new_message, 'author': author, 'selected_contact': selected_contact}, broadcast=True)


@socketio.on("delete msg")
def delete_msg(data):
    # delete message from the channel messages
    selection = data["selection"]
    selected_channel = data["selected_channel"]
    message_delete_list = message_channel[selected_channel][:]
    if selection in message_delete_list:
        message_delete_list.remove(selection)
        message_channel[selected_channel] = message_delete_list[:]
    emit("delete msg io", broadcast=True)


@socketio.on("delete direct")
def delete_direct(data):
    # delete direct message from the channel messages
    selection = data["selection"]
    selected_contact = data["selected_contact"]
    display_name = data["display_name"]

    contact_key = display_name + '_' + selected_contact
    if not contact_key in message_channel.keys():
        inverted_contact_key = selected_contact + '_' + display_name
        directs_delete_list = message_channel[inverted_contact_key]
    else:
        directs_delete_list = message_channel[contact_key]

    if selection in directs_delete_list:
        directs_delete_list.remove(selection)
    emit("delete msg io", {'delete_msg': selection}, broadcast=True)
