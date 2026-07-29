
document.addEventListener("DOMContentLoaded", () => {
    const snapTriggers = document.querySelectorAll('.snap-trigger');
    const snapModal = document.getElementById('snap-modal');
    const snapModalImage = document.getElementById('snap-modal-image');
    
    // CSRF Token fetch karne ke liye (kyunki humein POST request karni hai)
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    snapTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const snapId = this.getAttribute('data-snap-id');
            const snapUrl = this.getAttribute('data-snap-url');
            
          
            snapModalImage.src = snapUrl;
            snapModal.showModal();
            
            
            fetch(`/mark-snap-opened/${snapId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === "success") {
                  

                    this.classList.remove('snap-trigger', 'cursor-pointer', 'text-slate-100', 'hover:text-white');
                    this.classList.add('text-slate-400');
                    
                    const icon = this.querySelector('.snap-icon');
                    icon.classList.remove('fa-solid', 'drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]');
                    icon.classList.add('fa-regular');
                    
                    const text = this.querySelector('.snap-text');
                    text.textContent = 'Opened';
                    text.classList.remove('font-bold');
                    text.classList.add('font-semibold');
                    
                    // Button ke onClick events ko kill karne ka tareeka (clone karke replace)
                    const clone = this.cloneNode(true);
                    this.parentNode.replaceChild(clone, this);
                }
            })
            .catch(err => console.error(err));
        });
    });
});
