#!/usr/bin/env node
/**
 * run.js — Master Orchestrator
 * =============================
 * Unified entry point. Choose your renderer:
 *
 *   node run.js "topic"                  → Manim pipeline (Python)
 *   node run.js "topic" --remotion       → Remotion React video
 *   node run.js "topic" --threejs        → Three.js HTML scenes
 *   node run.js "topic" --all            → All three + merge
 *
 * Requirements:
 *   Python: pip install groq gtts python-dotenv moviepy manim
 *   Node:   npm install groq-sdk
 *   System: ffmpeg, node 18+
 */

const { execSync, spawnSync } = require("child_process");
const path = require("path");
const fs   = require("fs");

const args      = process.argv.slice(2);
const topic     = args.find(a => !a.startsWith("--")) || null;
const useRemot  = args.includes("--remotion");
const useThree  = args.includes("--threejs");
const useAll    = args.includes("--all");
const useMmpy   = args.includes("--manim") || (!useRemot && !useThree && !useAll);
const outDir    = args.includes("--out") ? args[args.indexOf("--out")+1] : "./output";
const quality   = args.includes("--quality") ? args[args.indexOf("--quality")+1] : "medium";
const doRender  = args.includes("--render");

if (!topic) {
  console.log(`
╔═══════════════════════════════════════════════════════════╗
║        AI EXPLAINER VIDEO GENERATOR — Master CLI          ║
╠═══════════════════════════════════════════════════════════╣
║  node run.js <topic> [renderer] [options]                 ║
║                                                           ║
║  Renderers (pick one):                                    ║
║    --manim       Manim animations (Python) [default]      ║
║    --remotion    Remotion React video                     ║
║    --threejs     Three.js 3D HTML scenes                  ║
║    --all         Generate all three                       ║
║                                                           ║
║  Options:                                                 ║
║    --out <dir>      Output directory  (default: ./output) ║
║    --quality <q>    low|medium|high|4k  (Manim only)      ║
║    --render         Auto-render after generation          ║
║                                                           ║
║  Examples:                                                ║
║    node run.js "How does DNA work?"                       ║
║    node run.js "Explain quicksort" --remotion --render    ║
║    node run.js "What is blockchain?" --all --render       ║
╚═══════════════════════════════════════════════════════════╝
  `);
  process.exit(0);
}

fs.mkdirSync(outDir, { recursive: true });

console.log(`\n${"═".repeat(60)}`);
console.log(`  AI EXPLAINER VIDEO GENERATOR`);
console.log(`  Topic   : ${topic}`);
console.log(`  Out     : ${outDir}`);
console.log(`  Render  : ${doRender}`);
console.log(`${"═".repeat(60)}\n`);

async function runManimPipeline() {
  console.log("[Manim] Starting Python/Manim pipeline …");
  const outFile = path.join(outDir, "manim_explainer.mp4");
  const result  = spawnSync(
    "python",
    ["pipeline.py", topic, "-o", outFile, "-q", quality],
    { stdio:"inherit", cwd: __dirname }
  );
  if (result.status !== 0) {
    console.error("[Manim] Pipeline failed.");
  } else {
    console.log(`[Manim] ✅ Done: ${outFile}`);
  }
}

async function runRemotionPipeline() {
  console.log("[Remotion] Generating React video project …");
  const { generatePlan, writeProject, renderProject } = require("./remotion_generator");
  const plan    = await generatePlan(topic);
  const projDir = path.join(outDir, "remotion_project");
  writeProject(plan, projDir);
  // Save plan for three.js
  fs.writeFileSync(path.join(outDir, "plan.json"), JSON.stringify(plan, null, 2));
  if (doRender) renderProject(projDir);
  console.log(`[Remotion] ✅ Done: ${projDir}`);
}

async function runThreeJsPipeline() {
  console.log("[Three.js] Generating 3D scene HTML files …");
  const planFile = path.join(outDir, "plan.json");
  if (!fs.existsSync(planFile)) {
    // Need to generate plan first
    const { generatePlan } = require("./remotion_generator");
    const plan = await generatePlan(topic);
    fs.writeFileSync(planFile, JSON.stringify(plan, null, 2));
  }
  const { writeThreeScenes, renderFrames, framesToVideo } = require("./threejs_scenes");
  const plan       = JSON.parse(fs.readFileSync(planFile, "utf-8"));
  const scenesDir  = path.join(outDir, "threejs_scenes");
  const htmlPaths  = writeThreeScenes(plan, scenesDir);

  if (doRender) {
    console.log("[Three.js] Rendering frames via puppeteer (needs: npm install puppeteer) …");
    for (let i = 0; i < htmlPaths.length; i++) {
      const sc  = plan.scenes[i];
      const dur = (sc.duration_frames || 210) / (plan.fps || 30);
      const fd  = path.join(scenesDir, `frames_${String(i).padStart(2,"0")}`);
      const mp4 = path.join(scenesDir, `scene_${String(i).padStart(2,"0")}.mp4`);
      await renderFrames(htmlPaths[i], fd, 30, Math.round(dur));
      framesToVideo(fd, mp4, 30);
    }
  }
  console.log(`[Three.js] ✅ Done: ${scenesDir}`);
}

(async () => {
  try {
    if (useAll) {
      await runRemotionPipeline();
      await runThreeJsPipeline();
      await runManimPipeline();
    } else if (useRemot)  {
      await runRemotionPipeline();
    } else if (useThree) {
      await runThreeJsPipeline();
    } else {
      await runManimPipeline();
    }
    console.log(`\n${"═".repeat(60)}`);
    console.log(`  ✅ ALL DONE — outputs in: ${path.resolve(outDir)}`);
    console.log(`${"═".repeat(60)}\n`);
  } catch(e) {
    console.error("[ERROR]", e.message);
    process.exit(1);
  }
})();