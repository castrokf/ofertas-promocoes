import { BarChart3, Bell, FileText, Link2, RadioTower, Store } from "lucide-react";
import { useState } from "react";
import { Channels } from "./pages/Channels";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { Logs } from "./pages/Logs";
import { MonitoredUrls } from "./pages/MonitoredUrls";
import { Rules } from "./pages/Rules";
import { Stores } from "./pages/Stores";
import { clearToken, getToken } from "./services/api";

const tabs = [
  { id: "dashboard", label: "Ofertas", icon: BarChart3 },
  { id: "stores", label: "Lojas", icon: Store },
  { id: "urls", label: "URLs", icon: Link2 },
  { id: "rules", label: "Regras", icon: Bell },
  { id: "channels", label: "Canais", icon: RadioTower },
  { id: "logs", label: "Logs", icon: FileText }
];

export function App() {
  const [active, setActive] = useState("dashboard");
  const [authenticated, setAuthenticated] = useState(Boolean(getToken()));
  if (!authenticated) {
    return <Login onLogin={() => setAuthenticated(true)} />;
  }
  return (
    <div className="app-shell">
      <aside>
        <div className="brand">
          <span>AT</span>
          <div>
            <strong>AutoTechDealsX</strong>
            <small>Admin SaaS</small>
          </div>
        </div>
        <nav>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} className={active === tab.id ? "active" : ""} onClick={() => setActive(tab.id)}>
                <Icon size={18} /> {tab.label}
              </button>
            );
          })}
        </nav>
        <button
          className="logout"
          type="button"
          onClick={() => {
            clearToken();
            setAuthenticated(false);
          }}
        >
          Sair
        </button>
      </aside>
      <main>
        {active === "dashboard" && <Dashboard />}
        {active === "stores" && <Stores />}
        {active === "urls" && <MonitoredUrls />}
        {active === "rules" && <Rules />}
        {active === "channels" && <Channels />}
        {active === "logs" && <Logs />}
      </main>
    </div>
  );
}
