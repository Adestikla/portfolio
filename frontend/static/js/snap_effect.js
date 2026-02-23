const initSnapAnimations = () => {
    const containers = document.querySelectorAll('.snap-box');

    containers.forEach((container) => {
        const sketch = (p) => {
            let rawText = container.parentElement.getAttribute('data-snap-text') || "UI/UX|DESIGN";
            let lines = rawText.split('|');
            let frameCount = 0;
            const cycleFrames = 150; // 一个完整的动画周期时长

            p.setup = () => {
                const canvas = p.createCanvas(container.offsetWidth, container.offsetHeight);
                canvas.parent(container);
                p.textAlign(p.CENTER, p.CENTER);
                p.textFont('Space Grotesk');
            };

            p.draw = () => {
                p.clear();
                frameCount = (p.frameCount % cycleFrames);

                // --- 动画阶段权重计算 ---
                // 0.0-0.3: 淡入合并 | 0.3-0.8: 拉伸平移保持 | 0.8-1.0: 极速淡出
                let stage = frameCount / cycleFrames;

                let progressIn = p.constrain(p.map(stage, 0, 0.3, 0, 1), 0, 1);
                let progressHold = p.constrain(p.map(stage, 0.3, 0.8, 0, 1), 0, 1);
                let progressOut = p.constrain(p.map(stage, 0.8, 0.95, 0, 1), 0, 1);

                // 动态行间距：从 350 缩减到 120 (实现合并效果)
                let currentSpacing = p.lerp(350, 120, p.pow(progressIn, 0.5));

                p.push();
                p.translate(p.width / 2, p.height / 2);

                // 2. 整体平移：随 Hold 阶段向左侧滑动
                let globalXShift = p.lerp(0, -50, progressHold);
                p.translate(globalXShift, 0);

                lines.forEach((lineText, lineIndex) => {
                    p.push();
                    let yPos = (lineIndex - (lines.length - 1) / 2) * currentSpacing;
                    p.translate(0, yPos);

                    let chars = lineText.split('');
                    let charGap = p.width * 0.07;

                    chars.forEach((char, charIndex) => {
                        p.push();
                        let xBase = (charIndex - (chars.length - 1) / 2) * charGap;

                        // 1. 左侧淡入位移：从左边更远的地方跑过来
                        let xOffset = p.lerp(-100, 0, p.pow(progressIn, 0.3));
                        p.translate(xBase + xOffset, 0);

                        // --- 关键：动力学拉伸 (Kinetic Stretch) ---
                        // 在 Hold 阶段随机触发横向 X 轴剧烈拉伸
                        let stretchX = 1.0;
                        if (progressHold > 0 && progressHold < 1) {
                            // 模拟视频中的瞬时爆发感
                            if (p.random(1) > 0.92) {
                                stretchX = p.random(1.5, 3.0);
                                p.shearX(p.random(-0.3, 0.3));
                            }
                        }
                        p.scale(stretchX, 1.0);

                        // 透明度处理：左侧淡入 + 整体淡出
                        let individualFadeIn = p.constrain(p.map(progressIn, charIndex * 0.05, 0.5 + charIndex * 0.05, 0, 255), 0, 255);
                        let totalAlpha = individualFadeIn * (1 - progressOut);

                        p.fill(255, totalAlpha);
                        p.textSize(p.height * 0.28);
                        p.textStyle(p.BOLD);
                        p.text(char, 0, 0);
                        p.pop();
                    });
                    p.pop();
                });
                p.pop();
            };

            p.windowResized = () => {
                p.resizeCanvas(container.offsetWidth, container.offsetHeight);
            };
        };

        new p5(sketch);
    });
};

window.addEventListener('load', initSnapAnimations);