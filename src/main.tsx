import { StrictMode } from 'react';

import { createRoot } from 'react-dom/client';
import { HelmetProvider } from 'react-helmet-async';

import App from './App.tsx';
import './i18n';
import './fonts.css';
import './index.css';

// index.html carries default title/description/Open Graph tags for crawlers
// that do not run JavaScript. Once the app runs, the SEO component owns them.
document
  .querySelectorAll('head [data-static-seo]')
  .forEach(element => element.remove());

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HelmetProvider>
      <App />
    </HelmetProvider>
  </StrictMode>
);
