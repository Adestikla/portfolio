/**
 * 工业动力学转场母版 - V19 (PC & Mobile 完美双端适配版)
 * 核心：注入响应式状态机，手机端根据宽度自适应防裁切，PC端保持原始张力
 */
const initSnapAnimations = () => {
    const containers = document.querySelectorAll('.snap-box');

    containers.forEach((container) => {
        const sketch = (p) => {
            let rawText = container.parentElement.getAttribute('data-snap-text') || "UI/UX|DESIGN|MOBILE|INTERFACE";
            let lines = rawText.split('|');
            while(lines.length < 4) lines.push(lines[lines.length-1] || " ");
            if(lines.length > 4) lines = lines.slice(0, 4);

            const totalFrames = 420;
            let maxWidth = 0, step = 0, centeringOffset = 0;
            let isMobile = false;

            // --- 核心修复：集中处理响应式计算的工具函数 ---
            const calcResponsive = () => {
                isMobile = window.innerWidth <= 768;

                if (isMobile) {
                    // 📱 手机端：字号基于屏幕宽度，防止被左右裁切
                    p.textSize(p.width * 0.13);
                } else {
                    // 💻 PC端：保持原样，基于高度带来视觉冲击力
                    p.textSize(p.height * 0.13);
                }

                // 重新计算最大宽度
                maxWidth = 0;
                lines.forEach(line => {
                    let w = p.textWidth(line);
                    if (w > maxWidth) maxWidth = w;
                });

                // 间距调整：手机端缩短左右滑动的间隔时间与距离
                step = maxWidth + (isMobile ? 120 : 600);
                centeringOffset = -maxWidth / 2;
            };

            p.setup = () => {
                const canvas = p.createCanvas(container.offsetWidth, container.offsetHeight);
                canvas.parent(container);
                p.textAlign(p.LEFT, p.CENTER);
                p.textFont('Space Grotesk');
                p.textStyle(p.BOLD);

                // 初始化时计算一次响应式参数
                calcResponsive();
            };

            p.draw = () => {
                p.clear();
                let frame = p.frameCount % totalFrames;
                let xOffset = 0, reveal = 1;
                let cursorState = 'none'; // none, blink, solid
                let alpha = 255;

                // --- 动态计算行距 (针对手机端缩放) ---
                // PC 保持 220/110，手机端根据字号动态计算紧凑行距
                let maxSp = isMobile ? p.textSize() * 1.8 : 220;
                let minSp = isMobile ? p.textSize() * 1.0 : 110;
                let spacing = maxSp;

                // --- 1. 拟人化光标与动画状态机 ---
                if (frame < 40) {
                    reveal = 0; cursorState = 'blink';
                } else if (frame < 100) {
                    reveal = p.map(frame, 40, 100, 0, 1, true);
                    cursorState = 'solid';
                    spacing = maxSp;
                } else if (frame < 140) {
                    reveal = 1; cursorState = 'blink';
                    spacing = maxSp;
                } else if (frame < 200) {
                    reveal = 1; cursorState = 'none';
                    spacing = p.map(frame, 140, 200, maxSp, minSp, true);
                } else if (frame < 260) {
                    reveal = 1; cursorState = 'none';
                    spacing = minSp; xOffset = 0;
                } else if (frame < 360) {
                    reveal = 1; cursorState = 'blink';
                    spacing = minSp;
                    xOffset = p.map(frame, 260, 360, 0, -step, true);
                } else if (frame < 400) {
                    spacing = minSp; xOffset = -step;
                    reveal = p.map(frame, 360, 400, 1, 0, true);
                    cursorState = 'solid';
                } else {
                    spacing = minSp; xOffset = -step;
                    reveal = 0; cursorState = 'blink';
                }

                // --- 2. 渲染逻辑 ---
                p.push();
                p.translate(p.width / 2 + xOffset, p.height / 2);

                for (let r = -1; r <= 3; r++) {
                    p.push();
                    p.translate(r * step, 0);

                    lines.forEach((lineText, i) => {
                        let y = (i - 1.5) * spacing;
                        let visibleCount = p.floor(lineText.length * reveal);
                        let currentText = lineText.substring(0, visibleCount);

                        p.fill(242, 97, 63, alpha);
                        p.text(currentText, centeringOffset, y);

                        // --- 3. 绘制 3px 细光标 ---
                        let isBlinking = (p.frameCount % 20 < 10);
                        let shouldDraw = (cursorState === 'solid') || (cursorState === 'blink' && isBlinking);

                        if (shouldDraw) {
                            let tw = p.textWidth(currentText);
                            let cursorX = centeringOffset + tw + 8; // 文字后的间距
                            p.push();
                            p.noStroke();
                            p.fill(242, 97, 63, alpha);
                            p.rect(cursorX, y - p.textSize()*0.42, 3, p.textSize()*0.85);
                            p.pop();
                        }
                    });
                    p.pop();
                }
                p.pop();
            };

            p.windowResized = () => {
                p.resizeCanvas(container.offsetWidth, container.offsetHeight);
                // 窗口尺寸改变（如横竖屏切换）时，重新校准参数
                calcResponsive();
            };
        };
        new p5(sketch);
    });
};
window.addEventListener('load', initSnapAnimations);