import { Fragment } from "react";
import styles from "./Card.module.css";
import { CATEGORIES } from "../categories.js";

const TAG_CLASS = {
  wishlist: styles.tagWishlist,
  movie: styles.tagMovie,
  bill: styles.tagBill,
  album: styles.tagAlbum,
};

function metaLines(cat, item) {
  const lines = [];
  if (cat === "wishlist") {
    if (item.description) lines.push(item.description);
    if (item.price) lines.push(`💵 ${item.price}`);
    if (item.url) {
      lines.push(
        <a href={item.url} target="_blank" rel="noopener noreferrer">Ссылка на товар ↗</a>,
      );
    }
    lines.push(`— добавил(а) ${item.added_by_name}`);
    if (item.status === "claimed") {
      const who = item.claimed_by_name ? `: ${item.claimed_by_name}` : "";
      lines.push(`🙋 Забронировано${who}`);
    } else if (item.status === "done") {
      lines.push("✅ Выполнено");
    }
  } else if (cat === "movie") {
    if (item.description) lines.push(item.description);
    lines.push(`— предложил(а) ${item.added_by_name}`);
  } else if (cat === "bill") {
    if (item.price) lines.push(`Сумма: ${item.price}`);
    if (item.due_date) lines.push(`Срок: ${item.due_date}`);
    if (item.is_recurring) lines.push("🔁 повторяющийся");
  } else if (cat === "album") {
    if (item.location) lines.push(`📍 ${item.location}`);
    if (item.due_date) lines.push(`📅 ${item.due_date}`);
    lines.push(`добавил(а) ${item.added_by_name}`);
  }
  return lines;
}

function RatingStars({ item, onRate }) {
  return (
    <div className={styles.ratingStars}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          onClick={(e) => {
            e.stopPropagation();
            onRate(n);
          }}
        >
          {item.rating && n <= item.rating ? "★" : "☆"}
        </span>
      ))}
    </div>
  );
}

function Actions({ cat, item, onAction }) {
  if (cat === "album") return null;
  if (cat === "movie" && item.status === "done") {
    return (
      <div className={styles.actions}>
        <button className={styles.danger} onClick={() => onAction("delete")}>🗑 Удалить</button>
      </div>
    );
  }
  if (cat === "wishlist" && item.status !== "active") {
    return (
      <div className={styles.actions}>
        <button onClick={() => onAction("restore")}>↩️ Вернуть в активные</button>
        <button className={styles.danger} onClick={() => onAction("delete")}>🗑 Удалить</button>
      </div>
    );
  }
  return (
    <div className={styles.actions}>
      {cat === "wishlist" && <button onClick={() => onAction("claim")}>🙋 Забронировать</button>}
      <button onClick={() => onAction("done")}>✅ Готово</button>
      <button className={styles.danger} onClick={() => onAction("delete")}>🗑 Удалить</button>
    </div>
  );
}

export default function Card({ category: cat, item, onAction, onRate, onOpenAlbum }) {
  const lines = metaLines(cat, item);
  return (
    <div
      className={`${styles.card} ${cat === "album" ? styles.albumCard : ""}`}
      onClick={cat === "album" ? () => onOpenAlbum(item) : undefined}
    >
      {item.photo_url && <img className={styles.photo} src={item.photo_url} alt={item.title} />}
      <div className={styles.body}>
        <span className={`${styles.tag} ${TAG_CLASS[cat]}`}>{CATEGORIES[cat].title}</span>
        <div className={styles.title}>{item.title}</div>
        <div className={styles.meta}>
          {lines.map((line, i) => (
            <Fragment key={i}>
              {i > 0 && <br />}
              {line}
            </Fragment>
          ))}
        </div>
        {cat === "album" && <div className={styles.hint}>{item.photo_count || 0} фото →</div>}
        {cat === "movie" && item.status === "done" && (
          <RatingStars item={item} onRate={(n) => onRate(item, n)} />
        )}
      </div>
      <Actions cat={cat} item={item} onAction={(action) => onAction(item, action)} />
    </div>
  );
}
