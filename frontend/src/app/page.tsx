"use client";
import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [format, setFormat] = useState("manim");
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setVideoUrl(null);
    setStatusText("Initializing job...");
    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, format })
      });
      const data = await res.json();
      
      let status = data.status;
      let job_id = data.id;
      
      while (status !== "completed" && status !== "failed") {
        await new Promise(r => setTimeout(r, 2000));
        const check = await fetch(`http://localhost:8000/status/${job_id}`);
        const checkData = await check.json();
        status = checkData.status;
        setStatusText(status.replace(/_/g, " "));
        
        if (status === "completed") {
           setVideoUrl(checkData.video_url);
        } else if (status === "failed") {
           setStatusText(`Failed: ${checkData.error}`);
        }
      }
    } catch (e: any) {
      setStatusText(`Connection Error: ${e.message}`);
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 overflow-hidden">
      <div className="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-indigo-500/10 to-transparent pointer-events-none blur-3xl"></div>
      
      <div className="relative max-w-5xl mx-auto px-6 py-24 flex flex-col items-center">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400 mb-6 text-center">
          AI Video Architect
        </h1>
        <p className="text-lg md:text-xl text-slate-400 mb-12 text-center max-w-2xl">
          Programmatically generate manim educational explainers, highly dynamic 3D web animations, and realistic motion overlays.
        </p>

        <div className="w-full max-w-3xl p-8 rounded-3xl bg-slate-900/40 backdrop-blur-xl border border-slate-800 shadow-2xl relative">
          <textarea 
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Describe your video idea (e.g., 'Explain Quantum Computing using doodle animations')"
            className="w-full h-32 bg-slate-950/50 border border-slate-800/80 rounded-2xl p-5 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none mb-6 text-lg"
          />
          
          <div className="flex flex-col md:flex-row gap-6 items-center justify-between mb-4">
            <div className="flex gap-3 bg-slate-950/50 p-2 rounded-2xl border border-slate-800/50">
              {['manim', '3d', 'motion'].map(f => (
                <button 
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-5 py-2.5 rounded-xl text-sm font-bold tracking-wide transition-all ${format === f ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/25' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
            
            <button 
              onClick={handleGenerate}
              disabled={loading || !prompt}
              className="px-8 py-3.5 bg-white text-slate-950 rounded-xl font-bold hover:bg-slate-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3 shadow-xl shadow-white/10"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {statusText || 'Starting...'}
                </span>
              ) : 'Generate Video'}
            </button>
          </div>

          {!loading && statusText && !videoUrl && (
            <p className="text-center text-rose-400 mt-4 text-sm font-medium">{statusText}</p>
          )}

          {videoUrl && (
            <div className="mt-8 pt-8 border-t border-slate-800/50 animate-in fade-in slide-in-from-bottom-4 duration-500">
               {format === 'manim' ? (
                 <video src={`http://localhost:8000${videoUrl}`} controls autoPlay className="w-full rounded-2xl shadow-2xl border border-slate-800" />
               ) : (
                 <div className="p-8 text-center bg-gradient-to-br from-indigo-500/10 to-purple-500/10 rounded-2xl border border-indigo-500/20 backdrop-blur-md">
                    <p className="text-indigo-300 font-bold text-lg mb-2">Remotion 3D Scene Generated Data Ready</p>
                    <p className="text-sm text-slate-400">Audio saved at {videoUrl}. Proceed to the `/preview` route to view programmatic React rendering.</p>
                 </div>
               )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
