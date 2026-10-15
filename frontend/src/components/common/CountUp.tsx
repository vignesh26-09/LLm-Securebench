// Adapted from React Bits CountUp (count mode), David Haz, 2026.
// Source: https://github.com/DavidHDev/react-bits
// License and permission notice: frontend/THIRD_PARTY_NOTICES.md
import { animate, useInView, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

export function CountUp({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const visible = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!visible) return;
    const control = animate(0, to, { duration: reduce ? 0 : 1.4, ease: [0.33, 1, 0.68, 1], onUpdate: latest => setValue(Math.round(latest)) });
    return () => control.stop();
  }, [to, visible, reduce]);
  return <span ref={ref} aria-label={`${to.toLocaleString()}${suffix}`}><span aria-hidden="true">{value.toLocaleString()}{suffix}</span></span>;
}
