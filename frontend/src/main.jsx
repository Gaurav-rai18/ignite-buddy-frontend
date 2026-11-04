/**
 * @file main.jsx
 * @description Application entry point. Mounts the React app into the DOM.
 *
 * Wraps the root <App /> component with:
 *   - React.StrictMode for development warnings.
 *   - BrowserRouter for client-side routing.
 *
 * The root DOM element (#root) is defined in index.html.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './app/App';
import './styles.css';

const rootElement = document.getElementById('root');

if (rootElement) {
  createRoot(rootElement).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>
  );
}
