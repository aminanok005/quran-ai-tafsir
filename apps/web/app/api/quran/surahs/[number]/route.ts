import { forwardBackendRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function GET(
  request: Request,
  { params }: { params: { number: string } },
) {
  const number = Number(params.number);
  if (!Number.isInteger(number) || number < 1 || number > 114) {
    return Response.json({ detail: "Surah number must be between 1 and 114" }, { status: 422 });
  }

  const edition = new URL(request.url).searchParams.get("edition") ?? "quran-uthmani";
  if (!["quran-uthmani", "th.thai", "ar.alafasy", "qpc-v4"].includes(edition)) {
    return Response.json({ detail: "Unsupported Quran edition" }, { status: 422 });
  }

  return forwardBackendRequest(
    `/api/v1/quran/surahs/${number}?edition=${encodeURIComponent(edition)}`,
  );
}
