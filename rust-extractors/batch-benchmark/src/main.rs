/// Batch benchmark for Rust extractors
/// Processes all gzipped HTML files in a directory and outputs timing
use dom_content_extraction::{DensityTree, scraper::Html};
use dom_smoothie::Readability;
use flate2::read::GzDecoder;
use serde_json::json;
use std::collections::HashMap;
use std::env;
use std::fs::{self, File};
use std::io::Read;
use std::time::Instant;

fn extract_with_dom_smoothie(html: &str) -> String {
    match Readability::new(html, None, None) {
        Ok(mut readability) => match readability.parse() {
            Ok(article) => article.text_content.to_string(),
            Err(_) => String::new(),
        },
        Err(_) => String::new(),
    }
}

fn extract_with_dom_content_extraction(html: &str) -> String {
    let document = Html::parse_document(html);
    match DensityTree::from_document(&document) {
        Ok(mut dtree) => {
            if dtree.calculate_density_sum().is_err() {
                return String::new();
            }
            dtree.extract_content(&document).unwrap_or_default()
        }
        Err(_) => String::new(),
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: batch-benchmark <extractor> [html_dir] [output_file]");
        eprintln!("Extractors: dom-smoothie, dom-content-extraction");
        std::process::exit(1);
    }

    let extractor = &args[1];
    let html_dir = if args.len() > 2 { &args[2] } else { "html" };
    let output_file = if args.len() > 3 {
        args[3].clone()
    } else {
        format!("output/{}-batch.json", extractor)
    };

    // Find all .html.gz files
    let mut files: Vec<_> = fs::read_dir(html_dir)?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().to_string_lossy().ends_with(".html.gz"))
        .collect();
    files.sort_by_key(|e| e.path());

    eprintln!("Processing {} files with {}...", files.len(), extractor);

    let mut results: HashMap<String, serde_json::Value> = HashMap::new();
    let start = Instant::now();

    for (i, entry) in files.iter().enumerate() {
        let path = entry.path();
        let file_id = path
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("")
            .trim_end_matches(".html")
            .to_string();

        // Read and decompress
        let file = File::open(&path)?;
        let mut decoder = GzDecoder::new(file);
        let mut html = String::new();
        decoder.read_to_string(&mut html)?;

        // Extract based on chosen extractor
        let content = match extractor.as_str() {
            "dom-smoothie" => extract_with_dom_smoothie(&html),
            "dom-content-extraction" => extract_with_dom_content_extraction(&html),
            _ => {
                eprintln!("Unknown extractor: {}", extractor);
                std::process::exit(1);
            }
        };

        results.insert(file_id, json!({"articleBody": content}));

        if (i + 1) % 200 == 0 {
            eprintln!(
                "  Processed {}/{} files ({:.1}s)",
                i + 1,
                files.len(),
                start.elapsed().as_secs_f64()
            );
        }
    }

    let elapsed = start.elapsed();
    eprintln!(
        "\n{}: {:.2} seconds for {} files",
        extractor,
        elapsed.as_secs_f64(),
        results.len()
    );
    eprintln!(
        "  ({:.1} ms per file)",
        elapsed.as_secs_f64() * 1000.0 / results.len() as f64
    );

    // Write results
    let output = serde_json::to_string(&results)?;
    fs::write(&output_file, output)?;
    eprintln!("  Results saved to {}", output_file);

    Ok(())
}
