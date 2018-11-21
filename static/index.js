document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // verify if display name is not storaged
    if (!localStorage.getItem('display_name')) {
        socket.on('connect', () => {

            document.querySelector('#new-name').onsubmit = () => {

                // place display name on storage and add to html
                const display_name = document.querySelector('#name').value;
                localStorage.setItem('display_name', display_name);
                document.querySelector('#display_name').innerHTML = '&#9733' + ' Hello, ' + localStorage.getItem('display_name');
                // emit contact to the other users
                socket.emit('submit contact', {'new_contact': localStorage.getItem('display_name')});
                // Clear and disable input field
                document.getElementById("new-name" ).style.display = "none";

                // Stop form from submitting
                return false;
            };

            // create new channel
            document.querySelector('#new-channel').onsubmit = () => {
                  let new_channel = document.querySelector('#channel_creation').value;
                  localStorage.setItem('new_channel', new_channel);
                  socket.emit('submit channel', {'new_channel': new_channel});

                  // Clear input field
                  document.querySelector('#channel_creation').value = '';

                  // Stop form from submitting
                  return false;
             };
        });
    }

    else {
        // if display name was already storaged, add to html and disable form
        document.querySelector('#display_name').innerHTML = '&#9786' + ' Hello, ' + localStorage.getItem('display_name');
        document.getElementById("new-name" ).style.display = "none";

        var display_name = localStorage.getItem('display_name');

        // When connected, configure form
        socket.on('connect', () => {

          // create new channel
          document.querySelector('#new-channel').onsubmit = () => {
                let new_channel = document.querySelector('#channel_creation').value;
                localStorage.setItem('new_channel', new_channel);
                socket.emit('submit channel', {'new_channel': new_channel});

                // Clear input field
                document.querySelector('#channel_creation').value = '';

                // Stop form from submitting
                return false;
           };

           // emit new message to other users
           document.querySelector('#new-message').onsubmit = () => {
                 // add display_name to the message
                 let new_message = display_name + ': ' +  document.querySelector('#message').value;
                 socket.emit('submit message', {'new_message': new_message, 'author': display_name, 'selected_channel': localStorage.getItem('last_channel')});

                 // Clear input field
                 document.querySelector('#message').value = '';

                 // Stop form from submitting
                 return false;
            };
          });


    // if the user is returning, display the messages from last channel he/she used
    if (localStorage.getItem('last_channel')) {
          document.querySelector('#canal').innerHTML = '#' + localStorage.getItem('last_channel');

          // Initialize new request
          const request = new XMLHttpRequest();
          var remember_channel = localStorage.getItem('last_channel');
          request.open('POST', '/memento');

          // Callback function for when request completes
          request.onload = () => {

                // Extract JSON data from request
                const data = JSON.parse(request.responseText);

                // iterate over data.msg and add li item to the page
                if (data.success) {
                    for (var i = 0; i < `${data.size}`; i++) {
                        const li = document.createElement('li');
                        li.innerHTML = `${data.msg[i]}`;
                        document.querySelector('#messages').append(li);
                    }

                    // update messages on the fly
                    socket.on('messages', data => {
                        // Create new item if data.selected_channel is the same storaged by the browser
                        if (`${data.selected_channel}` == localStorage.getItem('last_channel')) {
                          const li = document.createElement('li');
                          li.innerHTML = ` ${data.new_message} `;

                          // if message was created by the user itself add data attribute and delete button
                          if (`${data.author}` == display_name) {
                              const btn = document.createElement("BUTTON");
                              btn.setAttribute('data-delete', `${data.new_message}`);
                              const t = document.createTextNode("Delete");
                              btn.appendChild(t);

                              document.querySelector('#messages').append(li);
                              li.appendChild(btn);
                          }
                          // else just add message to ul
                          else {
                              document.querySelector('#messages').append(li);
                          }

                          // send button.dataset.delete message to be deleted from the dictinary
                          document.querySelectorAll('button').forEach(button => {
                              button.onclick = () => {
                                  const selection = button.dataset.delete;
                                  socket.emit('delete msg', {'selection': selection, 'selected_channel': localStorage.getItem('last_channel')});
                              };
                          });
                        }
                    });

                    // refresh page once message was deleted
                    socket.on('delete msg io', data => {
                            location.reload();
                    });






                }
                else {
                    document.querySelector('#messages').innerHTML = 'There was an error.';
                }
          }

          // Add data to send with request
          const data = new FormData();
          data.append('remember_channel', remember_channel);

          // Send request
          request.send(data);
          return false;
    }
    else {
      document.querySelector('#display_name').innerHTML = 'Hello, ' + localStorage.getItem('display_name');
    }
    }

    // Create new li item with link for new_contact if the new_contact is not the user itself
    socket.on('contacts', data => {
        if (`${data.new_contact}` != localStorage.getItem('display_name')) {
            var li = document.createElement('li');
            var a = document.createElement('a');
            var ulist = document.querySelector('#contacts');
            new_contact = `${data.new_contact}`;
            a.textContent = `${data.new_contact}`;
            a.setAttribute('href', "/direct?to=" + new_contact);
            li.appendChild(a);
            ulist.appendChild(li);
        }
      });

      socket.on('channels', data => {
          // Create new item with link for list if channel is new_channel and it was created by the browser
          if (`${data.new_channel}` == localStorage.getItem('new_channel') && `${data.channel_repeated}` == 1 ) {
          var li = document.createElement('li');
          var a = document.createElement('a');
          var ulist = document.querySelector('#channels');
          channel_added = `${data.new_channel}`;
          a.textContent = `${data.new_channel}`;
          a.setAttribute('href', "/messages?channel=" + channel_added);
          li.appendChild(a);
          ulist.appendChild(li);
          }
          // Create new item with link for list if channel is new_channel and it was created by other browser
          else if (`${data.new_channel}` != localStorage.getItem('new_channel') && `${data.channel_repeated}` == 1 ) {
            var li = document.createElement('li');
            var a = document.createElement('a');
            var ulist = document.querySelector('#channels');
            channel_added = `${data.new_channel}`;
            a.textContent = `${data.new_channel}`;
            a.setAttribute('href', "/messages?channel=" + channel_added);
            li.appendChild(a);
            ulist.appendChild(li);
          }
          // Send alert if it channel is not a new_channel and it was created by the browser
          else if (`${data.new_channel}` == localStorage.getItem('new_channel') && `${data.channel_repeated}` == 0 ) {
            alert('Channel already created');
          }
        });
});
