import styles from "./LoginScreen.module.css";

export default function LoginScreen({ authError }) {
  return (
    <div className={styles.screen}>
      <div className={styles.glow}></div>
      <div className={styles.card}>
        <span className={styles.eyebrow}>Только для своих</span>
        <h1>Семейный органайзер</h1>
        <p>
          Желания, фильмы, оплаты и альбомы — всё, что раньше жило в боте, теперь и здесь.
          Войди через Telegram, чтобы увидеть общий список семьи.
        </p>
        <a href="/auth/telegram/login" className={styles.btnTelegramLogin}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8-1.6 7.54c-.12.54-.44.67-.89.42l-2.46-1.81-1.19 1.14c-.13.13-.24.24-.5.24l.18-2.52 4.6-4.15c.2-.18-.04-.28-.31-.1l-5.68 3.58-2.45-.76c-.53-.17-.54-.53.11-.78l9.58-3.69c.44-.17.83.1.61.89z" fill="currentColor"/>
          </svg>
          Войти через Telegram
        </a>
        {authError && <p className={styles.hint}>⚠️ {authError}</p>}
      </div>
    </div>
  );
}
