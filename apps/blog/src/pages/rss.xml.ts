import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import YukinaConfig from "../../yukina.config";

export async function GET(context: { site: string }) {
  const posts = await getCollection("posts");
  return rss({
    title: YukinaConfig.title,
    description: YukinaConfig.description,
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.published,
    })),
  });
}
