import styles from "./Sidebar.module.css";
import { CATEGORIES } from "../categories.js";

export default function Sidebar({ user, currentCategory, onSwitchCategory, theme, onToggleTheme }) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.brandMark}>✦</span>
        <span className={styles.brandName}>Семейный<br />органайзер</span>
      </div>

      <nav className={styles.tabs}>
        {Object.entries(CATEGORIES).map(([cat, conf]) => (
          <button
            key={cat}
            className={`${styles.tab} ${cat === currentCategory ? styles.active : ""}`}
            onClick={() => onSwitchCategory(cat)}
          >
            <span className={styles.tabIcon}>{conf.emoji}</span>
            {conf.title}
          </button>
        ))}
      </nav>

      <div className={styles.userChip}>
        {user.photo_url && <img src={user.photo_url} alt="" className={styles.avatar} />}
        <span className={styles.userName}>{user.first_name}</span>
        <button
          className={styles.themeToggle}
          onClick={onToggleTheme}
          title={theme === "dark" ? "Светлая тема" : "Тёмная тема"}
          aria-label="Переключить тему"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <a href="/logout" className={styles.logoutLink} title="Выйти">⏻</a>
      </div>
    </aside>
  );
}
