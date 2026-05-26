import { type FormEvent, useState } from "react";
import { api, setToken } from "../services/api";

export function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("admin@autotech.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api.login(email, password);
      setToken(response.access_token);
      onLogin();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <p className="eyebrow">Acesso administrativo</p>
        <h1>AutoTechDealsX</h1>
        <label>
          E-mail
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
        </label>
        <label>
          Senha
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>{loading ? "Entrando..." : "Entrar"}</button>
        <small className="muted">Troque o usuario inicial e a senha antes de publicar em producao.</small>
      </form>
    </main>
  );
}
