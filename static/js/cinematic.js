/* =====================================================
   cinematic.js — Global interactions (vanilla JS only)
   - Optional cinematic intro (session-based, skippable)
   - Scroll reveal via IntersectionObserver
   - Number counters
   - Pointer-based 3D tilt
   - Respects prefers-reduced-motion
   ===================================================== */
(function () {
    "use strict";

    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* ---------- 1. Cinematic Intro ---------- */
    function initIntro() {
        const intro = document.getElementById("cine-intro");
        if (!intro) return;

        const skipBtn = document.getElementById("cine-skip");
        const SESSION_KEY = "cine_intro_shown";
        let dismissed = false;

        function dismiss() {
            if (dismissed) return;
            dismissed = true;
            intro.classList.add("is-hidden");
            document.body.style.overflow = "";
            try { sessionStorage.setItem(SESSION_KEY, "1"); } catch (e) { }
        }

        // Only show once per session, and only if not reduced-motion
        let alreadyShown = false;
        try { alreadyShown = sessionStorage.getItem(SESSION_KEY) === "1"; } catch (e) { }

        if (alreadyShown || prefersReduced) {
            intro.style.display = "none";
            return;
        }

        document.body.style.overflow = "hidden";
        if (skipBtn) skipBtn.addEventListener("click", dismiss);

        // Reveal brand after a beat
        setTimeout(() => intro.classList.add("is-revealing"), 400);
        // Auto-dismiss
        setTimeout(dismiss, 4200);

        // Escape to skip
        document.addEventListener("keydown", function onEsc(e) {
            if (e.key === "Escape") {
                dismiss();
                document.removeEventListener("keydown", onEsc);
            }
        });
    }

    /* ---------- 2. Scroll Reveal ---------- */
    function initReveal() {
        const items = document.querySelectorAll(".cine-reveal");
        if (!items.length) return;

        if (prefersReduced || !("IntersectionObserver" in window)) {
            items.forEach(el => el.classList.add("is-visible"));
            return;
        }

        const io = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );

        items.forEach(el => io.observe(el));
    }

    /* ---------- 3. Number Counters ---------- */
    function initCounters() {
        const counters = document.querySelectorAll("[data-cine-count]");
        if (!counters.length) return;

        function animate(el) {
            const target = parseFloat(el.getAttribute("data-cine-count")) || 0;
            const duration = parseInt(el.getAttribute("data-cine-duration") || "1400", 10);
            const decimals = parseInt(el.getAttribute("data-cine-decimals") || "0", 10);
            const prefix = el.getAttribute("data-cine-prefix") || "";
            const suffix = el.getAttribute("data-cine-suffix") || "";

            if (prefersReduced) {
                el.textContent = prefix + target.toFixed(decimals) + suffix;
                return;
            }

            const start = performance.now();
            function tick(now) {
                const p = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - p, 3);
                const val = target * eased;
                el.textContent = prefix + val.toFixed(decimals) + suffix;
                if (p < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        }

        if (!("IntersectionObserver" in window)) {
            counters.forEach(animate);
            return;
        }

        const io = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        animate(entry.target);
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.4 }
        );
        counters.forEach(el => io.observe(el));
    }

    /* ---------- 4. Pointer Tilt ---------- */
    function initTilt() {
        if (prefersReduced) return;
        if (window.matchMedia("(hover: none)").matches) return;

        const wraps = document.querySelectorAll(".cine-tilt-wrap");
        wraps.forEach(wrap => {
            const card = wrap.querySelector(".cine-tilt");
            if (!card) return;

            let rafId = null;
            let pendingX = 0, pendingY = 0;

            function onMove(e) {
                const rect = wrap.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                pendingX = ((e.clientY - cy) / rect.height) * -10;
                pendingY = ((e.clientX - cx) / rect.width) * 10;

                if (rafId) return;
                rafId = requestAnimationFrame(() => {
                    card.style.transform = `rotateX(${pendingX.toFixed(2)}deg) rotateY(${pendingY.toFixed(2)}deg)`;
                    rafId = null;
                });
            }

            function onLeave() {
                card.style.transform = "rotateX(0) rotateY(0)";
            }

            wrap.addEventListener("mousemove", onMove);
            wrap.addEventListener("mouseleave", onLeave);
        });
    }

    /* ---------- 5. Bootstrap tooltips ---------- */
    function initTooltips() {
        if (window.bootstrap && bootstrap.Tooltip) {
            document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
                new bootstrap.Tooltip(el);
            });
        }
    }

    /* ---------- 6. Auto-dismiss alerts ---------- */
    function initAutoDismissAlerts() {
        document.querySelectorAll(".alert[data-cine-auto-dismiss]").forEach(el => {
            setTimeout(() => {
                if (window.bootstrap && bootstrap.Alert) {
                    const b = bootstrap.Alert.getOrCreateInstance(el);
                    b.close();
                }
            }, 5000);
        });
    }

    /* ---------- 7. Active sidebar/nav highlighting ---------- */
    function initActiveNav() {
        const path = window.location.pathname;
        document.querySelectorAll(".cine-sidebar .nav-link[href]").forEach(link => {
            const href = link.getAttribute("href");
            if (!href || href === "#") return;
            if (path === href || (href !== "/" && path.startsWith(href))) {
                link.classList.add("active");
                link.setAttribute("aria-current", "page");
            }
        });
    }

    /* ---------- 8. Cinematic page fade-in ---------- */
    function initPageFade() {
        const main = document.querySelector("[data-cine-page]");
        if (!main || prefersReduced) return;
        main.animate(
            [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "translateY(0)" }],
            { duration: 500, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)", fill: "both" }
        );
    }

    /* ---------- Boot ---------- */
    document.addEventListener("DOMContentLoaded", function () {
        initIntro();
        initReveal();
        initCounters();
        initTilt();
        initTooltips();
        initAutoDismissAlerts();
        initActiveNav();
        initPageFade();
    });
})();
