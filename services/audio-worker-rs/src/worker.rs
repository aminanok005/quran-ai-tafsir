use crate::protocol::{AudioJob, AudioResult};
use tokio::sync::{mpsc, oneshot};

pub async fn run(mut jobs: mpsc::Receiver<(AudioJob, oneshot::Sender<AudioResult>)>) {
    while let Some((job, reply)) = jobs.recv().await {
        let result = process_job(job);
        let _ = reply.send(result);
    }
}

pub fn process_job(job: AudioJob) -> AudioResult {
    if job.version != 1 {
        return AudioResult {
            version: 1,
            job_id: job.job_id,
            status: "error",
            output_format: None,
            byte_length: 0,
            error_code: Some("unsupported_version"),
        };
    }
    if job.job_id.is_empty() || job.source_format.is_empty() || job.target_format.is_empty() {
        return AudioResult {
            version: 1,
            job_id: job.job_id,
            status: "error",
            output_format: None,
            byte_length: 0,
            error_code: Some("malformed_job"),
        };
    }
    if job.bytes_limit == 0 {
        AudioResult {
            version: 1,
            job_id: job.job_id,
            status: "error",
            output_format: None,
            byte_length: 0,
            error_code: Some("invalid_bytes_limit"),
        }
    } else if job.source_format != job.target_format {
        AudioResult {
            version: 1,
            job_id: job.job_id,
            status: "error",
            output_format: None,
            byte_length: 0,
            error_code: Some("codec_unavailable"),
        }
    } else {
        AudioResult {
            version: 1,
            job_id: job.job_id,
            status: "ok",
            output_format: Some(job.target_format),
            byte_length: 0,
            error_code: None,
        }
    }
}
