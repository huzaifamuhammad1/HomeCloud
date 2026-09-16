const pairingId = window.HOMECLOUD_PAIRING_ID;
const pairingStatus = document.getElementById("pairingStatus");
const pairingStatusText = document.getElementById("pairingStatusText");
const devicesList = document.getElementById("devicesList");
const deviceCount = document.getElementById("deviceCount");

function formatWhen(value) {
  if (!value) return "Never";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

async function loadDevices() {
  const response = await fetch("/api/admin/devices", { cache: "no-store" });
  const payload = await response.json();
  const active = payload.devices.filter((device) => !device.revoked_at);

  deviceCount.textContent = `${active.length} active`;

  if (!payload.devices.length) {
    devicesList.innerHTML = `
      <div class="no-devices">
        No phones paired yet. Scan the QR above to add the first one.
      </div>
    `;
    return;
  }

  devicesList.innerHTML = payload.devices.map((device) => `
    <div class="device-row ${device.revoked_at ? "revoked" : ""}">
      <div>
        <strong>${device.name}</strong>
        <span>
          ${device.revoked_at
            ? `Revoked ${formatWhen(device.revoked_at)}`
            : `Last seen ${formatWhen(device.last_seen_at)}`
          }
        </span>
      </div>
      ${
        device.revoked_at
          ? `<span class="revoked-label">Revoked</span>`
          : `<button type="button" data-revoke="${device.id}">Revoke</button>`
      }
    </div>
  `).join("");

  devicesList.querySelectorAll("[data-revoke]").forEach((button) => {
    button.addEventListener("click", async () => {
      const confirmed = window.confirm(
        "Revoke this device? It will immediately lose HomeCloud file access."
      );
      if (!confirmed) return;

      await fetch(`/api/admin/devices/${encodeURIComponent(button.dataset.revoke)}`, {
        method: "DELETE",
      });
      await loadDevices();
    });
  });
}

async function pollPairing() {
  try {
    const response = await fetch(
      `/api/admin/pairing/${encodeURIComponent(pairingId)}/status`,
      { cache: "no-store" }
    );
    const payload = await response.json();

    if (payload.status === "paired") {
      pairingStatus.classList.remove("waiting");
      pairingStatus.classList.add("success");
      pairingStatusText.textContent = "iPhone paired successfully";
      await loadDevices();
      return;
    }

    if (payload.status === "waiting") {
      setTimeout(pollPairing, 1200);
      return;
    }

    pairingStatus.classList.remove("waiting");
    pairingStatus.classList.add("expired");
    pairingStatusText.textContent = "Pairing code expired — reload for a new QR";
  } catch (_error) {
    setTimeout(pollPairing, 1800);
  }
}

loadDevices();
pollPairing();
