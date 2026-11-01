import { forwardBackendRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: { number: string } },
) {
  const number = Number(params.number);
  if (!Number.isInteger(number) || number < 1 || number > 604) {
    return Response.json({ detail: "Page number must be between 1 and 604" }, { status: 422 });
  }

  return forwardBackendRequest(`/api/v1/quran/mushaf/15-line/pages/${number}`);
}
