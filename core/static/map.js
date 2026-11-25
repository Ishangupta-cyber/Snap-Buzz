// 1. Map ko chalu (Initialize) karna.
var map = L.map('map', { zoomControl: false }).setView([20.5937, 78.9629], 5);

// 2. Map ke "Tiles" mangwana
// OSM ki usage policy: attribution dikhana zaroori hai, aur single host use karo ({s} subdomains deprecated)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);


window.friendsData.forEach(friend => {
    let customIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<img src="${friend.avatar}" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid white;">`,
        iconSize: [40, 40]
    });

    let marker = L.marker([friend.lat, friend.lng], { icon: customIcon }).addTo(map);
    marker.bindPopup(`<b>${friend.username}</b>`);
});


function sendLocationToServer(lat, lng) {
    fetch("/update-location/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.csrfToken
        },
        body: JSON.stringify({ lat: lat, lng: lng })
    })
    .then(res => res.json())
    .then(data => console.log("Server ka jawab:", data));
}



document.getElementById("locate-me-btn").addEventListener("click", function() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                map.flyTo([lat, lng], 14);

                sendLocationToServer(lat, lng);
            },
            function(error) { alert("Please allow location access!"); },
            { enableHighAccuracy: true }
        );
    }
});