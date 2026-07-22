import { useRef, useState } from "react";
import styles from "./AddForm.module.css";
import { CATEGORIES } from "../categories.js";

export default function AddForm({ category, onSubmit, onCancel }) {
  const formRef = useRef(null);
  const [error, setError] = useState("");
  const conf = CATEGORIES[category];

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const formData = new FormData(formRef.current);
    try {
      await onSubmit(formData);
    } catch (err) {
      setError(err.message || "Не получилось сохранить");
    }
  }

  return (
    <form className={styles.form} ref={formRef} onSubmit={handleSubmit}>
      {error && <div className={styles.field} style={{ color: "var(--rose)" }}>{error}</div>}
      {conf.fields.map((f) => {
        if (f.type === "checkbox") {
          return (
            <label key={f.name} className={`${styles.field} ${styles.checkboxRow}`}>
              <input type="checkbox" name={f.name} /> {f.label}
            </label>
          );
        }
        return (
          <label key={f.name} className={styles.field}>
            {f.label}{f.required ? " *" : ""}
            {f.type === "textarea" ? (
              <textarea name={f.name} rows={2} />
            ) : f.type === "file" ? (
              <input type="file" name={f.name} accept="image/*" />
            ) : (
              <input type={f.type} name={f.name} required={f.required} />
            )}
          </label>
        );
      })}
      <div className={styles.formActions}>
        <button type="submit" className={styles.btnPrimary}>Сохранить</button>
        <button type="button" className={styles.btnSecondary} onClick={onCancel}>Отмена</button>
      </div>
    </form>
  );
}
