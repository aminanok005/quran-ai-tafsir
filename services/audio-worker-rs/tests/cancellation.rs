use audio_worker_rs::{
    protocol::{AudioJob, AudioResult},
    worker::{process_job, run},
};

#[tokio::test]
async fn bounded_queue_rejects_after_capacity() {
    let (tx, _rx) = tokio::sync::mpsc::channel(1);
    let job = AudioJob {
        version: 1,
        job_id: "1".into(),
        source_format: "mp3".into(),
        target_format: "mp3".into(),
        bytes_limit: 1,
    };
    let (reply, _wait) = tokio::sync::oneshot::channel::<AudioResult>();
    tx.send((job.clone(), reply)).await.unwrap();
    let (reply2, _wait2) = tokio::sync::oneshot::channel::<AudioResult>();
    assert!(tx.try_send((job, reply2)).is_err());
}

#[tokio::test]
async fn worker_stops_after_all_senders_close() {
    let (tx, rx) = tokio::sync::mpsc::channel(1);
    drop(tx);
    assert!(
        tokio::time::timeout(std::time::Duration::from_millis(50), run(rx))
            .await
            .is_ok()
    );
}

#[test]
fn malformed_job_fails_closed() {
    let result = process_job(AudioJob {
        version: 1,
        job_id: String::new(),
        source_format: "mp3".into(),
        target_format: "mp3".into(),
        bytes_limit: 1,
    });
    assert_eq!(result.error_code, Some("malformed_job"));
}

#[test]
fn unsupported_codec_fails_closed() {
    let result = process_job(AudioJob {
        version: 1,
        job_id: "1".into(),
        source_format: "opus".into(),
        target_format: "mp3".into(),
        bytes_limit: 1,
    });
    assert_eq!(result.error_code, Some("codec_unavailable"));
}

#[test]
fn zero_limit_fails_closed() {
    let result = process_job(AudioJob {
        version: 1,
        job_id: "1".into(),
        source_format: "mp3".into(),
        target_format: "mp3".into(),
        bytes_limit: 0,
    });
    assert_eq!(result.error_code, Some("invalid_bytes_limit"));
}

#[test]
fn unsupported_version_fails_closed() {
    let result = process_job(AudioJob {
        version: 2,
        job_id: "1".into(),
        source_format: "mp3".into(),
        target_format: "mp3".into(),
        bytes_limit: 1,
    });
    assert_eq!(result.error_code, Some("unsupported_version"));
}
