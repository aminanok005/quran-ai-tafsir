import { forwardBackendRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: { number: string } },
) {
  const number = Number(params.number);
  if (!Number.isInteger(number) || number < 1 || number > 114) {
    return Response.json({ detail: "Surah number must be between 1 and 114" }, { status: 422 });
  }

  return forwardBackendRequest(`/api/v1/quran/surahs/${number}/info`);
}
