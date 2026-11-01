import { forwardQuranRequest } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export function GET() {
  return forwardQuranRequest("/surah");
}
