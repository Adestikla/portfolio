// ==========================================
// Web Crawler Multi-Stage Particle Morphing (Pro Shader Version)
// ==========================================

window.addEventListener("load", () => {
    const canvas = document.getElementById('crawler-canvas');
    if (!canvas) return;

    // 1. 基础场景设置
    const scene = new THREE.Scene();
    // 调小 FOV，增加纵深感，让“近大远小”更夸张
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 3000);
    camera.position.z = 400;

    const renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // 2. 核心数据升级：暴增至 40,000 颗粒子
    const particleCount = 100000;
    const geometry = new THREE.BufferGeometry();
    const currentPositions = new Float32Array(particleCount * 3);

    // 【新增】每颗粒子独有的大小和随机抖动种子
    const sizes = new Float32Array(particleCount);
    const randoms = new Float32Array(particleCount * 3);

    const shapes = {
        chaos: new Float32Array(particleCount * 3),
        web: new Float32Array(particleCount * 3),
        network: new Float32Array(particleCount * 3),
        streams: new Float32Array(particleCount * 3),
        logo: new Float32Array(particleCount * 3)
    };

    // 初始化随机属性
    for (let i = 0; i < particleCount; i++) {
        // 大小差异化：极少数非常大，大部分是小星尘
        sizes[i] = Math.random() > 0.9 ? Math.random() * 8.0 + 4.0 : Math.random() * 3.0 + 1.0;

        // 随机三维向量，用于控制每颗粒子的独立抖动
        randoms[i * 3] = Math.random() * 10;
        randoms[i * 3 + 1] = Math.random() * 10;
        randoms[i * 3 + 2] = Math.random() * 10;
    }

    function assignPoints(targetArray, points) {
        let pLen = points.length;
        for (let i = 0; i < particleCount; i++) {
            let pt = points[i % pLen];
            // 加入微小的坐标扰动，让密集的地方产生体积感而不是变成一个平面
            targetArray[i * 3] = pt.x + (Math.random() - 0.5) * 2;
            targetArray[i * 3 + 1] = pt.y + (Math.random() - 0.5) * 2;
            targetArray[i * 3 + 2] = pt.z + (Math.random() - 0.5) * 4;
        }
    }

    // --- 形态 1: 极度混乱的宇宙 (强化“扑面而来”的纵深感) ---
    for (let i = 0; i < particleCount * 3; i++) {
        // Z 轴分布拉得极长，模拟深深的隧道
        if (i % 3 === 2) shapes.chaos[i] = (Math.random() - 0.5) * 9000;
        else shapes.chaos[i] = (Math.random() - 0.5) * 2000;
        currentPositions[i] = shapes.chaos[i];
    }

    // --- 形态 2: 线性的 Web 网页 ---
    const webPoints = [];
    for (let i = 0; i < 5000; i++) {
        if (i < 800) webPoints.push({ x: (Math.random()-0.5)*350, y: 120, z: (Math.random()-0.5)*10 });
        else if (i < 1800) webPoints.push({ x: -140 + (Math.random()-0.5)*20, y: (Math.random()-0.5)*200, z: 0 });
        else {
            let col = Math.floor(Math.random() * 3);
            webPoints.push({ x: -60 + col * 90 + (Math.random()-0.5)*70, y: (Math.random()-0.5)*200, z: (Math.random()-0.5)*15 });
        }
    }
    assignPoints(shapes.web, webPoints);

    // --- 形态 3: 网络安全球体 (带有两层壳的洋葱结构) ---
    const netPoints = [];
    for (let i = 0; i < particleCount; i++) {
        let phi = Math.acos(-1 + (2 * i) / particleCount);
        let theta = Math.sqrt(particleCount * Math.PI) * phi;
        // 20%的粒子构成内核心，80%构成外层护盾
        let r = Math.random() > 0.8 ? 60 + Math.random() * 10 : 130 + Math.random() * 20;
        netPoints.push({
            x: r * Math.cos(theta) * Math.sin(phi),
            y: r * Math.sin(theta) * Math.sin(phi),
            z: r * Math.cos(phi)
        });
    }
    assignPoints(shapes.network, netPoints);

    // --- 形态 4: 纵向粗线条数据流 (黑客帝国代码雨) ---
    const streamPoints = [];
    for (let i = 0; i < particleCount; i++) {
        // 将 10 万粒子密集地分配到 3 层主板上
        let layer = i % 3;
        let yPos = (layer - 1) * 80; // 3层在 Y 轴的高度：-80, 0, 80

        // 在 XZ 平面上生成带有中心空洞的方框 (类似 CPU 的晶体管阵列)
        let x, z;
        let isEdge = Math.random() > 0.5;
        let outerSize = 400; // 主板外径
        let innerSize = 180; // 内部空洞大小
        let thickness = (outerSize - innerSize) / 2; // 边框厚度

        if (isEdge) { // 上下边缘
            x = (Math.random() - 0.5) * outerSize;
            z = (Math.random() > 0.5 ? 1 : -1) * (innerSize/2 + Math.random() * thickness);
        } else { // 左右边缘
            x = (Math.random() > 0.5 ? 1 : -1) * (innerSize/2 + Math.random() * thickness);
            z = (Math.random() - 0.5) * outerSize;
        }

        // 加入高斯噪点，产生“原子沉积”的厚重颗粒感
        x += (Math.random() - 0.5) * 15;
        yPos += (Math.random() - 0.5) * 15;
        z += (Math.random() - 0.5) * 15;

        streamPoints.push({ x: x, y: yPos, z: z });
    }
    assignPoints(shapes.streams, streamPoints);

    // --- 形态 5: 专属 Logo "A" ---
    function createLogoPoints() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 512; tempCanvas.height = 512;
        const ctx = tempCanvas.getContext('2d');

        ctx.fillStyle = 'black'; ctx.fillRect(0, 0, 512, 512);
        ctx.fillStyle = 'white';
        ctx.font = '900 350px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('A', 256, 240);

        ctx.font = '900 45px sans-serif';

        const imgData = ctx.getImageData(0, 0, 512, 512).data;
        const lPoints = [];
        // 因为粒子多了，我们可以更密集地采样 (步长减小到 2)
        for (let y = 0; y < 512; y += 2) {
            for (let x = 0; x < 512; x += 2) {
                let alpha = imgData[(y * 512 + x) * 4];
                if (alpha > 128) {
                    lPoints.push({
                        x: (x - 256) * 0.65,
                        y: -(y - 256) * 0.65 + 20,
                        z: (Math.random() - 0.5) * 30 // 加大厚度，让 Logo 看起来是立体的
                    });
                }
            }
        }
        return lPoints;
    }
    assignPoints(shapes.logo, createLogoPoints());

    // 3. 【核心黑科技】自定义 Shader 材质
    geometry.setAttribute('position', new THREE.BufferAttribute(currentPositions, 3));
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
    geometry.setAttribute('aRandom', new THREE.BufferAttribute(randoms, 3));

    const uniforms = {
        uTime: { value: 0 },
        uPhase: { value: 0 },
        uColor: { value: new THREE.Color('#F2613F') }
    };

    const material = new THREE.ShaderMaterial({
        // 【就是这里！上一次漏掉了这行，导致 GPU 收不到任何指令】
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
                
                // 【加强版物理抖动】
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
                
                vec3 colorMain = vec3(0.95, 0.38, 0.25); // 主色：落日橙
                vec3 colorSecond = vec3(1.0, 0.75, 0.0); // 拼接色：金黄
                
                vec3 finalColor = colorMain; 
                
                // 【CPU 蓝绿三层上色】
                if (uPhase > 2.1 && uPhase < 3.9) {
                    float cpuWeight = smoothstep(2.1, 3.0, uPhase) * smoothstep(3.9, 3.0, uPhase);
                    
                    vec3 targetColor = colorMain;
                    if (vPos.y > 40.0) targetColor = vec3(0.3, 0.6, 1.0);      // 顶层科技蓝
                    else if (vPos.y < -40.0) targetColor = vec3(0.5, 0.9, 0.4); // 底层雷蛇绿
                    
                    finalColor = mix(colorMain, targetColor, cpuWeight);
                }
                
                // 【A字双色拼接】
                if (uPhase > 3.1) {
                    float aWeight = smoothstep(3.1, 4.0, uPhase);
                    float mixFactor = smoothstep(-60.0, 60.0, vPos.x);
                    vec3 aColor = mix(colorMain, colorSecond, mixFactor);
                    
                    finalColor = mix(finalColor, aColor, aWeight);
                }
                
                gl_FragColor = vec4(finalColor, alpha * 0.95);
            }
        `,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending
    });

    const particleSystem = new THREE.Points(geometry, material);
    scene.add(particleSystem);

    // 4. GSAP 动画控制与精准触发机制
    const params = { phase: 0 };
    gsap.registerPlugin(ScrollTrigger);

    // 初始状态设定：放在屏幕外围，并且透明
    gsap.set(particleSystem.position, { z: 350 });
    gsap.set('.crawler-ui-layer > *', { opacity: 0, y: 20 });

    // 【核心修复】：听到 index.html 开火的信号后，才创建滚动触发器！
    window.addEventListener("start3DScroll", () => {
        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: ".crawler-3d-section",
                start: "top top", // 此时此刻量到的 top 绝对是精准的
                end: "bottom bottom",
                scrub: 1.5,
            }
        });

        tl.to(params, { phase: 1, ease: "power1.inOut", duration: 1 })
          .to(particleSystem.position, { x: 0, z: -50, duration: 1 }, "<")
          .to(particleSystem.rotation, { y: 0.1, x: -0.1, duration: 1 }, "<") // 极其微小的偏移

          // 阶段 2: 网络球体
          .to(params, { phase: 2, ease: "power1.inOut", duration: 1 })
          .to(particleSystem.position, { x: 120, z: 80, duration: 1 }, "<")
          .to(particleSystem.rotation, { y: 0.2, x: 0.1, duration: 1 }, "<") // 侧一点点

          // 阶段 3: CPU 沉积层 (倾斜成上帝视角！)
          .to(params, { phase: 3, ease: "power1.inOut", duration: 1 })
          .to(particleSystem.position, { x: 0, y: 0, z: -100, duration: 1 }, "<")
          // 【核心魔法】：X轴翻下，Y轴侧转，形成极其高级的 2.5D 晶体管透视视角！
          .to(particleSystem.rotation, { x: 0.8, y: 0.5, z: 0, duration: 1 }, "<")

          // 阶段 4: 最终 Logo
          .to(params, { phase: 4, ease: "power1.inOut", duration: 1 })
          .to(particleSystem.position, { x: 0, y: -65, z: 60, duration: 1 }, "<")
          .to(particleSystem.rotation, { y: -0.08, x: 0.02, z: 0, duration: 1 }, "<")
          .to('.crawler-ui-layer > *', { opacity: 1, y: 0, duration: 0.1, stagger: 0.05 });
    });
    gsap.set('.crawler-ui-layer > *', { opacity: 0, y: 20 });

    // 5. 渲染循环
    const phasesArray = [shapes.chaos, shapes.web, shapes.network, shapes.streams, shapes.logo];
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        // 传递时间给 Shader，驱动粒子持续抖动
        uniforms.uTime.value = clock.getElapsedTime();
        uniforms.uPhase.value = params.phase;

        const posAttr = geometry.attributes.position;
        let currentPhaseIdx = Math.floor(params.phase);
        let nextPhaseIdx = Math.min(currentPhaseIdx + 1, 4);
        let progress = params.phase - currentPhaseIdx;

        let arr1 = phasesArray[currentPhaseIdx];
        let arr2 = phasesArray[nextPhaseIdx];

        // 4万粒子的位置更新
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
});