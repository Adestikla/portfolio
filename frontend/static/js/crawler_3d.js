// ==========================================
// Web Crawler Multi-Stage Particle Morphing (双端物理隔离版)
// ==========================================

window.addEventListener("load", () => {
    // 性能优化：将 3D 引擎的初始化推迟 3.5 秒！彻底释放首屏 CPU 压力
    setTimeout(() => {
        const canvas = document.getElementById('crawler-canvas');
        if (!canvas) return;

        // --- 【核心 1：双端参数隔离】 ---
        const isMobile = window.innerWidth <= 768;
        const particleCount = isMobile ? 1500 : 100000; // 手机端只有 1500 颗粒子作为氛围点缀！PC 端 10 万满血！

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 3000);
        camera.position.z = 400;

        const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const geometry = new THREE.BufferGeometry();
        const currentPositions = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);
        const randoms = new Float32Array(particleCount * 3);

        const shapes = {
            chaos: new Float32Array(particleCount * 3),
            web: new Float32Array(particleCount * 3),
            network: new Float32Array(particleCount * 3),
            streams: new Float32Array(particleCount * 3),
            logo: new Float32Array(particleCount * 3)
        };

        for (let i = 0; i < particleCount; i++) {
            sizes[i] = Math.random() > 0.9 ? Math.random() * 8.0 + 4.0 : Math.random() * 3.0 + 1.0;
            randoms[i * 3] = Math.random() * 10;
            randoms[i * 3 + 1] = Math.random() * 10;
            randoms[i * 3 + 2] = Math.random() * 10;
        }

        function assignPoints(targetArray, points) {
            let pLen = points.length;
            if(pLen === 0) return;
            for (let i = 0; i < particleCount; i++) {
                let pt = points[i % pLen];
                targetArray[i * 3] = pt.x + (Math.random() - 0.5) * 2;
                targetArray[i * 3 + 1] = pt.y + (Math.random() - 0.5) * 2;
                targetArray[i * 3 + 2] = pt.z + (Math.random() - 0.5) * 4;
            }
        }

        // 形态 1: 极度混乱的宇宙 (底层星空)
        for (let i = 0; i < particleCount * 3; i++) {
            if (i % 3 === 2) shapes.chaos[i] = (Math.random() - 0.5) * 9000;
            else shapes.chaos[i] = (Math.random() - 0.5) * 2000;
            currentPositions[i] = shapes.chaos[i];
        }

        // 形态 2: 线性的 Web 网页
        const webPoints = [];
        for (let i = 0; i < Math.min(5000, particleCount); i++) {
            if (i < 800) webPoints.push({ x: (Math.random()-0.5)*350, y: 120, z: (Math.random()-0.5)*10 });
            else if (i < 1800) webPoints.push({ x: -140 + (Math.random()-0.5)*20, y: (Math.random()-0.5)*200, z: 0 });
            else { let col = Math.floor(Math.random() * 3); webPoints.push({ x: -60 + col * 90 + (Math.random()-0.5)*70, y: (Math.random()-0.5)*200, z: (Math.random()-0.5)*15 }); }
        }
        assignPoints(shapes.web, webPoints);

        // 形态 3: 网络安全球体
        const netPoints = [];
        for (let i = 0; i < particleCount; i++) {
            let phi = Math.acos(-1 + (2 * i) / particleCount);
            let theta = Math.sqrt(particleCount * Math.PI) * phi;
            let r = Math.random() > 0.8 ? 60 + Math.random() * 10 : 130 + Math.random() * 20;
            netPoints.push({ x: r * Math.cos(theta) * Math.sin(phi), y: r * Math.sin(theta) * Math.sin(phi), z: r * Math.cos(phi) });
        }
        assignPoints(shapes.network, netPoints);

        // 形态 4: 纵向粗线条数据流
        const streamPoints = [];
        for (let i = 0; i < particleCount; i++) {
            let layer = i % 3; let yPos = (layer - 1) * 80;
            let x, z; let isEdge = Math.random() > 0.5;
            let outerSize = 400; let innerSize = 180; let thickness = (outerSize - innerSize) / 2;
            if (isEdge) { x = (Math.random() - 0.5) * outerSize; z = (Math.random() > 0.5 ? 1 : -1) * (innerSize/2 + Math.random() * thickness); }
            else { x = (Math.random() > 0.5 ? 1 : -1) * (innerSize/2 + Math.random() * thickness); z = (Math.random() - 0.5) * outerSize; }
            x += (Math.random() - 0.5) * 15; yPos += (Math.random() - 0.5) * 15; z += (Math.random() - 0.5) * 15;
            streamPoints.push({ x: x, y: yPos, z: z });
        }
        assignPoints(shapes.streams, streamPoints);

        // 形态 5: 专属 Logo "A"
        function createLogoPoints() {
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = 512; tempCanvas.height = 512;
            const ctx = tempCanvas.getContext('2d');
            ctx.fillStyle = 'black'; ctx.fillRect(0, 0, 512, 512);
            ctx.fillStyle = 'white';
            ctx.font = '900 350px "Space Grotesk", sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText('A', 256, 240);

            const imgData = ctx.getImageData(0, 0, 512, 512).data;
            const lPoints = [];
            const step = isMobile ? 8 : 2;
            for (let y = 0; y < 512; y += step) {
                for (let x = 0; x < 512; x += step) {
                    if (imgData[(y * 512 + x) * 4] > 128) {
                        lPoints.push({ x: (x - 256) * 0.65, y: -(y - 256) * 0.65 + 20, z: (Math.random() - 0.5) * 30 });
                    }
                }
            }
            return lPoints;
        }
        assignPoints(shapes.logo, createLogoPoints());

        geometry.setAttribute('position', new THREE.BufferAttribute(currentPositions, 3));
        geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
        geometry.setAttribute('aRandom', new THREE.BufferAttribute(randoms, 3));

        const uniforms = {
            uTime: { value: 0 }, uPhase: { value: 0 }, uColor: { value: new THREE.Color('#F2613F') }
        };

        const material = new THREE.ShaderMaterial({
            uniforms: uniforms,
            vertexShader: `
                uniform float uTime;
                uniform float uPhase;
                attribute float aSize;
                attribute vec3 aRandom;
                varying vec3 vPos;
                void main() {
                    vPos = position;
                    vec3 pos = position;
                    // 物理抖动
                    pos.x += sin(uTime * 3.5 + aRandom.x * 20.0) * 4.0;
                    pos.y += cos(uTime * 3.0 + aRandom.y * 20.0) * 4.0;
                    pos.z += sin(uTime * 4.0 + aRandom.z * 20.0) * 4.0;
                    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                    gl_PointSize = aSize * (500.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                uniform vec3 uColor;
                uniform float uPhase;
                varying vec3 vPos;
                void main() {
                    vec2 xy = gl_PointCoord.xy - vec2(0.5);
                    float ll = length(xy);
                    if(ll > 0.5) discard;
                    float alpha = smoothstep(0.5, 0.0, ll);

                    vec3 colorMain = vec3(0.95, 0.38, 0.25);
                    vec3 colorSecond = vec3(1.0, 0.75, 0.0);
                    vec3 finalColor = colorMain;

                    if (uPhase > 2.1 && uPhase < 3.9) {
                        float cpuWeight = smoothstep(2.1, 3.0, uPhase) * smoothstep(3.9, 3.0, uPhase);
                        vec3 targetColor = colorMain;
                        if (vPos.y > 40.0) targetColor = vec3(0.3, 0.6, 1.0);
                        else if (vPos.y < -40.0) targetColor = vec3(0.5, 0.9, 0.4);
                        finalColor = mix(colorMain, targetColor, cpuWeight);
                    }

                    if (uPhase > 3.1) {
                        float aWeight = smoothstep(3.1, 4.0, uPhase);
                        float mixFactor = smoothstep(-60.0, 60.0, vPos.x);
                        vec3 aColor = mix(colorMain, colorSecond, mixFactor);
                        finalColor = mix(finalColor, aColor, aWeight);
                    }
                    gl_FragColor = vec4(finalColor, alpha * 0.95);
                }
            `,
            transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
        });

        const particleSystem = new THREE.Points(geometry, material);
        scene.add(particleSystem);

        const params = { phase: 0 };
        gsap.registerPlugin(ScrollTrigger);

        // --- 【核心 2：事件分流】 ---
        // --- 【核心 2：事件分流 (修复回退消失Bug)】 ---
        const init3DScrollAnimations = () => {
            let mm = gsap.matchMedia();

            // 💻 1. PC 端逻辑
            mm.add("(min-width: 769px)", () => {
                gsap.set('.phase-text-container', { opacity: 0, y: 30 });
                gsap.set('.crawler-ui-layer', { opacity: 0, pointerEvents: "none" });
                gsap.set(['.crawler-title', '.crawler-subtitle', '.crawler-search-box'], { opacity: 0, y: 20 });
                gsap.set(particleSystem.position, { z: 350 });

                const tl = gsap.timeline({
                    scrollTrigger: {
                        trigger: ".crawler-3d-section",
                        start: "top top",
                        end: "bottom bottom",
                        scrub: 1,
                    }
                });
                tl.to(params, { phase: 1, ease: "none", duration: 2 }, "step1")
                  .to(particleSystem.position, { x: 120, z: -50, duration: 2 }, "step1")
                  .to(particleSystem.rotation, { y: 0.1, x: -0.1, duration: 2 }, "step1")
                  .to("#text-phase-1", { opacity: 1, y: 0, duration: 0.5 }, "step1+=0.5")
                  .to("#text-phase-1", { opacity: 0, y: -30, duration: 0.5 }, "step2")
                  .to(params, { phase: 2, ease: "none", duration: 2 }, "step2")
                  .to(particleSystem.position, { x: 140, z: 80, duration: 2 }, "step2")
                  .to(particleSystem.rotation, { y: 0.2, x: 0.1, duration: 2 }, "step2")
                  .to("#text-phase-2", { opacity: 1, y: 0, duration: 0.5 }, "step2+=0.5")
                  .to("#text-phase-2", { opacity: 0, y: -30, duration: 0.5 }, "step3")
                  .to(params, { phase: 3, ease: "none", duration: 2 }, "step3")
                  .to(particleSystem.position, { x: 120, y: -20, z: -100, duration: 2 }, "step3")
                  .to(particleSystem.rotation, { x: 0.8, y: 0.5, z: 0, duration: 2 }, "step3")
                  .to("#text-phase-3", { opacity: 1, y: 0, duration: 0.5 }, "step3+=0.5")
                  .to("#text-phase-3", { opacity: 0, y: -30, duration: 0.5 }, "step4")
                  .to(params, { phase: 4, ease: "none", duration: 2 }, "step4")
                  .to(particleSystem.position, { x: 0, y: -65, z: 60, duration: 2 }, "step4")
                  .to(particleSystem.rotation, { y: -0.08, x: 0.02, z: 0, duration: 2 }, "step4")
                  .to('.crawler-ui-layer', { opacity: 1, pointerEvents: "auto", duration: 0.1 }, "step4+=1")
                  .to(['.crawler-title', '.crawler-subtitle', '.crawler-search-box'], { opacity: 1, y: 0, duration: 0.8, stagger: 0.2 }, "step4+=1");
            });

            // 📱 2. 手机端逻辑
            mm.add("(max-width: 768px)", () => {
                gsap.set('.phase-text-container', { clearProps: "all" });
                gsap.set('.crawler-ui-layer', { clearProps: "all" });
                gsap.set(['.crawler-title', '.crawler-subtitle', '.crawler-search-box'], { clearProps: "all" });

                params.phase = 0;
                gsap.set(particleSystem.position, { x: 0, y: 0, z: -100 });

                const mobContainer = document.querySelector('.crawler-mobile-flex-container');
                if(mobContainer) {
                    mobContainer.addEventListener('scroll', () => {
                        const maxScroll = mobContainer.scrollWidth - mobContainer.clientWidth;
                        if(maxScroll <= 0) return;

                        const progress = mobContainer.scrollLeft / maxScroll;
                        let targetPhase = progress * 4;

                        gsap.to(params, {
                            phase: targetPhase,
                            duration: 0.5,
                            overwrite: "auto",
                            ease: "power2.out"
                        });

                        if (progress > 0.85) {
                            gsap.to(particleSystem.position, { x: 0, y: -15, z: 0, duration: 0.8, overwrite: "auto" });
                            gsap.to(particleSystem.rotation, { x: 0, y: 0, z: 0, duration: 0.8, overwrite: "auto" });
                        } else {
                            gsap.to(particleSystem.position, { x: 0, y: 0, z: -100, duration: 0.8, overwrite: "auto" });
                            gsap.to(particleSystem.rotation, { x: 0.1, y: progress * 3, z: 0, duration: 0.8, overwrite: "auto" });
                        }
                    });
                }
            });
        };

        // 🚨 核心修复：判断信号是否已经提前发过了
        if (window.isIntroFinished) {
            init3DScrollAnimations(); // 如果回退网页，进场动画秒跳过，信号已发，直接初始化
        } else {
            window.addEventListener("start3DScroll", init3DScrollAnimations); // 还在看进场动画，乖乖等信号
        }

        const phasesArray = [shapes.chaos, shapes.web, shapes.network, shapes.streams, shapes.logo];
        const clock = new THREE.Clock();

        // 性能核弹：交叉观察器。只有当 3D 画布进入屏幕时，才允许渲染！
        let is3DVisible = false;
        const observer = new IntersectionObserver((entries) => {
            is3DVisible = entries[0].isIntersecting;
        }, { rootMargin: "0px" });
        observer.observe(document.querySelector('.crawler-3d-section'));

        function animate() {
            requestAnimationFrame(animate);

            // 核心拦截：如果没滚动到 3D 区域，直接跳出函数，0 性能消耗！
            if (!is3DVisible) return;

            uniforms.uTime.value = clock.getElapsedTime();
            uniforms.uPhase.value = params.phase;

            const posAttr = geometry.attributes.position;
            let currentPhaseIdx = Math.floor(params.phase);
            let nextPhaseIdx = Math.min(currentPhaseIdx + 1, 4);
            let progress = params.phase - currentPhaseIdx;
            let arr1 = phasesArray[currentPhaseIdx];
            let arr2 = phasesArray[nextPhaseIdx];

            for (let i = 0; i < particleCount * 3; i++) {
                posAttr.array[i] = arr1[i] + (arr2[i] - arr1[i]) * progress;
            }
            posAttr.needsUpdate = true;
            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

    // 这里就是缺失的闭合括号！它把上面的所有 3D 初始化逻辑包起来，并延迟 3.5 秒执行
    }, 3500);
});