/** Prefix a site-absolute path ("/media/x.mp4") with the Vite base URL so the
 *  page works both at "/" and under a GitHub Pages project path
 *  such as "/AgenticGRAIL/". */
export function asset(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return base + (path.startsWith('/') ? path : '/' + path);
}
