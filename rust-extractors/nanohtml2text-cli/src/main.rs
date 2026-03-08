use nanohtml2text::html2text;
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

    // Extract all text from HTML
    let content = html2text(&html);

    // nanohtml2text extracts ALL text, no title/author extraction
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
