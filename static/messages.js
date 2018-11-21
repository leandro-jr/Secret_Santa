document.addEventListener('DOMContentLoaded', () => {
      // Connect to websocket
      var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

      // retrieve display_name and add last channel to local storage
      var display_name = localStorage.getItem('display_name');
      var last_channel = document.querySelector('#selected_channel').dataset.selected_channel;
      localStorage.setItem('last_channel', last_channel);
      document.querySelector('#canal').innerHTML = '#' + localStorage.getItem('last_channel');

      // When connected, configure form
      socket.on('connect', () => {

        // create new message and emit to users
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
});
