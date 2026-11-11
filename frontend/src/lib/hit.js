import { useEffect } from "react";

// The desktop window is a big transparent rectangle. Only the parts that actually show something should catch the mouse;
// everything else must click through to the apps underneath. Every interactive/visible block carries `data-hit`; we report
// their rectangles to the desktop shell (through the agent), which turns them into a window mask.
export const collectRects = (root = document) =>
  [...root.querySelectorAll("[data-hit]")].map((el) => {
    const r = el.getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  }).filter(([, , w, h]) => w > 0 && h > 0);

export function useHitRegions(send) {
  useEffect(() => {
    let last = "", raf = 0;
    const push = () => {
      raf = 0;
      const rects = collectRects();
      const key = JSON.stringify(rects);
      if (key !== last) {
        last = key;
        send({ type: "shell_hit", rects });
        // Electron shell (optional): update click-through regions in the main process
        try { window.electronShell?.setHitRects?.(rects); } catch (_) {}
      }
    };
    const schedule = () => { if (!raf) raf = requestAnimationFrame(push); };
    const mo = new MutationObserver(schedule);
    mo.observe(document.body, { childList: true, subtree: true, attributes: true });
    const ro = new ResizeObserver(schedule);
    ro.observe(document.body);
    window.addEventListener("resize", schedule);
    const iv = setInterval(schedule, 400);                      // animations / scrolling that observers do not report
    schedule();
    return () => { mo.disconnect(); ro.disconnect(); clearInterval(iv); window.removeEventListener("resize", schedule); };
  }, [send]);
}
