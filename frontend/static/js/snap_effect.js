/**
 * 工业动力学转场母版 - V18 (拟人光标注入版)
 * 核心：保持 V17 的块对齐逻辑，注入拟人化光标状态机
 */
const initSnapAnimations = () => {
    const containers = document.querySelectorAll('.snap-box');

    containers.forEach((container) => {
        const sketch = (p) => {
            let rawText = container.parentElement.getAttribute('data-snap-text') || "UI/UX|DESIGN|MOBILE|INTERFACE";
            let lines = rawText.split('|');
            while(lines.length < 4) lines.push(lines[lines.length-1] || " ");
            if(lines.length > 4) lines = lines.slice(0, 4);

            const totalFrames = 420; // 适当拉长时间轴以容纳闪烁
            let maxWidth = 0, step = 0, centeringOffset = 0;

            p.setup = () => {
                const canvas = p.createCanvas(container.offsetWidth, container.offsetHeight);
                canvas.parent(container);
                // 关键：改为左对齐实现稳定打字，但通过 Offset 实现视觉居中
                p.textAlign(p.LEFT, p.CENTER);
                p.textFont('Space Grotesk');
                p.textSize(p.height * 0.13);
                p.textStyle(p.BOLD);

                maxWidth = 0;
                lines.forEach(line => {
                    let w = p.textWidth(line);
                    if (w > maxWidth) maxWidth = w;
                });
                step = maxWidth + 600;
                centeringOffset = -maxWidth / 2; // 视觉对齐偏置
            };

            p.draw = () => {
                p.clear();
                let frame = p.frameCount % totalFrames;
                let spacing = 220, xOffset = 0, reveal = 1;
                let cursorState = 'none'; // none, blink, solid
                let alpha = 255;

                // --- 1. 拟人化光标与动画状态机 ---

                // [0-40帧] 思考期：光标闪烁，文字未现
                if (frame < 40) {
                    reveal = 0; cursorState = 'blink';
                }
                // [40-100帧] 打字期：文字同步打出，光标常亮
                else if (frame < 100) {
                    reveal = p.map(frame, 40, 100, 0, 1, true);
                    cursorState = 'solid';
                    spacing = 220;
                }
                // [100-140帧] 停顿期：字打完了，光标闪烁
                else if (frame < 140) {
                    reveal = 1; cursorState = 'blink';
                    spacing = 220;
                }
                // [140-200帧] 聚合期：上下合并，光标按要求消失
                else if (frame < 200) {
                    reveal = 1; cursorState = 'none';
                    spacing = p.map(frame, 140, 200, 220, 110, true);
                }
                // [200-260帧] 聚合停顿：并拢静止 1s，光标保持隐藏
                else if (frame < 260) {
                    reveal = 1; cursorState = 'none';
                    spacing = 110; xOffset = 0;
                }
                // [260-360帧] 平移期：整体向左滑动，光标重新闪烁
                else if (frame < 360) {
                    reveal = 1; cursorState = 'blink';
                    spacing = 110;
                    xOffset = p.map(frame, 260, 360, 0, -step, true);
                }
                // [360-400帧] 删除期：像按退格键一样逐个消失，光标常亮
                else if (frame < 400) {
                    spacing = 110; xOffset = -step;
                    reveal = p.map(frame, 360, 400, 1, 0, true);
                    cursorState = 'solid';
                }
                // [400-420帧] 结尾：文字消失，光标最后闪烁几下
                else {
                    spacing = 110; xOffset = -step;
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
                            // 锁定 3px 宽度，高度随字号
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
                p.textSize(p.height * 0.13);
                maxWidth = 0;
                lines.forEach(line => { let w = p.textWidth(line); if (w > maxWidth) maxWidth = w; });
                step = maxWidth + 600;
                centeringOffset = -maxWidth / 2;
            };
        };
        new p5(sketch);
    });
};
window.addEventListener('load', initSnapAnimations);