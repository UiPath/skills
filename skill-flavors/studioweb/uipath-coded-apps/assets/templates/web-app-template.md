<!--skill-flavor:host-base-files:start-->
## Studio Web base files

Studio Web cannot run `create-vite`, so write these files yourself: they are what `create-vite --template react-ts` generates, without its demo assets and linter. Paths are relative to the app's `source/` folder. The version ranges are the ones `create-vite` and the CLI install steps write — keep them, and do not add a `package-lock.json`. Replace `{{APP_NAME}}` with the app name.

### `package.json` — Coded Web App

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
    "@uipath/uipath-typescript": "^1.8.1",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.3.3",
    "@types/node": "^24.13.3",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@uipath/coded-apps-dev": "^1.0.0-beta.1",
    "@vitejs/plugin-react": "^6.1.1",
    "autoprefixer": "^10.6.1",
    "postcss": "^8.5.30",
    "tailwindcss": "^4.3.3",
    "typescript": "~6.0.2",
    "vite": "^8.3.0"
  }
}
```

On `default styling = yes`, add to `dependencies`: `"@uipath/apollo-core": "^5.15.1"`, `"@uipath/apollo-wind": "^2.68.0"`, `"lucide-react": "^1.56.0"`, `"next-themes": "^0.4.6"`.

### `package.json` — Coded Action App

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

### `tsconfig.json`

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

### `tsconfig.app.json`

`"types": ["vite/client"]` declares `.css`, `.svg` and other asset imports. Without it, `tsc -b` rejects `import './index.css'` with TS2882.

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023", "DOM"],
    "module": "esnext",
    "types": ["vite/client"],
    "allowArbitraryExtensions": true,
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

### `tsconfig.node.json`

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "es2023",
    "lib": ["ES2023"],
    "types": ["node"],
    "skipLibCheck": true,

    /* Bundler mode */
    "module": "nodenext",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

### `index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{APP_NAME}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `src/main.tsx` (Q6 = no)

The Coded Web App's `default styling = no` path. The Q6 = yes path and the action app take `src/main.tsx` from their own template section.

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

No `.gitignore` is needed: Studio Web has no git working tree and no `.uipath/` directory, so skip the `.gitignore` step.

### Build checklist

Nothing builds the app in Studio Web, and its first `tsc -b` enforces the `tsconfig.app.json` above. Before handing the app over, check every file under `source/`:

1. `tsconfig.app.json` keeps `"types": ["vite/client"]`.
2. Each relative import resolves to a file you wrote, and each package import is listed in `package.json`.
3. Type-only imports use `import type` (`verbatimModuleSyntax`).
4. No local, parameter or import goes unused (`noUnusedLocals`, `noUnusedParameters`).
5. No `enum`, `namespace` or constructor parameter property (`erasableSyntaxOnly`).
6. No `switch` case falls through (`noFallthroughCasesInSwitch`).

---

<!--skill-flavor:host-base-files:end-->
