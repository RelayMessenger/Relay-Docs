const versions = (env: Env): Readonly<Record<string, string>> => ({
  "/llms.txt": env.LLMS_VERSION,
  "/llms-full.txt": env.LLMS_FULL_VERSION,
});

export default {
  async fetch(request, env): Promise<Response> {
    const incoming = new URL(request.url);
    const version = versions(env)[incoming.pathname];
    if (!version) return new Response("Not found.", { status: 404 });
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed.", {
        status: 405,
        headers: { Allow: "GET, HEAD" },
      });
    }

    const upstream = new URL(incoming.pathname, env.MINTLIFY_ORIGIN);
    upstream.searchParams.set("relay_source", version);
    const response = await fetch(upstream, {
      headers: { Accept: "text/plain" },
      redirect: "manual",
    });
    const headers = new Headers(response.headers);
    headers.set("Cache-Control", "no-store, max-age=0");
    headers.set("X-Relay-Docs-Source", version);
    headers.delete("Age");
    headers.delete("Set-Cookie");
    return new Response(request.method === "HEAD" ? null : response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
} satisfies ExportedHandler<Env>;
