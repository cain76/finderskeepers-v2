import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// Entry point for the redesigned FindersKeepers v2 frontend.  We use
// ReactDOM.createRoot here to enable concurrent rendering. The
// <React.StrictMode> wrapper helps catch common mistakes and ensures
// components are resilient against future React releases.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);