// The crate is named fast_html2md but exports as html2md
use html2md::parse_html;
use serde::Serialize;
use std::io::{self, Read};

#[derive(Serialize)]
struct Output {
    title: Option<String>,
    author: Option<String>,
    date: Option<String>,
    main_content: String,
}

fn main() {
    let mut html = String::new();
    if let Err(e) = io::stdin().read_to_string(&mut html) {
        eprintln!("Error reading stdin: {}", e);
        print_empty_output();
        return;
    }

    // Convert HTML to Markdown (false = don't include URLs inline)
    let content = parse_html(&html, false);

    // fast_html2md extracts ALL content as markdown, no title/author extraction
    let output = Output {
        title: None,
        author: None,
        date: None,
        main_content: content,
    };

    println!("{}", serde_json::to_string(&output).unwrap());
}

fn print_empty_output() {
    let output = Output {
        title: None,
        author: None,
        date: None,
        main_content: String::new(),
    };
    println!("{}", serde_json::to_string(&output).unwrap());
}
