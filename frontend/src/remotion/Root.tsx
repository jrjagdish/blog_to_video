import React from "react";
import { Composition } from "remotion";
import { DynamicScene, myCompSchema } from "./DynamicScene";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DynamicVideoScene"
        component={DynamicScene}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        schema={myCompSchema}
        defaultProps={{
          title: "Dynamic AI Video",
          scenes: [
            {
              id: 1,
              text: "Generating...",
              duration: 10,
              threejs_props: { text: "AI Gen", color: "#ffffff" }
            }
          ]
        }}
      />
    </>
  );
};
