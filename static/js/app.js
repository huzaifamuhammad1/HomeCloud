const state = {
  items: [],
  filter: "all",
  pendingDelete: null,
  deviceName: "Paired device",
};

const authorizedApp = document.getElementById("authorizedApp");
const pairGate = document.getElementById("pairGate");
const fileInput = document.getElementById("fileInput");
const refreshButton = document.getElementById("refreshButton");
const gallery = document.getElementById("gallery");
const emptyState = document.getElementById("emptyState");
const serverPill = document.getElementById("serverPill");
const statusText = document.getElementById("statusText");
const deviceLabel = document.getElementById("deviceLabel");
const storageUsed = document.getElementById("storageUsed");
const diskFree = document.getElementById("diskFree");
const itemCount = document.getElementById("itemCount");
const meterFill = document.getElementById("meterFill");
const storagePercent = document.getElementById("storagePercent");
const uploadStatus = document.getElementById("uploadStatus");
const uploadStatusTitle = document.getElementById("uploadStatusTitle");
const uploadStatusText = document.getElementById("uploadStatusText");
const queueCopy = document.getElementById("queueCopy");
const progressBar = document.getElementById("progressBar");
const toast = document.getElementById("toast");
const mobileNav = document.getElementById("mobileNav");

const installChip = document.getElementById("installChip");
const installModal = document.getElementById("installModal");
const closeInstall = document.getElementById("closeInstall");

const settingsModal = document.getElementById("settingsModal");
const settingsNavButton = document.getElementById("settingsNavButton");
const closeSettings = document.getElementById("closeSettings");
const settingsDeviceName = document.getElementById("settingsDeviceName");
const openInstallFromSettings = document.getElementById("openInstallFromSettings");
const forgetDeviceButton = document.getElementById("forgetDeviceButton");

const detailsModal = document.getElementById("detailsModal");
const closeDetailsButton = document.getElementById("closeDetails");
const detailName = document.getElementById("detailName");
const detailType = document.getElementById("detailType");
const detailSize = document.getElementById("detailSize");
const detailDate = document.getElementById("detailDate");
const detailStored = document.getElementById("detailStored");
const detailChecksum = document.getElementById("detailChecksum");

const deleteModal = document.getElementById("deleteModal");
const cancelDelete = document.getElementById("cancelDelete");
const confirmDelete = document.getElementById("confirmDelete");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, i);
  const digits = i === 0 ? 0 : value >= 100 ? 0 : value >= 10 ? 1 : 2;
  return `${value.toFixed(digits)} ${units[i]}`;
}

function formatDate(iso) {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function extension(name) {
  const parts = name.split(".");
  return parts.length > 1 ? parts.pop().toUpperCase().slice(0, 5) : "FILE";
}

function showToast(text) {
  if (!toast) return;
  toast.textContent = text;
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 2600);
}

function filteredItems() {
  if (state.filter === "all") return state.items;
  return state.items.filter((item) => item.category === state.filter);
}

function previewHtml(item) {
  const url = encodeURI(item.view_url);

  if (item.category === "photos") {
    return `<img src="${url}" alt="" loading="lazy">`;
  }

  if (item.category === "videos") {
    return `<video src="${url}" muted playsinline preload="metadata"></video>`;
  }

  return `<div class="type-icon">${escapeHtml(extension(item.original_name))}</div>`;
}

function renderGallery() {
  const items = filteredItems();

  if (!items.length) {
    gallery.innerHTML = "";
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");

  gallery.innerHTML = items.map((item) => `
    <article class="file-card">
      <a class="preview" href="${encodeURI(item.view_url)}" target="_blank" rel="noopener">
        ${previewHtml(item)}
      </a>

      <div class="file-meta">
        <div class="file-name" title="${escapeHtml(item.original_name)}">
          ${escapeHtml(item.original_name)}
        </div>

        <div class="file-subline">
          <span>${formatBytes(item.size_bytes)}</span>
          <span>${escapeHtml(formatDate(item.created_at).split(",")[0])}</span>
        </div>

        <div class="file-actions">
          <a class="download-link" href="${encodeURI(item.download_url)}">Download</a>
          <button class="details-button" data-details="${escapeHtml(item.id)}" type="button">Info</button>
          <button class="delete-button" data-delete="${escapeHtml(item.id)}" type="button">Delete</button>
        </div>
      </div>
    </article>
  `).join("");

  gallery.querySelectorAll("[data-delete]").forEach((button) => {
    button.addEventListener("click", () => openDelete(button.dataset.delete));
  });

  gallery.querySelectorAll("[data-details]").forEach((button) => {
    button.addEventListener("click", () => openDetails(button.dataset.details));
  });
}

async function loadFiles() {
  const response = await fetch("/files", { cache: "no-store" });

  if (response.status === 401) {
    showPairGate();
    throw new Error("Pairing required.");
  }

  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "Could not load files.");

  state.items = payload.items;
  renderGallery();
}

async function loadStorage() {
  const response = await fetch("/storage", { cache: "no-store" });

  if (response.status === 401) {
    showPairGate();
    throw new Error("Pairing required.");
  }

  const payload = await response.json();
  if (!payload.ok) throw new Error(payload.error || "Could not load storage.");

  storageUsed.textContent = formatBytes(payload.homecloud_used_bytes);
  diskFree.textContent = `${formatBytes(payload.disk_free_bytes)} free on Mac`;
  itemCount.textContent = `${payload.item_count} item${payload.item_count === 1 ? "" : "s"}`;

  const usedDisk = Math.max(0, payload.disk_total_bytes - payload.disk_free_bytes);
  const percent = payload.disk_total_bytes
    ? (usedDisk / payload.disk_total_bytes) * 100
    : 0;

  storagePercent.textContent = `${percent.toFixed(0)}% disk used`;
  meterFill.style.width = `${Math.max(1, Math.min(100, percent))}%`;
}

async function refreshAll({ quiet = false } = {}) {
  try {
    await Promise.all([loadFiles(), loadStorage()]);
    if (!quiet) showToast("HomeCloud refreshed");
  } catch (error) {
    if (error.message !== "Pairing required.") {
      showToast(error.message || "Could not refresh HomeCloud.");
    }
  }
}

async function checkServer() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) throw new Error("offline");
    serverPill.classList.add("online");
    statusText.textContent = "Mac online";
  } catch (_error) {
    serverPill.classList.remove("online");
    statusText.textContent = "Mac offline";
  }
}

function showPairGate() {
  pairGate.classList.remove("hidden");
  authorizedApp.classList.add("hidden");
  mobileNav.classList.add("hidden");
}

function showAuthorized(deviceName) {
  state.deviceName = deviceName || "Paired device";
  pairGate.classList.add("hidden");
  authorizedApp.classList.remove("hidden");
  mobileNav.classList.remove("hidden");
  deviceLabel.textContent = state.deviceName;
  settingsDeviceName.textContent = state.deviceName;
}

async function checkAuthorization() {
  try {
    const response = await fetch("/api/auth/status", { cache: "no-store" });
    const payload = await response.json();

    if (!payload.authorized) {
      showPairGate();
      return false;
    }

    showAuthorized(payload.device?.name || "Paired device");
    await refreshAll({ quiet: true });
    return true;
  } catch (_error) {
    showPairGate();
    return false;
  }
}

function uploadOneFile(file, index, total) {
  return new Promise((resolve, reject) => {
    uploadStatus.classList.remove("hidden");
    uploadStatusTitle.textContent = `Uploading ${file.name}`;
    queueCopy.textContent = total > 1 ? `File ${index + 1} of ${total}` : "";
    uploadStatusText.textContent = "0%";
    progressBar.style.width = "0%";

    const form = new FormData();
    form.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload");

    xhr.upload.addEventListener("progress", (event) => {
      if (!event.lengthComputable) return;
      const percent = Math.round((event.loaded / event.total) * 100);
      uploadStatusText.textContent = `${percent}%`;
      progressBar.style.width = `${percent}%`;
    });

    xhr.addEventListener("load", () => {
      let payload = {};
      try { payload = JSON.parse(xhr.responseText); } catch (_error) {}

      if (xhr.status === 401) {
        showPairGate();
        reject(new Error("Pairing required."));
        return;
      }

      if (xhr.status >= 200 && xhr.status < 300 && payload.ok) {
        progressBar.style.width = "100%";
        uploadStatusText.textContent = "Saved";
        resolve(payload);
      } else {
        reject(new Error(payload.error || `Could not upload ${file.name}.`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("The Mac connection dropped."));
    });

    xhr.send(form);
  });
}

async function uploadFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;

  let uploaded = 0;

  try {
    for (let index = 0; index < files.length; index += 1) {
      await uploadOneFile(files[index], index, files.length);
      uploaded += 1;
    }

    uploadStatusTitle.textContent = files.length === 1 ? "Upload complete" : "Uploads complete";
    queueCopy.textContent = "";
    uploadStatusText.textContent = `${uploaded} saved`;
    progressBar.style.width = "100%";

    showToast(
      files.length === 1
        ? `Saved ${files[0].name}`
        : `Saved ${uploaded} files to your Mac`
    );

    await refreshAll({ quiet: true });
    setTimeout(() => uploadStatus.classList.add("hidden"), 1300);
  } catch (error) {
    uploadStatusTitle.textContent = "Upload stopped";
    uploadStatusText.textContent = `${uploaded}/${files.length} saved`;
    queueCopy.textContent = error.message || "Please try again";
    showToast(error.message || "Upload failed.");
  } finally {
    fileInput.value = "";
  }
}

function openDetails(itemId) {
  const item = state.items.find((entry) => entry.id === itemId);
  if (!item) return;

  detailName.textContent = item.original_name;
  detailType.textContent = item.mime_type;
  detailSize.textContent = `${formatBytes(item.size_bytes)} · ${item.size_bytes.toLocaleString()} bytes`;
  detailDate.textContent = formatDate(item.created_at);
  detailStored.textContent = item.stored_name;
  detailChecksum.textContent = item.checksum_sha256;
  detailsModal.classList.remove("hidden");
}

function closeDetails() {
  detailsModal.classList.add("hidden");
}

function openDelete(itemId) {
  state.pendingDelete = itemId;
  deleteModal.classList.remove("hidden");
}

function closeDelete() {
  state.pendingDelete = null;
  deleteModal.classList.add("hidden");
}

async function deletePending() {
  const itemId = state.pendingDelete;
  if (!itemId) return;

  confirmDelete.disabled = true;
  confirmDelete.textContent = "Deleting…";

  try {
    const response = await fetch(`/files/${encodeURIComponent(itemId)}`, {
      method: "DELETE",
    });

    if (response.status === 401) {
      closeDelete();
      showPairGate();
      return;
    }

    const payload = await response.json();
    if (!payload.ok) throw new Error(payload.error || "Delete failed.");

    closeDelete();
    showToast("File deleted");
    await refreshAll({ quiet: true });
  } catch (error) {
    showToast(error.message || "Delete failed.");
  } finally {
    confirmDelete.disabled = false;
    confirmDelete.textContent = "Delete";
  }
}

function openInstallModal() {
  installModal.classList.remove("hidden");
}

function closeInstallModal() {
  installModal.classList.add("hidden");
}

function openSettingsModal() {
  settingsDeviceName.textContent = state.deviceName;
  settingsModal.classList.remove("hidden");
}

function closeSettingsModal() {
  settingsModal.classList.add("hidden");
}

async function forgetThisBrowser() {
  const confirmed = window.confirm(
    "Forget this browser? HomeCloud will require pairing again on this browser."
  );
  if (!confirmed) return;

  await fetch("/api/auth/forget-this-device", {
    method: "POST",
  });

  window.location.reload();
}

fileInput?.addEventListener("change", () => uploadFiles(fileInput.files));
refreshButton?.addEventListener("click", () => refreshAll());

closeDetailsButton?.addEventListener("click", closeDetails);
detailsModal?.addEventListener("click", (event) => {
  if (event.target === detailsModal) closeDetails();
});

cancelDelete?.addEventListener("click", closeDelete);
confirmDelete?.addEventListener("click", deletePending);
deleteModal?.addEventListener("click", (event) => {
  if (event.target === deleteModal) closeDelete();
});

installChip?.addEventListener("click", openInstallModal);
closeInstall?.addEventListener("click", closeInstallModal);
installModal?.addEventListener("click", (event) => {
  if (event.target === installModal) closeInstallModal();
});

settingsNavButton?.addEventListener("click", openSettingsModal);
closeSettings?.addEventListener("click", closeSettingsModal);
settingsModal?.addEventListener("click", (event) => {
  if (event.target === settingsModal) closeSettingsModal();
});

openInstallFromSettings?.addEventListener("click", () => {
  closeSettingsModal();
  openInstallModal();
});

forgetDeviceButton?.addEventListener("click", forgetThisBrowser);

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".segment").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    state.filter = button.dataset.filter;
    renderGallery();
  });
});

document.querySelectorAll("[data-scroll]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.scroll);
    if (!target) return;

    document.querySelectorAll(".mobile-nav-item").forEach((item) => {
      item.classList.remove("active");
    });
    button.classList.add("active");

    target.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

checkServer();
checkAuthorization();
setInterval(checkServer, 15000);
