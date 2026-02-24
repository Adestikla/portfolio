/**
 * 工业动力学转场母版 - 逐字同步入场版
 * 核心：同步左到右逐字显示，压缩垂直间距，保持轴心对齐
 */
const initSnapAnimations = () => {
    const containers = document.querySelectorAll('.snap-box');

    containers.forEach((container) => {
        const sketch = (p) => {
            let rawText = container.parentElement.getAttribute('data-snap-text') || "UI/UX|DESIGN|MOBILE|INTERFACE";
            let lines = rawText.split('|');
            while(lines.length < 4) lines.push(lines[lines.length-1] || " ");
            if(lines.length > 4) lines = lines.slice(0, 4);

            const totalFrames = 360;
            let maxWidth = 0;
            let step = 0;

            p.setup = () => {
                const canvas = p.createCanvas(container.offsetWidth, container.offsetHeight);
                canvas.parent(container);
                p.textAlign(p.CENTER, p.CENTER);
                p.textFont('Space Grotesk');
                p.textSize(p.height * 0.13);
                p.textStyle(p.BOLD);

                maxWidth = 0;
                lines.forEach(line => {
                    let w = p.textWidth(line);
                    if (w > maxWidth) maxWidth = w;
                });
                step = maxWidth + 600;
            };

            p.draw = () => {
                p.clear();
                let frame = p.frameCount % totalFrames;

                // --- 节奏与间距参数 ---
                let spacing = 220;
                let xOffset = 0;
                let revealProgress = 1; // 默认全显示

                // --- 1. 0-60帧 (1s): 同步逐字出现 (取代淡入) ---
                if (frame < 60) {
                    revealProgress = p.map(frame, 0, 50, 0, 1, true); // 0.8s 内完成打印
                    spacing = 220;
                }
                // 2. 60-120帧 (1s): 宽间距停顿阅读
                else if (frame < 120) {
                    spacing = 220;
                }
                // 3. 120-180帧 (1s): 垂直聚合
                else if (frame < 240) {
                    spacing = p.map(frame, 120, 180, 220, 110, true);
                    // 聚合后的 1s 绝对停顿在此处涵盖
                    if (frame >= 180 && frame < 240) {
                        spacing = 110;
                        xOffset = 0;
                    }
                }
                // 4. 240-330帧 (1.5s): 匀速平移
                else if (frame < 330) {
                    spacing = 110;
                    xOffset = p.map(frame, 240, 330, 0, -step, true);
                }
                // 5. 330-360帧: 渐隐
                else {
                    spacing = 110;
                    xOffset = -step;
                    revealProgress = p.map(frame, 330, 360, 1, 0, true);
                }

                p.push();
                p.translate(p.width / 2 + xOffset, p.height / 2);

                for (let r = -1; r <= 3; r++) {
                    p.push();
                    p.translate(r * step, 0);

                    lines.forEach((lineText, i) => {
                        p.push();
                        let y = (i - 1.5) * spacing;
                        p.translate(0, y);

                        // --- 核心：逐字显示逻辑 ---
                        let chars = lineText.split('');
                        let fullWidth = p.textWidth(lineText);
                        let currentText = "";

                        // 计算当前该显示多少个字
                        let visibleCount = p.floor(chars.length * revealProgress);
                        currentText = lineText.substring(0, visibleCount);

                        // 即使字没出全，也要按全宽度的中心对齐，防止文字跳动
                        p.fill(255);
                        p.text(currentText, 0, 0);
                        p.pop();
                    });
                    p.pop();
                }
                p.pop();
            };

            p.windowResized = () => {
                p.resizeCanvas(container.offsetWidth, container.offsetHeight);
                maxWidth = 0;
                lines.forEach(line => {
                    let w = p.textWidth(line);
                    if (w > maxWidth) maxWidth = w;
                });
                step = maxWidth + 600;
            };
        };
        new p5(sketch);
    });
};
window.addEventListener('load', initSnapAnimations);