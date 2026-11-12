# Audio Worker Spike

Optional bounded async worker. Protocol carries job IDs and safe error codes only. It does not process Quran text, Tafsir, citations, provider credentials, or device audio. Production integration waits for codec need, licensing, benchmark, and ownership approval.

Protocol version `1` requires `job_id`, `source_format`, `target_format`, and positive `bytes_limit`. Unsupported versions, malformed jobs, zero limits, and unavailable codecs fail closed with deterministic codes.
