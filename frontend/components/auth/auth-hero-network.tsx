"use client";

import { useEffect, useRef } from "react";

type Node = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  core: boolean;
};

type Pulse = {
  from: number;
  to: number;
  t: number;
  speed: number;
};

// Same rgb() triples as the pinned .auth-hero tokens in globals.css.
const LINK_RGB = "183,176,255"; // --color-primary (dark)
const HIGHLIGHT_RGB = "229,225,249"; // --color-on-background (dark)
const CORE_INDEX = 0;
const LINK_DIST = 150;

export function AuthHeroNetwork() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;
    let nodes: Node[] = [];
    let pulses: Pulse[] = [];
    let running = true;
    let rafId = 0;
    let last = performance.now();
    let pulseTimer = 0;
    const mouse = { x: -9999, y: -9999, active: false };

    function resize() {
      const rect = container!.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas!.width = width * dpr;
      canvas!.height = height * dpr;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function seed() {
      nodes = [];
      const count = Math.max(28, Math.floor((width * height) / 26000));
      for (let i = 0; i < count; i++) {
        nodes.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.14,
          vy: (Math.random() - 0.5) * 0.14,
          r: Math.random() * 1.4 + 1,
          core: false,
        });
      }
      nodes[CORE_INDEX] = {
        x: width * 0.32,
        y: height * 0.34,
        vx: 0,
        vy: 0,
        r: 3.4,
        core: true,
      };
    }

    function spawnPulse() {
      if (nodes.length < 2) return;
      const to = Math.floor(Math.random() * nodes.length);
      if (to === CORE_INDEX) return;
      pulses.push({ from: CORE_INDEX, to, t: 0, speed: 0.006 + Math.random() * 0.004 });
    }

    function step(dt: number) {
      for (const node of nodes) {
        if (node.core) continue;
        node.x += node.vx * dt;
        node.y += node.vy * dt;
        if (node.x < 0 || node.x > width) node.vx *= -1;
        if (node.y < 0 || node.y > height) node.vy *= -1;
        node.x = Math.max(0, Math.min(width, node.x));
        node.y = Math.max(0, Math.min(height, node.y));

        if (mouse.active) {
          const dx = node.x - mouse.x;
          const dy = node.y - mouse.y;
          const d2 = dx * dx + dy * dy;
          const radius = 90;
          if (d2 < radius * radius) {
            const d = Math.sqrt(d2) || 1;
            const force = (1 - d / radius) * 0.06;
            node.x += (dx / d) * force * dt;
            node.y += (dy / d) * force * dt;
          }
        }
      }

      for (let i = pulses.length - 1; i >= 0; i--) {
        pulses[i].t += pulses[i].speed * dt;
        if (pulses[i].t >= 1) pulses.splice(i, 1);
      }
    }

    function draw() {
      ctx!.clearRect(0, 0, width, height);

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < LINK_DIST) {
            const opacity = (1 - dist / LINK_DIST) * (a.core || b.core ? 0.5 : 0.16);
            ctx!.strokeStyle = `rgba(${LINK_RGB},${opacity})`;
            ctx!.lineWidth = 1;
            ctx!.beginPath();
            ctx!.moveTo(a.x, a.y);
            ctx!.lineTo(b.x, b.y);
            ctx!.stroke();
          }
        }
      }

      for (const node of nodes) {
        if (node.core) {
          const pulseR = node.r + Math.sin(Date.now() / 500) * 1.1;
          const glow = ctx!.createRadialGradient(node.x, node.y, 0, node.x, node.y, pulseR * 7);
          glow.addColorStop(0, `rgba(${HIGHLIGHT_RGB},0.55)`);
          glow.addColorStop(1, `rgba(${HIGHLIGHT_RGB},0)`);
          ctx!.fillStyle = glow;
          ctx!.beginPath();
          ctx!.arc(node.x, node.y, pulseR * 7, 0, Math.PI * 2);
          ctx!.fill();

          ctx!.fillStyle = "rgba(255,255,255,0.95)";
          ctx!.beginPath();
          ctx!.arc(node.x, node.y, pulseR, 0, Math.PI * 2);
          ctx!.fill();
        } else {
          ctx!.fillStyle = `rgba(${HIGHLIGHT_RGB},0.4)`;
          ctx!.beginPath();
          ctx!.arc(node.x, node.y, node.r, 0, Math.PI * 2);
          ctx!.fill();
        }
      }

      for (const pulse of pulses) {
        const a = nodes[pulse.from];
        const b = nodes[pulse.to];
        if (!a || !b) continue;
        const x = a.x + (b.x - a.x) * pulse.t;
        const y = a.y + (b.y - a.y) * pulse.t;
        const alpha = Math.sin(pulse.t * Math.PI);
        ctx!.fillStyle = `rgba(${HIGHLIGHT_RGB},${alpha * 0.95})`;
        ctx!.beginPath();
        ctx!.arc(x, y, 2.1, 0, Math.PI * 2);
        ctx!.fill();

        const glow = ctx!.createRadialGradient(x, y, 0, x, y, 8);
        glow.addColorStop(0, `rgba(${HIGHLIGHT_RGB},${alpha * 0.5})`);
        glow.addColorStop(1, `rgba(${HIGHLIGHT_RGB},0)`);
        ctx!.fillStyle = glow;
        ctx!.beginPath();
        ctx!.arc(x, y, 8, 0, Math.PI * 2);
        ctx!.fill();
      }
    }

    function drawStatic() {
      step(0);
      draw();
    }

    function frame(now: number) {
      if (!running) return;
      const dt = Math.min(now - last, 48);
      last = now;
      pulseTimer += dt;
      if (pulseTimer > 900 + Math.random() * 900) {
        pulseTimer = 0;
        spawnPulse();
      }
      step(dt);
      draw();
      rafId = requestAnimationFrame(frame);
    }

    resize();
    seed();

    if (reduceMotion) {
      drawStatic();
    } else {
      rafId = requestAnimationFrame(frame);
    }

    const resizeObserver = new ResizeObserver(() => {
      resize();
      seed();
      if (reduceMotion) drawStatic();
    });
    resizeObserver.observe(container);

    function handleMouseMove(event: MouseEvent) {
      const rect = container!.getBoundingClientRect();
      mouse.x = event.clientX - rect.left;
      mouse.y = event.clientY - rect.top;
      mouse.active = true;
    }
    function handleMouseLeave() {
      mouse.active = false;
    }
    function handleVisibilityChange() {
      running = !document.hidden && !reduceMotion;
      if (running) {
        last = performance.now();
        rafId = requestAnimationFrame(frame);
      } else {
        cancelAnimationFrame(rafId);
      }
    }

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      running = false;
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  return <canvas ref={canvasRef} className="auth-hero-canvas" aria-hidden="true" />;
}
