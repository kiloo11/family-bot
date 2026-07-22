import { useRef } from "react";
import styles from "./AlbumView.module.css";

export default function AlbumView({ item, photos, onBack, onDeleteAlbum, onOpenPhoto, onUploadPhotos, onDeletePhoto }) {
  const fileInputRef = useRef(null);

  const metaParts = [];
  if (item.location) metaParts.push(`📍 ${item.location}`);
  if (item.due_date) metaParts.push(`📅 ${item.due_date}`);

  return (
    <div>
      <button className={styles.btnBack} onClick={onBack}>← Назад к альбомам</button>
      <div className={styles.head}>
        <div>
          <h2>{item.title}</h2>
          <div>{metaParts.join("  ·  ")}</div>
        </div>
        <button className={styles.btnDangerOutline} onClick={onDeleteAlbum}>🗑 Удалить альбом</button>
      </div>
      <div className={styles.photoGrid}>
        {photos.map((p, i) => (
          <div className={styles.photoTile} key={p.id}>
            <img src={p.url} alt="" onClick={() => onOpenPhoto(i)} />
            <div className={styles.overlay}>
              <a href={p.url} download title="Скачать" onClick={(e) => e.stopPropagation()}>⬇</a>
              <button
                className={styles.dangerBtn}
                title="Удалить фото"
                onClick={(e) => {
                  e.stopPropagation();
                  if (!confirm("Удалить это фото?")) return;
                  onDeletePhoto(p.id);
                }}
              >
                ✕
              </button>
            </div>
          </div>
        ))}
        <label className={styles.addTile}>
          <span className={styles.plus}>+</span>Добавить фото
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: "none" }}
            onChange={(e) => {
              if (!e.target.files.length) return;
              onUploadPhotos(e.target.files);
              e.target.value = "";
            }}
          />
        </label>
      </div>
    </div>
  );
}
