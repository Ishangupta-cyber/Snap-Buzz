document.addEventListener("DOMContentLoaded", () => {
    const chatbox = document.getElementById("chat-box");
    const chatInner = chatbox.querySelector('.min-h-full');
    
    if (chatbox){
        chatbox.scrollTop = chatbox.scrollHeight;   
    }

    // Config passed from Django template
    const { friendId, currentUserId, currentUsername, friendUsername, sendUrl } = window.chatConfig;
    
    // 1. Connection shuru karna
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const chatSocket = new WebSocket(wsScheme + '://' + window.location.host + '/ws/chat/' + friendId + '/');

    // 2. JAB NAYA MESSAGE AAYEGA (Aapka ya dost ka)
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);

        if (data.type==="snap_opened"){
            const snapDiv=document.querySelector(`[data-snap-id="${data.message_id}"]`)
             if (snapDiv) {
            snapDiv.outerHTML = `
                <div class="flex items-center gap-2 mb-2 px-1 text-slate-300">
                    <i class="fa-regular fa-square text-red-500 text-lg"></i>
                    <span class="font-semibold text-sm">Opened</span>
                </div>`;
        }
            return;
        }


        const isMe = (data.sender_id === currentUserId);
        
        const alignment = isMe ? 'chat-end' : 'chat-start';
        const bubbleBg = isMe ? 'bg-purple-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.2)]' : 'bg-slate-800 text-slate-200 border border-slate-700 shadow-md';
        const senderName = isMe ? currentUsername : friendUsername;
        let bubbleContent = '';
                if (data.image_url) {
            // Agar image bheji gayi hai
            if (isMe) {
                bubbleContent = `
                    <div class="flex items-center gap-2 mb-2 px-1 text-slate-100" data-snap-id="${data.message_id}">
                        <i class="fa-solid fa-square text-red-500 text-lg"></i>
                        <span class="font-semibold text-sm">Delivered</span>
                    </div>`;
            } else {
                bubbleContent = `
                    <div class="snap-trigger cursor-pointer flex items-center gap-2 mb-2 px-1 text-slate-100 hover:text-white transition-colors" 
                        data-snap-id="${data.message_id}" 
                        data-snap-url="${data.image_url}"
                        onclick="window.location.reload();"> <!-- Temporary click handler for new snap -->
                        <i class="fa-solid fa-square text-red-500 text-lg snap-icon drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]"></i>
                        <span class="font-bold text-sm snap-text">New Snap</span>
                    </div>`;
            }
        }
        
        // Text bhi lagao agar sath me text bheja hai (ya sirf text message hai)
        if (data.message) {
            bubbleContent += `<p>${data.message}</p>`;
        }
        
        
        const html = `
        <div class="chat ${alignment} mb-4">
            <div class="chat-header flex items-center gap-2 mb-1">
                <span class="font-bold text-slate-200">${senderName}</span>
                <time class="text-xs font-medium text-slate-500">Just now</time>
            </div>
            <div class="chat-bubble ${bubbleBg} break-words leading-relaxed">
                ${bubbleContent}
            </div>
            ${isMe ? '<div class="chat-footer text-xs font-semibold text-slate-500 mt-1">Delivered</div>' : ''}
        </div>
        `;
        
        chatInner.insertAdjacentHTML('beforeend', html);
        chatbox.scrollTop = chatbox.scrollHeight; 
    };

    // 3. JAB HUM FORM SUBMIT KAREIN
    const form = document.querySelector(`form[action='${sendUrl}']`);
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault()
            const fileInput = document.getElementById('snap-file');
            const textInput = document.querySelector('input[name="content"]');
            const message = textInput.value;
            
            if (fileInput && fileInput.files.length > 0) {
                const formData=new FormData(form)
            
            fetch(sendUrl,{
                method:"POST",
                body:formData
            })
            .then(response=>response.json())
            .then(data=>{
                    form.reset();
                    const dock = document.getElementById('preview-dock');
                    if(dock) dock.style.display = 'none';
                })
                .catch(err => console.error("Upload Error:", err));
            }
        

            else if (message.trim() !== "") {
                // Text ko bhi WebSocket ke bajaye AJAX (fetch) se bhejo
                // Taaki Django view me jaye, aur Conversation/Streak update ho sake
                const formData = new FormData(form);
                fetch(sendUrl, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    textInput.value = ''; // Box khali kar do
                })
                .catch(err => console.error("Message Error:", err));
            }
        });
    }
});
