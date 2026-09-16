(async function () {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    const status = await response.json();

    if (status.stage !== 6) return;

    const eyebrow = document.querySelector("#homeSection .eyebrow");
    const headline = document.querySelector("#homeSection h1");
    const copy = document.querySelector("#homeSection .hero-copy p");
    const footerParts = document.querySelectorAll("footer span");

    if (eyebrow) eyebrow.textContent = "PRIVATE HTTPS · ANYWHERE";
    if (headline) headline.innerHTML = "Your Mac,<br>from anywhere.";
    if (copy) {
      copy.textContent =
        "HomeCloud now travels through your private Tailscale network, with HTTPS in the browser and your paired-device lock on top.";
    }

    if (footerParts.length) {
      footerParts[0].textContent = "HomeCloud · Stage 6";
      if (footerParts.length >= 3) footerParts[2].textContent = "Private remote access";
    }

    if (status.https) {
      const pill = document.createElement("div");
      pill.className = "remote-secure-badge";
      pill.textContent = "HTTPS · Tailscale";
      const card = document.querySelector(".security-card");
      if (card) card.appendChild(pill);
    }
  } catch (_error) {}
})();
