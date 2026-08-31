const versions = (env: Env): Readonly<Record<string, string>> => ({
  "/llms.txt": env.LLMS_VERSION,
  "/llms-full.txt": env.LLMS_FULL_VERSION,
});

export default {
  async fetch(request, env): Promise<Response> {
    const incoming = new URL(request.url);
    const version = versions(env)[incoming.pathname];
    if (
      version
      && request.method !== "GET"
      && request.method !== "HEAD"
    ) {
      return new Response("Method not allowed.", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    }

    const upstream = new URL(
      `${incoming.pathname}${incoming.search}`,
      env.MINTLIFY_ORIGIN,
    );
    if (version) upstream.searchParams.set("relay_source", version);
    const response = await fetch(new Request(upstream, request));
    const headers = new Headers(response.headers);
    if (version) {
      headers.set("Cache-Control", "no-store, max-age=0");
      headers.set("X-Relay-Docs-Source", version);
      headers.delete("Age");
    }
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
