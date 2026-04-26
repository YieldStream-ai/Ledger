import { useEffect, useState } from "react";
import { healthCheck } from "../api/client";

export function useHealthCheck(intervalMs = 30_000) {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;

    const check = async () => {
      const ok = await healthCheck();
      if (active) setHealthy(ok);
    };

    check();
    const id = setInterval(check, intervalMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [intervalMs]);

  return healthy;
}
