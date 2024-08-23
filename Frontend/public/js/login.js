
const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');
const LoginMessage = document.getElementById('LoginMessage');
const RegisterMessage = document.getElementById('RegisterMessage');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
    LoginMessage.textContent = 'Enter your personal details to use all of site features';
})




loginForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const username = formData.get('username');
    const password = formData.get('password');

    // Verificar que ambos campos estén completos antes de continuar
    if (!username && !password) {
      LoginMessage.textContent = 'Please enter both username and password.';
      return;
    } else if (!username) {
      LoginMessage.textContent = 'Please enter username.';
      return;
    } else if (!password) {
      LoginMessage.textContent = 'Please enter password.';
      return;
    }

    fetch('/login', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        console.log(data);
        console.log(data.success);
        window.location.href = data.redirect;
      } else {
        LoginMessage.textContent = data.error || 'An error occurred. Please try again.';
      }
    })
    .catch(error => {
      console.error('Error en la solicitud:', error);
      LoginMessage.textContent = 'An error occurred. Please try again.';
    });
});
  
RegisterForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(RegisterForm);
  const name = formData.get('name');
  const username = formData.get('username');
  const password = formData.get('password');

  // Verificar que ambos campos estén completos antes de continuar
  if (!username && !password && !name) {
    LoginMessage.textContent = 'Please enter all Data.';
    return;
  }

  fetch('/register', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (response.ok) {
      container.classList.remove("active");
      LoginMessage.textContent = 'Enter your new user details to use all of site features';
      RegisterMessage.textContent = 'Enter your personal details to use all of site features';
    } else if(response.status === 401) {
      console.error(response.statusText)
      RegisterMessage.textContent = 'Invalid credentials. Please try again.';
    } else if(response.status === 422) {
      console.error(response.statusText)
      RegisterMessage.textContent = 'You did not enter complete information. Please try again.';
    }
    else{
      console.error(response.statusText)
    }
  })
  .catch(error => {
    console.error('Error en la solicitud:', error);
  });
});