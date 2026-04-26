import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";

interface AppLayoutProps {
  children: ReactNode;
  configPanel: ReactNode;
  activePage: string;
  onNavigate: (id: string) => void;
  healthy: boolean | null;
}

export function AppLayout({
  children,
  configPanel,
  activePage,
  onNavigate,
  healthy,
}: AppLayoutProps) {
  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-white">
      <Sidebar active={activePage} onNavigate={onNavigate} healthy={healthy} />
      <main className="overflow-hidden basis-3/5 min-h-0">{children}</main>
      <aside className="border-l border-gray-200 bg-white overflow-hidden basis-2/5 min-h-0">
        {configPanel}
      </aside>
    </div>
  );
}
