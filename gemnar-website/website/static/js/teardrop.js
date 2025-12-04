document.addEventListener("click", function (e) {
  if (e.target.classList.contains("error-bg")) {
    let teardrop = document.createElement("div");
    teardrop.classList.add("teardrop");
    teardrop.style.left = e.pageX + "px";
    teardrop.style.top = e.pageY + "px";
    document.body.appendChild(teardrop);

    setTimeout(() => {
      teardrop.remove();
    }, 1000); // Corresponds to animation duration
  }
});
