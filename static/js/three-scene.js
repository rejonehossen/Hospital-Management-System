/* =====================================================
   three-scene.js — Three.js cinematic 3D scenes
   - Intro: rotating holographic medical sphere + particles
   - Hero: floating wireframe anatomical / molecular visual
   Uses Three.js from CDN. Falls back gracefully if
   WebGL is unavailable or reduced-motion is set.
   ===================================================== */
(function () {
    "use strict";

    if (!window.THREE) return;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function supportsWebGL() {
        try {
            const c = document.createElement("canvas");
            return !!(window.WebGLRenderingContext && (c.getContext("webgl") || c.getContext("experimental-webgl")));
        } catch (e) {
            return false;
        }
    }

    if (!supportsWebGL()) {
        document.querySelectorAll("[data-cine-three]").forEach(el => el.style.display = "none");
        return;
    }

    /* ============ INTRO SCENE ============ */
    function initIntroScene() {
        const canvas = document.getElementById("cine-intro-canvas");
        if (!canvas) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 5;

        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(window.innerWidth, window.innerHeight);

        // Holographic wireframe sphere
        const sphereGeo = new THREE.IcosahedronGeometry(1.5, 1);
        const sphereMat = new THREE.MeshBasicMaterial({
            color: 0x22d3ee,
            wireframe: true,
            transparent: true,
            opacity: 0.55,
        });
        const sphere = new THREE.Mesh(sphereGeo, sphereMat);
        scene.add(sphere);


        // Inner glow sphere
        const innerGeo = new THREE.SphereGeometry(1.1, 32, 32);
        const innerMat = new THREE.MeshBasicMaterial({
            color: 0x0e7490,
            transparent: true,
            opacity: 0.18,
        });
        scene.add(new THREE.Mesh(innerGeo, innerMat));

        // Particle cloud
        const pCount = 600;
        const positions = new Float32Array(pCount * 3);
        for (let i = 0; i < pCount; i++) {
            const r = 2.4 + Math.random() * 2.4;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = r * Math.cos(phi);
        }
        const pGeo = new THREE.BufferGeometry();
        pGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        const pMat = new THREE.PointsMaterial({
            color: 0xa5f3fc,
            size: 0.03,
            transparent: true,
            opacity: 0.7,
            depthWrite: false,
        });
        const particles = new THREE.Points(pGeo, pMat);
        scene.add(particles);

        let visible = true;
        document.addEventListener("visibilitychange", () => {
            visible = !document.hidden;
        });

        let t = 0;
        function animate() {
            if (!visible) {
                requestAnimationFrame(animate);
                return;
            }
            t += 0.004;
            sphere.rotation.y += 0.0035;
            sphere.rotation.x = Math.sin(t) * 0.15;
            particles.rotation.y -= 0.0009;
            particles.rotation.x += 0.0004;
            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        if (!prefersReduced) animate();
        else renderer.render(scene, camera);

        window.addEventListener("resize", () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }

    /* ============ HERO SCENE ============ */
    function initHeroScene() {
        const canvas = document.querySelector("[data-cine-three]");
        if (!canvas) return;

        const wrap = canvas.parentElement;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(50, wrap.clientWidth / wrap.clientHeight, 0.1, 1000);
        camera.position.z = 6;

        const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(wrap.clientWidth, wrap.clientHeight);

        // Outer dodecahedron shell
        const shellGeo = new THREE.DodecahedronGeometry(2.4, 0);
        const shellMat = new THREE.MeshBasicMaterial({
            color: 0x22d3ee,
            wireframe: true,
            transparent: true,
            opacity: 0.35,
        });
        const shell = new THREE.Mesh(shellGeo, shellMat);
        scene.add(shell);

        // Inner icosahedron
        const coreGeo = new THREE.IcosahedronGeometry(1.1, 1);
        const coreMat = new THREE.MeshBasicMaterial({
            color: 0x8b5cf6,
            wireframe: true,
            transparent: true,
            opacity: 0.55,
        });
        const core = new THREE.Mesh(coreGeo, coreMat);
        scene.add(core);

        // Glow sphere
        const glowGeo = new THREE.SphereGeometry(0.6, 24, 24);
        const glowMat = new THREE.MeshBasicMaterial({
            color: 0x14b8a6,
            transparent: true,
            opacity: 0.35,
        });
        scene.add(new THREE.Mesh(glowGeo, glowMat));

        // Orbital ring of dots
        const ringCount = 60;
        const ringPos = new Float32Array(ringCount * 3);
        for (let i = 0; i < ringCount; i++) {
            const a = (i / ringCount) * Math.PI * 2;
            ringPos[i * 3] = Math.cos(a) * 3.2;
            ringPos[i * 3 + 1] = Math.sin(a) * 0.4;
            ringPos[i * 3 + 2] = Math.sin(a) * 3.2;
        }
        const ringGeo = new THREE.BufferGeometry();
        ringGeo.setAttribute("position", new THREE.BufferAttribute(ringPos, 3));
        const ringMat = new THREE.PointsMaterial({
            color: 0xa5f3fc,
            size: 0.07,
            transparent: true,
            opacity: 0.9,
        });
        const ring = new THREE.Points(ringGeo, ringMat);
        scene.add(ring);

        // Pointer parallax
        let targetX = 0, targetY = 0;
        window.addEventListener("pointermove", e => {
            targetX = (e.clientX / window.innerWidth - 0.5) * 0.6;
            targetY = (e.clientY / window.innerHeight - 0.5) * 0.6;
        });

        let visible = true;
        document.addEventListener("visibilitychange", () => {
            visible = !document.hidden;
        });

        function animate() {
            if (!visible) {
                requestAnimationFrame(animate);
                return;
            }
            shell.rotation.y += 0.0022;
            shell.rotation.x += 0.0008;
            core.rotation.y -= 0.004;
            core.rotation.z += 0.002;
            ring.rotation.y += 0.006;

            camera.position.x += (targetX - camera.position.x) * 0.04;
            camera.position.y += (-targetY - camera.position.y) * 0.04;
            camera.lookAt(scene.position);

            renderer.render(scene, camera);
            requestAnimationFrame(animate);
        }

        if (!prefersReduced) animate();
        else renderer.render(scene, camera);

        const ro = new ResizeObserver(() => {
            camera.aspect = wrap.clientWidth / wrap.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(wrap.clientWidth, wrap.clientHeight);
        });
        ro.observe(wrap);
    }

    document.addEventListener("DOMContentLoaded", function () {
        initIntroScene();
        initHeroScene();
    });
})();
