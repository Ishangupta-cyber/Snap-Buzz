document.addEventListener("DOMContentLoaded",()=>{

  const forms=document.querySelectorAll('form[action*="/accept-invite/"]');

  forms.forEach(form =>{
    form.addEventListener('submit',(e)=>{

      e.preventDefault();

      const button=form.querySelector('button')
      const url=form.getAttribute('action')

      const csrf_token=form.querySelector('[name=csrfmiddlewaretoken]').value;

      const listItem=form.closest('li')

      fetch(url,{
        method:'POST',
        headers:{
          'X-CSRFToken': csrf_token
        }
      })
      .then(response => response.json())
      .then(data=>{

        if(data.status === "success"){
          listItem.remove()
        }
        else{
          alert(data.message);
        }

      })

    })
  })















})