import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export const MainLayout = () => (
  <div className="app-shell">
    <Sidebar />
    <div className="workspace">
      <Header />
      <main className="page-content">
        <Outlet />
      </main>
      <footer className="workspace-footer">
        <span>EMBICO · Репродуктивная медицина</span>
        <span>Забота начинается с внимания к деталям</span>
      </footer>
    </div>
  </div>
);
