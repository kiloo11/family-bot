import styles from "./Content.module.css";
import { SUBTABS } from "../categories.js";

export default function SubTabs({ category, status, onChange }) {
  const tabs = SUBTABS[category];
  if (!tabs) return null;
  return (
    <div className={styles.subTabs}>
      {tabs.map((t) => (
        <button
          key={t.status}
          className={`${styles.subTab} ${t.status === status ? styles.active : ""}`}
          onClick={() => onChange(t.status)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
