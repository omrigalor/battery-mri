// Static build for hosting on omrigalor.com (no FastAPI backend).
// Leaves src/ untouched: the API calls are rewritten at build time and the
// Lab-mode entry point (which needs the live solver) is dropped.
import { defineConfig } from 'vite'

const staticApi = {
  name: 'static-api',
  enforce: 'pre' as const,
  transform(code: string, id: string) {
    if (!/App\.tsx$/.test(id)) return null
    console.log('[static-api] transforming', id)
    return code
      .replace("fetch('/api/demo')", "fetch(import.meta.env.BASE_URL+'data/demo.json')")
      .replace("fetch('/api/demo/result')", "fetch(import.meta.env.BASE_URL+'data/result.json')")
      .replace("<button onClick={()=>{setLab(!lab);setPaused(true)}}>Lab mode</button>", "")
  },
}

export default defineConfig({
  base: '/battery-mri/',
  plugins: [staticApi],
  build: { outDir: 'dist-static', emptyOutDir: true },
})
