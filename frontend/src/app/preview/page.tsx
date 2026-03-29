"use client";
import { Player } from "@remotion/player";
import { DynamicScene } from "../../remotion/DynamicScene";
import Link from "next/link";

export default function PreviewPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-5xl">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Programmatic Remotion Preview</h1>
          <Link href="/" className="px-5 py-2.5 bg-slate-800 text-sm font-medium rounded-xl hover:bg-slate-700 transition-all border border-slate-700">
            &larr; Back to Generator
          </Link>
        </div>
        
        <div className="rounded-2xl overflow-hidden shadow-2xl shadow-indigo-500/20 border border-slate-800 bg-slate-900 aspect-video">
          <Player
            component={DynamicScene}
            durationInFrames={300} // 10 seconds at 30fps
            compositionWidth={1920}
            compositionHeight={1080}
            fps={30}
            controls
            style={{ width: "100%", height: "100%" }}
            inputProps={{
              title: "Dynamic AI SaaS Template",
              scenes: [{ 
                id: 1, 
                text: "Waiting for the backend JSON payload (in production, we fetch Job ID data here)...", 
                threejs_props: { color: "#8b5cf6" } 
              }],
              audioUrl: undefined
            }}
          />
        </div>
        
        <p className="text-slate-400 mt-6 text-center max-w-2xl mx-auto">
          This preview player mounts React components and Three.js scenes directly in the browser. Using Remotion's Lambda services, you could also render this to a cloud MP4 in the background!
        </p>
      </div>
    </main>
  );
}
