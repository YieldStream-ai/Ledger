import { useState, useRef, useEffect } from "react";
import {
  FileText,
  ScanSearch,
  FileCheck,
  BarChart3,
  ClipboardList,
  Layers,
  ChevronDown,
  ExternalLink,
} from "lucide-react";
import { clsx } from "clsx";
import styles from "./Sidebar.module.css";

const navItems = [
  { id: "parse", label: "Parse", icon: FileText },
  { id: "classify", label: "Classify", icon: ScanSearch },
  { id: "approval", label: "Approval", icon: FileCheck },
  { id: "enrich", label: "Enrich", icon: BarChart3 },
  { id: "templates", label: "Templates", icon: Layers },
  { id: "review", label: "Needs Review", icon: ClipboardList },
];

function Logomark() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" fill="rgba(255,255,255,0.12)" />
      <rect x="8" y="9" width="16" height="2" rx="1" fill="rgba(255,255,255,0.9)" />
      <rect x="8" y="15" width="12" height="2" rx="1" fill="rgba(255,255,255,0.9)" />
      <rect x="8" y="21" width="14" height="2" rx="1" fill="rgba(255,255,255,0.9)" />
    </svg>
  );
}

interface SidebarProps {
  active: string;
  onNavigate: (id: string) => void;
  healthy: boolean | null;
}

export function Sidebar({ active, onNavigate, healthy }: SidebarProps) {
  const [brandOpen, setBrandOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!brandOpen) return;
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setBrandOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [brandOpen]);

  return (
    <aside className={styles.sidebar}>
      {/* ── Brand block ── */}
      <div className={styles.brandZone} ref={dropdownRef}>
        <button
          type="button"
          className={styles.brandButton}
          onClick={() => setBrandOpen((o) => !o)}
          aria-expanded={brandOpen}
        >
          <Logomark />
          <div className={styles.brandText}>
            <span className={styles.wordmark}>Ledger</span>
            <span className={styles.brandSub}>by YieldStream</span>
          </div>
          <ChevronDown
            className={clsx(styles.brandChevron, brandOpen && styles.brandChevronOpen)}
          />
        </button>

        {brandOpen && (
          <div className={styles.brandDropdown}>
            <div className={styles.dropdownRow}>
              <span className={styles.dropdownLabel}>API Status</span>
              <span className={styles.dropdownValue}>
                <span
                  className={clsx(
                    styles.statusDot,
                    healthy === true && styles.statusConnected,
                    healthy === false && styles.statusOffline,
                    healthy === null && styles.statusChecking
                  )}
                />
                {healthy === true
                  ? "Connected"
                  : healthy === false
                    ? "Offline"
                    : "Checking…"}
              </span>
            </div>
            <div className={styles.dropdownRow}>
              <span className={styles.dropdownLabel}>Environment</span>
              <span className={styles.dropdownValue}>Production</span>
            </div>
            <div className={styles.dropdownRow}>
              <span className={styles.dropdownLabel}>Version</span>
              <span className={styles.dropdownValue}>1.0.0</span>
            </div>
            <div className={styles.dropdownDivider} />
            <a
              href="https://yieldstream.io"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.dropdownLink}
            >
              Open YieldStream
              <ExternalLink className={styles.dropdownLinkIcon} />
            </a>
          </div>
        )}
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={clsx(
              styles.navButton,
              active === item.id && styles.navButtonActive
            )}
          >
            <item.icon className={styles.navIcon} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className={styles.footer}>
        <div className={styles.statusRow}>
          <span
            className={clsx(
              styles.statusDot,
              healthy === true && styles.statusConnected,
              healthy === false && styles.statusOffline,
              healthy === null && styles.statusChecking
            )}
          />
          {healthy === true
            ? "API Connected"
            : healthy === false
              ? "API Offline"
              : "Checking..."}
        </div>
      </div>
    </aside>
  );
}
