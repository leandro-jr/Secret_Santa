# Project 2

Web Programming with Python and JavaScript

On Index, the user must sign in. When the user does that, it is saved on browser local storage as display_name and Socket.IO is used to comunicate with Flask.
User is added to contact_list, and starting from second user a key Old_User_NewUser is used as key for the dictionary that will store the direct messages exhanged between users.
Socket.IO is used to send the new contacts for other users.
The contacts created are added to the html page with a link "/direct?to=contact"

After entering a new channel, Socket.IO is used  to send the channel to Flask (where it is used as key for dictionary message_channel that will store the messages) and the channel is
also send to users to update their html pages.
The channel created are added to the html page with a link "/messages?channel=channel"

When a user click on channel link, messages.html is loaded with previous messages(if any). Channel is saved to local storage as  last_channel.
New messages are submited using Socket.IO to Flask where they are saved on the dictionary and send to all users on the channel. If the user was the writter of the message a delete button is also added to the message.

If user closes the browser and return, Index.js will look for last_channel on local storage. If found, it will make a POST request to Flask memento sending JSON data with the last_channel. 
Memento will return a JSON with the message_channel dictionary for the specific channel.

When a user click on list of contacts link, direct.html is loaded. Direct.js will make a POST request to Flask memento sending JSON data with display_name and the contact. On application.py in direct it will look for the key of 
the message_channel dictionary "display_name" + "_" + "contact" or vice-versa. Once messages are found, they are sent as JSON for the specific users.
New messages are submited using Socket.IO to Flask where they are saved on the dictionary and send to users on the direct messages pair. If the user was the writter of the message a delete button is also added to the message.