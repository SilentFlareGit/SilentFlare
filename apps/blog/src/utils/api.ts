export interface ApiPost {
  id: number;
  title: string;
  slug: string;
  summary: string;
  cover_url: string;
  category: string;
  tags: string[];
  published_at: string;
  content_markdown?: string;
}

const API_BASE = "http://127.0.0.1:8000/api/v1";

export async function fetchApiPosts(): Promise<ApiPost[]> {
  try {
    const res = await fetch(`${API_BASE}/posts`, { signal: AbortSignal.timeout(2000) });
    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    const data = await res.json();
    return data.items || [];
  } catch (e) {
    console.warn("Failed to fetch posts from backend mock API, falling back to local posts.", e);
    return [];
  }
}

export async function fetchApiPostBySlug(slug: string): Promise<ApiPost | null> {
  try {
    const res = await fetch(`${API_BASE}/posts/${slug}`, { signal: AbortSignal.timeout(2000) });
    if (!res.ok) {
      if (res.status === 404) return null;
      throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.warn(`Failed to fetch post detail for slug ${slug} from backend mock API.`, e);
    return null;
  }
}

export function renderMarkdown(md: string): string {
  if (!md) return "";
  return md
    .replace(/^# (.*$)/gim, '<h1 class="text-3xl font-bold my-4">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold my-3">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 class="text-xl font-bold my-2">$1</h3>')
    .replace(/^\* (.*$)/gim, '<li class="list-disc ml-5">$1</li>')
    .replace(/^- (.*$)/gim, '<li class="list-disc ml-5">$1</li>')
    .split('\n\n')
    .map(para => {
      if (para.trim().startsWith('<h') || para.trim().startsWith('<li')) {
        return para;
      }
      return `<p class="my-2">${para.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('\n');
}
