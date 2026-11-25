// HTML special characters escape karo — XSS se bachne ke liye.
// Server se aaya koi bhi text innerHTML me daalne se pehle isse guzarna chahiye.
function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

document.addEventListener("DOMContentLoaded", () => {
    const chatbox = document.getElementById("chat-box");
    if (!chatbox) return;
    const chatInner = chatbox.querySelector(".min-h-full");
    chatbox.scrollTop = chatbox.scrollHeight;

    // Config passed from Django template
    const { friendId, currentUserId, currentUsername, friendUsername, sendUrl } = window.chatConfig;

    // 1. Connection shuru karna
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const chatSocket = new WebSocket(`${wsScheme}://${window.location.host}/ws/chat/${friendId}/`);

    // 2. JAB NAYA MESSAGE AAYEGA (Aapka ya dost ka)
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.type === "snap_opened") {
            window.showSnapOpened(data.message_id);
            return;
        }

        const isMe = data.sender_id === currentUserId;
        const messageId = escapeHtml(data.message_id);

        const alignment = isMe ? "chat-end" : "chat-start";
        const bubbleBg = isMe
            ? "bg-purple-600 text-white shadow-[0_0_15px_rgba(168,85,247,0.2)]"
            : "bg-slate-800 text-slate-200 border border-slate-700 shadow-md";
        const senderName = escapeHtml(isMe ? currentUsername : friendUsername);
        let bubbleContent = "";

        if (data.image_url) {
            if (isMe) {
                bubbleContent = `
                    <div class="flex items-center gap-2 mb-2 px-1 text-slate-100" data-snap-id="${messageId}">
                        <i class="fa-solid fa-square text-red-500 text-lg"></i>
                        <span class="font-semibold text-sm">Delivered</span>
                    </div>`;
            } else {
                // Click chat_snap_viewer.js ke delegated listener se handle hota hai — koi reload nahi
                bubbleContent = `
                    <div class="snap-trigger cursor-pointer flex items-center gap-2 mb-2 px-1 text-slate-100 hover:text-white transition-colors"
                        data-snap-id="${messageId}"
                        data-snap-url="${escapeHtml(data.image_url)}">
                        <i class="fa-solid fa-square text-red-500 text-lg snap-icon drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]"></i>
                        <span class="font-bold text-sm snap-text">New Snap</span>
                    </div>`;
            }
        }

        if (data.message) {
            bubbleContent += `<p>${escapeHtml(data.message)}</p>`;
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
            ${isMe ? '<div class="chat-footer text-xs font-semibold text-slate-500 mt-1">Delivered</div>' : ""}
        </div>`;

        chatInner.insertAdjacentHTML("beforeend", html);
        chatbox.scrollTop = chatbox.scrollHeight;
    };

    // 3. JAB HUM FORM SUBMIT KAREIN — text aur image dono HTTP view se jaate hain
    // (taaki validation, Conversation aur Streak update ho sake). Page refresh nahi hota.
    const form = document.querySelector(`form[action='${sendUrl}']`);
    if (!form) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const fileInput = document.getElementById("snap-file");
        const textInput = form.querySelector('input[name="content"]');
        const hasFile = fileInput && fileInput.files.length > 0;

        if (!hasFile && textInput.value.trim() === "") return;

        fetch(sendUrl, { method: "POST", body: new FormData(form) })
            .then((response) => response.json())
            .then((data) => {
                if (data.status !== "success") {
                    alert(data.message || "Message send nahi hua.");
                    return;
                }
                form.reset();
                const dock = document.getElementById("preview-dock");
                if (dock) dock.style.display = "none";
            })
            .catch((err) => console.error("Send Error:", err));
    });
});
