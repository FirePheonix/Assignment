(function () {
  let isRightFoot = true;
  let throttleTimer = null;
  const THROTTLE_DELAY = 120; // ms

  document.addEventListener("mousemove", function (e) {
    if (throttleTimer) {
      return;
    }

    throttleTimer = setTimeout(() => {
      const footstep = document.createElement("div");
      footstep.classList.add("footstep");

      footstep.style.left = e.pageX + "px";
      footstep.style.top = e.pageY + "px";

      const rotation = isRightFoot ? 20 : -20;
      const offsetX = isRightFoot ? 8 : -8;
      footstep.style.transform = `translateX(${offsetX}px) rotate(${rotation}deg)`;

      document.body.appendChild(footstep);

      isRightFoot = !isRightFoot;

      setTimeout(() => {
        footstep.remove();
      }, 1500);

      throttleTimer = null;
    }, THROTTLE_DELAY);
  });
})();
