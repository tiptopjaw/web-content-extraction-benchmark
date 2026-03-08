use dom_content_extraction::{DensityTree, scraper::Html};
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

    let document = Html::parse_document(&html);

    let content = match extract_content(&document) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Error extracting content: {}", e);
            String::new()
        }
    };

    // Try to extract title from <title> tag
    let title = document
        .select(&dom_content_extraction::scraper::Selector::parse("title").unwrap())
        .next()
        .map(|el| el.text().collect::<String>().trim().to_string())
        .filter(|s| !s.is_empty());

    let output = Output {
        title,
        author: None,
        date: None,
        main_content: content,
    };

    println!("{}", serde_json::to_string(&output).unwrap());
}

fn extract_content(document: &Html) -> Result<String, Box<dyn std::error::Error>> {
    let mut dtree = DensityTree::from_document(document)?;
    dtree.calculate_density_sum()?;
    let content = dtree.extract_content(document)?;
    Ok(content)
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
