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

export async function forwardQuranRequest(path: string): Promise<Response> {
  try {
    const upstream = await fetch(`https://api.alquran.cloud/v1${path}`, {
      next: { revalidate: 86_400 },
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(15_000),
    });
    const body = await upstream.text();
    try {
      return Response.json(JSON.parse(body), {
        status: upstream.ok ? 200 : upstream.status,
        headers: {
          "Cache-Control": upstream.ok
            ? "public, s-maxage=86400, stale-while-revalidate=3600"
            : "no-store",
        },
      });
    } catch {
      return Response.json(
        { detail: "Quran text provider returned an invalid response" },
        { status: 502, headers: { "Cache-Control": "no-store" } },
      );
    }
  } catch (error) {
    const detail =
      error instanceof Error && error.name === "TimeoutError"
        ? "Quran text request timed out"
        : "Could not reach the Quran text provider";
    return Response.json({ detail }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
