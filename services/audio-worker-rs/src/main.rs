#[tokio::main(flavor = "current_thread")]
async fn main() {
    let (_tx, rx) = tokio::sync::mpsc::channel(8);
    audio_worker_rs::worker::run(rx).await;
}
