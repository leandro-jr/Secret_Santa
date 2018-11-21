document.addEventListener('DOMContentLoaded', () => {

      // Connect to websocket
      var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

      display_name = localStorage.getItem('display_name');

      // obtain selected_contact from the html page place on local storage
      var selected_contact = document.querySelector('#selected_contact').dataset.selected_contact;
      localStorage.setItem('selected_contact', selected_contact);
      

      // When connected, configure form
      socket.on('connect', () => {

        // create new direct message
        document.querySelector('#new-message').onsubmit = () => {
              // add display_name to the message
              let new_message = display_name + ': ' +  document.querySelector('#message').value;
              socket.emit('submit direct', {'new_message': new_message, 'author': display_name, 'selected_contact': selected_contact});

              // Clear input field
              document.querySelector('#message').value = '';

              // Stop form from submitting
              return false;
         };
        });

      // update direct messages on the fly
      socket.on('messages', data => {
          // Create new item if it is browser's sender OR if browser is the destiny AND sender is equal browser destiny
          if (`${data.author}` == display_name || (`${data.selected_contact}` == display_name && `${data.author}` == selected_contact)) {
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
                    socket.emit('delete direct', {'selection': selection, 'selected_contact': selected_contact, 'display_name': display_name});
                };
            });
          }
      });

      // refresh page once message was deleted
      socket.on('delete msg io', data => {
              location.reload();
      });

      // Initialize new request
      const request = new XMLHttpRequest();
      request.open('POST', '/direct');

        // Callback function for when request completes
        request.onload = () => {

              // Extract JSON data from request
              const data = JSON.parse(request.responseText);

              /// iterate over data.msg and add li item to the page
              if (data.success) {
                  for (var i = 0; i < `${data.size}`; i++) {
                      // var contents = `${data.msg[i]}`
                      const li = document.createElement('li');
                      li.innerHTML = `${data.msg[i]}`;
                      document.querySelector('#messages').append(li);
                  }
              }
              else {
                  document.querySelector('#messages').innerHTML = 'There was an error.';
              }
            }

      // Add data to send with request
      const data = new FormData();
      data.append('display_name', display_name)
      data.append('selected_contact', selected_contact);

      // Send request
      request.send(data);
      return false;
});
