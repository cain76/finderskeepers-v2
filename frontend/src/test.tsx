import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

function SimpleApp() {
  return <div style={{padding: '20px', fontSize: '24px'}}>Hello from React!</div>
}

const rootElement = document.getElementById('root')
if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <SimpleApp />
    </StrictMode>
  )
} else {
  console.error('Root element not found!')
}