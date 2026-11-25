const snapFile = document.getElementById("snap-file");
const fileBtn = document.getElementById("file-button");
const previewDock = document.getElementById("preview-dock");
const previewContainer = document.getElementById("preview-container");
const caption = document.getElementById("caption");
const previewClose = document.getElementById("preview-close");

fileBtn.addEventListener("click", () => {
  snapFile.click();
});

snapFile.addEventListener("change", () => {
  const currentFile = snapFile.files[0];
  if (!currentFile) return;

  // innerHTML ki jagah DOM API — file name me HTML ho to bhi safe
  const img = document.createElement("img");
  img.id = "preview-snap";
  img.src = URL.createObjectURL(currentFile);
  img.alt = currentFile.name;
  img.className = "object-cover h-full w-full";
  previewContainer.replaceChildren(img);

  caption.textContent = currentFile.name;
  previewDock.style.display = "block";
});

// ✕ button — selected image hata do
if (previewClose) {
  previewClose.addEventListener("click", () => {
    snapFile.value = "";
    previewContainer.replaceChildren();
    caption.textContent = "";
    previewDock.style.display = "none";
  });
}
