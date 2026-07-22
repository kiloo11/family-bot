import { useEffect, useRef } from "react";
import styles from "./Lightbox.module.css";

export default function Lightbox({ photos, index, albumTitle, onClose, onShow, onDelete }) {
  const activeThumbRef = useRef(null);

  useEffect(() => {
    function onKeydown(e) {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowLeft") onShow(index - 1);
      else if (e.key === "ArrowRight") onShow(index + 1);
    }
    document.addEventListener("keydown", onKeydown);
    return () => document.removeEventListener("keydown", onKeydown);
  }, [index, onClose, onShow]);

  useEffect(() => {
    activeThumbRef.current?.scrollIntoView({ inline: "center", block: "nearest" });
  }, [index]);

  const photo = photos[index];
  if (!photo) return null;

  return (
    <div
      className={styles.lightbox}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className={styles.toolbar}>
        <a href={photo.url} download><span className={styles.label}>⬇ Скачать</span></a>
        <button className={styles.dangerBtn} onClick={() => onDelete(photo)}>
          <span className={styles.label}>🗑 Удалить</span>
        </button>
      </div>
      <button className={styles.close} onClick={onClose} aria-label="Закрыть">✕</button>
      <div className={styles.title}>{albumTitle}</div>
      <div className={styles.stage}>
        <button
          className={styles.nav}
          onClick={() => onShow(index - 1)}
          disabled={index === 0}
          aria-label="Предыдущее фото"
        >
          ‹
        </button>
        <img className={styles.image} src={photo.url} alt="" />
        <button
          className={styles.nav}
          onClick={() => onShow(index + 1)}
          disabled={index === photos.length - 1}
          aria-label="Следующее фото"
        >
          ›
        </button>
      </div>
      <div className={styles.counter}>{index + 1} / {photos.length}</div>
      <div className={styles.thumbs}>
        {photos.map((p, i) => (
          <img
            key={p.id}
            ref={i === index ? activeThumbRef : null}
            src={p.url}
            alt=""
            className={i === index ? styles.active : ""}
            onClick={() => onShow(i)}
          />
        ))}
      </div>
    </div>
  );
}
