document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[action*="/send-invite/"]');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); 
            
            const button = form.querySelector('button');
            const url = form.getAttribute('action');

            const csrf_token = form.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf_token
                }
            })
            .then(response => response.json())
            .then(data => {

                if (data.status === 'success') {

                    button.className = "btn btn-sm border-none outline-none rounded-full bg-yellow-300 text-gray-800";
                    button.innerHTML = '<i class="fa-solid fa-clock"></i> Pending';
                    
                    button.disabled = true; 
                } else {

                    alert("Error: " + data.message);
                }
            })
            .catch(error => {
                console.error("Something went wrong", error);
            });
        });
    });
});
