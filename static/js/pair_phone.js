const pairButton = document.getElementById("pairPhoneButton");
const message = document.getElementById("phonePairMessage");
const secret = window.HOMECLOUD_PAIR_SECRET;

function showMessage(type, text) {
  message.className = `phone-pair-message ${type}`;
  message.textContent = text;
}

pairButton.addEventListener("click", async () => {
  pairButton.disabled = true;
  pairButton.textContent = "Pairing…";
  message.classList.add("hidden");

  try {
    const response = await fetch("/api/pair/claim", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        secret,
        device_name: "iPhone",
      }),
    });

    const payload = await response.json();

    if (!payload.ok) {
      throw new Error(payload.error || "Pairing failed.");
    }

    showMessage("success", "Paired. Opening your HomeCloud…");
    pairButton.textContent = "Paired";

    setTimeout(() => {
      window.location.href = "/";
    }, 650);
  } catch (error) {
    showMessage("error", error.message || "Pairing failed.");
    pairButton.disabled = false;
    pairButton.textContent = "Try pairing again";
  }
});
