import cardStyles from "./Card.module.css";
import contentStyles from "./Content.module.css";
import Card from "./Card.jsx";

export default function ItemsGrid({ category, items, emptyHint, onAction, onRate, onOpenAlbum }) {
  if (!items.length) {
    return <p className={contentStyles.emptyHint}>{emptyHint}</p>;
  }
  return (
    <div className={cardStyles.grid}>
      {items.map((item) => (
        <Card
          key={item.id}
          category={category}
          item={item}
          onAction={onAction}
          onRate={onRate}
          onOpenAlbum={onOpenAlbum}
        />
      ))}
    </div>
  );
}
