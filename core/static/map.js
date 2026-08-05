


function sendLocationToServer(lat,lng){
  console.log("location is sending....")
  fetch("/update-location/",{
    method:"POST",
    headers:{
      "Content-Type":"application/json",
       "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ lat: lat, lng: lng }) // Data ko JSON (text) me badalna
  })
   .then(response => response.json()) // Server ka jawab padhna
    .then(data => {
        console.log("Server ka jawab:", data);
    })
    .catch(error => {
        console.error("Bhejne mein error aayi:", error);
    });
}




document.getElementById("locate-me-btn").addEventListener
("click",function(){

  if ("geolocation" in navigator ){

    navigator.geolocation.getCurrentPosition(

      function(position){
        const lat=position.coords.latitude
        const lng=position.coords.longitude
        alert("location accessed")

      },
      function(error){
        alert("Please Allow location permission")
      },
      { enableHighAccuracy: true }
    )
  }

  else{
    alert("your browser dont support gps")
  }
})