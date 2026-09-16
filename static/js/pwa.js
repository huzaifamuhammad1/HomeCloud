(function () {
  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  document.documentElement.classList.toggle("standalone-mode", isStandalone);

  const installChip = document.getElementById("installChip");
  if (installChip && isStandalone) {
    installChip.classList.add("hidden");
  }

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
      try {
        await navigator.serviceWorker.register("/service-worker.js", { scope: "/" });
        document.documentElement.dataset.serviceWorker = "active";
      } catch (_error) {
        // Normal on the current local-IP HTTP stage.
        // Registration will work automatically once HomeCloud is on HTTPS.
        document.documentElement.dataset.serviceWorker = "unavailable";
      }
    });
  } else {
    document.documentElement.dataset.serviceWorker = "unsupported";
  }
})();
