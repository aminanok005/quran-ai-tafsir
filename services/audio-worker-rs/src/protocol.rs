#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AudioJob {
    pub version: u8,
    pub job_id: String,
    pub source_format: String,
    pub target_format: String,
    pub bytes_limit: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AudioResult {
    pub version: u8,
    pub job_id: String,
    pub status: &'static str,
    pub output_format: Option<String>,
    pub byte_length: usize,
    pub error_code: Option<&'static str>,
}
