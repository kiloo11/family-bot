export const CATEGORIES = {
  wishlist: {
    title: "Желания", endpoint: "/api/wishlist", emoji: "🎁",
    fields: [
      { name: "title", label: "Что хотим?", type: "text", required: true },
      { name: "description", label: "Комментарий (размер, цвет...)", type: "textarea" },
      { name: "price", label: "Примерная цена", type: "text" },
      { name: "url", label: "Ссылка на товар", type: "text" },
      { name: "photo", label: "Фото", type: "file" },
    ],
  },
  movie: {
    title: "Фильмы", endpoint: "/api/movies", emoji: "🎬",
    fields: [
      { name: "title", label: "Название", type: "text", required: true },
      { name: "description", label: "Комментарий", type: "textarea" },
    ],
  },
  bill: {
    title: "Оплаты", endpoint: "/api/bills", emoji: "💰",
    fields: [
      { name: "title", label: "Название платежа", type: "text", required: true },
      { name: "price", label: "Сумма", type: "text" },
      { name: "due_date", label: "Срок оплаты", type: "date", required: true },
      { name: "is_recurring", label: "Повторяющийся (каждый месяц)", type: "checkbox" },
    ],
  },
  album: {
    title: "Альбомы", endpoint: "/api/albums", emoji: "📷",
    fields: [
      { name: "title", label: "Название альбома", type: "text", required: true },
      { name: "due_date", label: "Дата поездки", type: "date" },
      { name: "location", label: "Страна/город", type: "text" },
    ],
  },
};

// категории, у которых есть саб-табы (переключатель "активные / история" и т.п.)
export const SUBTABS = {
  wishlist: [
    { status: "active", label: "Активные" },
    { status: "history", label: "🗂 История" },
  ],
  movie: [
    { status: "active", label: "Хотим посмотреть" },
    { status: "done", label: "✅ Просмотрено" },
  ],
};

export function emptyHintText(cat, status) {
  if (cat === "movie" && status === "done") return "Пока ничего не посмотрели.";
  if (cat === "wishlist" && status === "history") {
    return "История пуста — пока ничего не выполнено и не забронировано.";
  }
  return "Пока пусто. Самое время что-то добавить 👆";
}
