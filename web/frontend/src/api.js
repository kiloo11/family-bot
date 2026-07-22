async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (res.status === 401) {
    window.location.reload();
    throw new Error("unauthorized");
  }
  return res;
}

export async function getMe() {
  const res = await fetch("/api/me");
  if (!res.ok) return null;
  return res.json();
}

export async function listItems(category, status) {
  const res = await request(`/api/items/${category}?status=${status}`);
  return res.json();
}

export function markDone(id) {
  return request(`/api/items/${id}/done`, { method: "POST" });
}

export function claimItem(id) {
  return request(`/api/items/${id}/claim`, { method: "POST" });
}

export function restoreItem(id) {
  return request(`/api/items/${id}/restore`, { method: "POST" });
}

export function deleteItem(id) {
  return request(`/api/items/${id}/delete`, { method: "POST" });
}

export function setRating(id, rating) {
  const formData = new FormData();
  formData.append("rating", rating);
  return request(`/api/items/${id}/rating`, { method: "POST", body: formData });
}

export async function addItem(endpoint, formData) {
  const res = await request(endpoint, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Не получилось сохранить");
  }
  return res.json();
}

export async function listAlbumPhotos(itemId) {
  const res = await request(`/api/albums/${itemId}/photos`);
  return res.json();
}

export async function uploadAlbumPhotos(itemId, files) {
  const formData = new FormData();
  Array.from(files).forEach((f) => formData.append("files", f));
  const res = await request(`/api/albums/${itemId}/photos`, { method: "POST", body: formData });
  return res.json();
}

export async function deleteAlbumPhoto(itemId, photoId) {
  const res = await request(`/api/albums/${itemId}/photos/${photoId}/delete`, { method: "POST" });
  return res.json();
}
