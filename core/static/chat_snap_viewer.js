// Snap viewer: click "New Snap" -> image modal me khulta hai, server pe opened mark hota hai.
// Event delegation (#chat-box pe ek hi listener) use kiya hai, isliye WebSocket se
// live aaye naye snaps bhi bina page refresh ke khul jaate hain.

const OPENED_SNAP_HTML = `
    <div class="flex items-center gap-2 mb-2 px-1 text-slate-300">
        <i class="fa-regular fa-square text-red-500 text-lg"></i>
        <span class="font-semibold text-sm">Opened</span>
    </div>`;

// Global helper — chat_websocket.js bhi isko use karta hai jab "snap_opened" event aata hai
window.showSnapOpened = function (messageId) {
    const el = document.querySelector(`[data-snap-id="${CSS.escape(String(messageId))}"]`);
    if (el) el.outerHTML = OPENED_SNAP_HTML;
};

document.addEventListener("DOMContentLoaded", () => {
    const chatbox = document.getElementById("chat-box");
    const snapModal = document.getElementById("snap-modal");
    const snapModalImage = document.getElementById("snap-modal-image");
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    if (!chatbox || !snapModal) return;

    // Modal band hote hi image hata do — one-time view
    snapModal.addEventListener("close", () => {
        snapModalImage.removeAttribute("src");
    });

    chatbox.addEventListener("click", (e) => {
        const trigger = e.target.closest(".snap-trigger");
        if (!trigger) return;

        const snapId = trigger.dataset.snapId;
        const snapUrl = trigger.dataset.snapUrl;

        // Double-click se dobara na khule
        trigger.classList.remove("snap-trigger");

        snapModalImage.src = snapUrl;
        snapModal.showModal();

        fetch(`/mark-snap-opened/${snapId}`, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.status === "success" || data.status === "already_opened") {
                    window.showSnapOpened(snapId);
                }
            })
            .catch((err) => console.error(err));
    });
});
