<!--skill-flavor:host-base-files:start-->
## Studio Web base files

Studio Web cannot run `create-vite`, so write this `package.json` yourself, plus the `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` and `index.html` both app types share from [web-app-template.md](web-app-template.md) § Studio Web base files. Paths are relative to the app's `source/` folder. Keep the version ranges, and do not add a `package-lock.json`. Replace `{{APP_NAME}}` with the app name.

### `package.json`

```json
{
  "name": "{{APP_NAME}}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@uipath/coded-action-app": "^1.0.0",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@types/node": "^24.13.3",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^6.1.1",
    "typescript": "~6.0.2",
    "vite": "^8.3.0"
  }
}
```

Add `"@uipath/uipath-typescript": "^1.8.1"` to `dependencies` only when the app calls SDK services, and `"react-pdf": "^11.0.0"` only when it shows a PDF.

---

<!--skill-flavor:host-base-files:end-->
