const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

function backendUrl(path: string): string {
  const baseUrl = (process.env.TAFSIR_API_URL ?? DEFAULT_BACKEND_URL).replace(
    /\/+$/,
    "",
  );
  return `${baseUrl}${path}`;
}

export async function forwardBackendRequest(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  let upstream: Response;
  try {
    upstream = await fetch(backendUrl(path), {
      ...init,
      cache: "no-store",
      signal: AbortSignal.timeout(50_000),
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
      },
    });
  } catch (error) {
    const detail =
      error instanceof Error && error.name === "TimeoutError"
        ? "Backend request timed out"
        : "Could not reach the tafsir backend";
    return Response.json({ detail }, { status: 503 });
  }

  const body = await upstream.text();
  try {
    return Response.json(JSON.parse(body), { status: upstream.status });
  } catch {
    return Response.json(
      { detail: "Tafsir backend returned an invalid response" },
      { status: 502 },
    );
  }
}
