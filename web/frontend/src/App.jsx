import { useCallback, useEffect, useState } from "react";
import styles from "./App.module.css";
import contentStyles from "./components/Content.module.css";
import LoginScreen from "./components/LoginScreen.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SubTabs from "./components/SubTabs.jsx";
import AddForm from "./components/AddForm.jsx";
import ItemsGrid from "./components/ItemsGrid.jsx";
import AlbumView from "./components/AlbumView.jsx";
import Lightbox from "./components/Lightbox.jsx";
import { CATEGORIES, SUBTABS, emptyHintText } from "./categories.js";
import {
  getMe, listItems, markDone, claimItem, restoreItem, deleteItem, setRating,
  addItem, listAlbumPhotos, uploadAlbumPhotos, deleteAlbumPhoto,
} from "./api.js";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = ещё грузим, null = не залогинен
  const [authError, setAuthError] = useState("");

  const [currentCategory, setCurrentCategory] = useState("wishlist");
  const [subStatus, setSubStatus] = useState({ wishlist: "active", movie: "active" });
  const [items, setItems] = useState([]);
  const [addFormOpen, setAddFormOpen] = useState(false);

  const [albumItem, setAlbumItem] = useState(null);
  const [albumPhotos, setAlbumPhotos] = useState([]);
  const [lightboxIndex, setLightboxIndex] = useState(null);

  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute("data-theme") || "light",
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const err = params.get("auth_error");
    if (err) {
      setAuthError(err);
      window.history.replaceState({}, "", "/");
    }
    getMe().then(setUser);
  }, []);

  const status = subStatus[currentCategory] || "active";

  const reloadItems = useCallback(async () => {
    const data = await listItems(currentCategory, status);
    setItems(data);
  }, [currentCategory, status]);

  useEffect(() => {
    if (user && !albumItem) reloadItems();
  }, [user, albumItem, reloadItems]);

  if (user === undefined) return null;
  if (!user) return <LoginScreen authError={authError} />;

  function switchCategory(cat) {
    setCurrentCategory(cat);
    setAddFormOpen(false);
    setAlbumItem(null);
    if (SUBTABS[cat]) {
      setSubStatus((prev) => ({ ...prev, [cat]: "active" }));
    }
  }

  async function handleAddSubmit(formData) {
    await addItem(CATEGORIES[currentCategory].endpoint, formData);
    setAddFormOpen(false);
    reloadItems();
  }

  async function handleAction(item, action) {
    if (action === "done") {
      await markDone(item.id);
      if (currentCategory === "movie") { setSubStatus((p) => ({ ...p, movie: "done" })); return; }
      if (currentCategory === "wishlist") { setSubStatus((p) => ({ ...p, wishlist: "history" })); return; }
      reloadItems();
    } else if (action === "claim") {
      await claimItem(item.id);
      setSubStatus((p) => ({ ...p, wishlist: "history" }));
    } else if (action === "restore") {
      await restoreItem(item.id);
      reloadItems();
    } else if (action === "delete") {
      if (!confirm(`Удалить «${item.title}»?`)) return;
      await deleteItem(item.id);
      reloadItems();
    }
  }

  async function handleRate(item, n) {
    await setRating(item.id, n);
    reloadItems();
  }

  async function openAlbum(item) {
    setAlbumItem(item);
    setAlbumPhotos(await listAlbumPhotos(item.id));
  }

  async function handleDeleteAlbum() {
    if (!albumItem) return;
    if (!confirm(`Удалить альбом «${albumItem.title}» вместе со всеми фото?`)) return;
    await deleteItem(albumItem.id);
    setAlbumItem(null);
    setAlbumPhotos([]);
  }

  async function refreshAlbumPhotos() {
    const photos = await listAlbumPhotos(albumItem.id);
    setAlbumPhotos(photos);
    return photos;
  }

  async function handleUploadPhotos(files) {
    await uploadAlbumPhotos(albumItem.id, files);
    refreshAlbumPhotos();
  }

  async function handleDeletePhotoFromGrid(photoId) {
    await deleteAlbumPhoto(albumItem.id, photoId);
    refreshAlbumPhotos();
  }

  async function handleDeletePhotoFromLightbox(photo) {
    if (!confirm("Удалить это фото?")) return;
    await deleteAlbumPhoto(albumItem.id, photo.id);
    const updated = await refreshAlbumPhotos();
    if (!updated.length) { setLightboxIndex(null); return; }
    setLightboxIndex((i) => Math.min(i, updated.length - 1));
  }

  function showLightboxPhoto(i) {
    if (i < 0 || i >= albumPhotos.length) return;
    setLightboxIndex(i);
  }

  return (
    <div className={styles.app}>
      <Sidebar
        user={user}
        currentCategory={currentCategory}
        onSwitchCategory={switchCategory}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className={contentStyles.content}>
        {!albumItem && (
          <>
            <div className={contentStyles.contentHead}>
              <h2>{CATEGORIES[currentCategory].title}</h2>
              <button className={contentStyles.btnAdd} onClick={() => setAddFormOpen((v) => !v)}>
                + Добавить
              </button>
            </div>

            <SubTabs
              category={currentCategory}
              status={status}
              onChange={(s) => setSubStatus((p) => ({ ...p, [currentCategory]: s }))}
            />

            {addFormOpen && (
              <AddForm
                category={currentCategory}
                onSubmit={handleAddSubmit}
                onCancel={() => setAddFormOpen(false)}
              />
            )}

            <ItemsGrid
              category={currentCategory}
              items={items}
              emptyHint={emptyHintText(currentCategory, status)}
              onAction={handleAction}
              onRate={handleRate}
              onOpenAlbum={openAlbum}
            />
          </>
        )}

        {albumItem && (
          <AlbumView
            item={albumItem}
            photos={albumPhotos}
            onBack={() => setAlbumItem(null)}
            onDeleteAlbum={handleDeleteAlbum}
            onOpenPhoto={showLightboxPhoto}
            onUploadPhotos={handleUploadPhotos}
            onDeletePhoto={handleDeletePhotoFromGrid}
          />
        )}
      </main>

      {lightboxIndex !== null && (
        <Lightbox
          photos={albumPhotos}
          index={lightboxIndex}
          albumTitle={albumItem?.title || ""}
          onClose={() => setLightboxIndex(null)}
          onShow={showLightboxPhoto}
          onDelete={handleDeletePhotoFromLightbox}
        />
      )}
    </div>
  );
}
