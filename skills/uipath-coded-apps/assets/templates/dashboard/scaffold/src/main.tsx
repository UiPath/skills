import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { installFetchCache } from './lib/fetch-cache'

// Dedupe + briefly cache identical GET requests so many widgets mounting at once
// don't hammer the same API endpoint into a 429. Must run before the app renders.
installFetchCache()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
