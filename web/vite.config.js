import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  base: "/amx-26/",
  plugins: [viteSingleFile()],
  build: {
    outDir: "../docs",
    emptyOutDir: true,
    assetsInlineLimit: 100000000
  }
});
