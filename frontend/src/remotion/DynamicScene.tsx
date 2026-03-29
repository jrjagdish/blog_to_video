import React from "react";
import { AbsoluteFill, useVideoConfig, useCurrentFrame, Audio } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { z } from "zod";
import { Text3D, Center, Float, Environment } from "@react-three/drei";

export const myCompSchema = z.object({
  title: z.string(),
  scenes: z.array(z.any()),
  audioUrl: z.string().optional()
});

export const DynamicScene: React.FC<z.infer<typeof myCompSchema>> = ({
  title,
  scenes,
  audioUrl
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  // Basic timeline logic based on scenes
  // In a real SaaS, we calculate current scene by aggregating durations
  
  return (
    <AbsoluteFill className="bg-slate-950 flex items-center justify-center relative overflow-hidden">
      {audioUrl && <Audio src={audioUrl} />}
      
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/50 to-purple-900/50 opacity-50"></div>
      
      <ThreeCanvas width={1920} height={1080}>
        <Environment preset="city" />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
           {/* Fallback to simple mesh if Text3D font not loaded, using basic Drei box for now */}
           <mesh rotation={[frame * 0.01, frame * 0.02, 0]}>
             <boxGeometry args={[3, 3, 3]} />
             <meshStandardMaterial color={scenes[0]?.threejs_props?.color || "#6366f1"} wireframe />
           </mesh>
        </Float>
      </ThreeCanvas>
      
      <div className="absolute bottom-24 w-full text-center">
         <h1 className="text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
           {title}
         </h1>
         <p className="text-3xl text-slate-300 mt-6 font-medium bg-slate-900/50 p-6 inline-block rounded-3xl backdrop-blur-md">
           {scenes[0]?.text || "Loading scene data..."}
         </p>
      </div>
    </AbsoluteFill>
  );
};
