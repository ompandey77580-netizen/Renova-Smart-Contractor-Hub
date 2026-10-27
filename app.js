/* static/app.js - client-side validation helpers */
function togglePwd() {
  const f = document.getElementById("pwd");
  if (f) f.type = f.type === "password" ? "text" : "password";
}

// number+range guard used by every money field
document.addEventListener("input", (e) => {
  if (e.target.matches("input[type=number]")) {
    const v = parseFloat(e.target.value);
    if (e.target.min && v < parseFloat(e.target.min)) {
      e.target.setCustomValidity("Value is below the minimum allowed.");
    } else {
      e.target.setCustomValidity("");
    }
  }
});

// simple search debounce for the project list
let t;
function liveSearch(box, url) {
  clearTimeout(t);
  t = setTimeout(() => {
    const q = encodeURIComponent(box.value);
    fetch(url + "?q=" + q)
      .then(r => r.text())
      .then(html => {
        document.getElementById("project-list").innerHTML = html;
      });
  }, 350);
}
