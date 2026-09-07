import llms from "../../../llms.txt";
import llmsFull from "../../../llms-full.txt";

const documents = (env: Env) => ({
  "/llms.txt": {
    body: llms,
    version: env.LLMS_VERSION,
  },
  "/llms-full.txt": {
    body: llmsFull,
    version: env.LLMS_FULL_VERSION,
  },
});

export default {
  async fetch(request, env): Promise<Response> {
    const incoming = new URL(request.url);
    const document = documents(env)[
      incoming.pathname as keyof ReturnType<typeof documents>
    ];
    if (document && request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed.", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    }
    if (document) {
      return new Response(request.method === "HEAD" ? null : document.body, {
        headers: {
          "Cache-Control": "no-store, max-age=0",
          "Content-Type": "text/plain; charset=utf-8",
          "X-Relay-Docs-Proxy": "cloudflare-staging",
          "X-Relay-Docs-Source": document.version,
        },
      });
    }

    const upstream = new URL(
      `${incoming.pathname}${incoming.search}`,
      env.MINTLIFY_ORIGIN,
    );
    const response = await fetch(new Request(upstream, request));
    const headers = new Headers(response.headers);
    headers.set("X-Relay-Docs-Proxy", "cloudflare-staging");
    headers.delete("Set-Cookie");
    return new Response(
      request.method === "HEAD" ? null : response.body,
      {
      status: response.status,
      statusText: response.statusText,
      headers,
      },
    );
  },
} satisfies ExportedHandler<Env>;
