document.getElementById("loginForm").addEventListener("submit", function(e) {
  e.preventDefault(); // evita recargar la página

  const user = document.getElementById("username").value;
  const pass = document.getElementById("password").value;
  const message = document.getElementById("message");

  // Usuario y contraseña de prueba
  const userTest = "admin";
  const passTest = "1234";

  if (user === userTest && pass === passTest) {
    message.style.color = "green";
    message.textContent = "✅ Login exitoso, bienvenido " + user + "!";
  } else {
    message.style.color = "red";
    message.textContent = "❌ Usuario o contraseña incorrectos";
  }
});
