import { forwardBackendRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (contentLength > 64_000) {
    return Response.json({ detail: "Request body is too large" }, { status: 413 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ detail: "Request body must be valid JSON" }, { status: 400 });
  }

  return forwardBackendRequest("/api/v1/tafsir/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
