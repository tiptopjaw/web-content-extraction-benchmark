use dom_smoothie::Readability;
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

    let result = extract_content(&html);

    let output = match result {
        Ok((title, author, content)) => Output {
            title,
            author,
            date: None,
            main_content: content,
        },
        Err(e) => {
            eprintln!("Error extracting content: {}", e);
            Output {
                title: None,
                author: None,
                date: None,
                main_content: String::new(),
            }
        }
    };

    println!("{}", serde_json::to_string(&output).unwrap());
}

fn extract_content(html: &str) -> Result<(Option<String>, Option<String>, String), Box<dyn std::error::Error>> {
    // Readability::new takes (html, url, config)
    let mut readability = Readability::new(html, None, None)?;
    let article = readability.parse()?;

    // title is a String, not Option<String>
    let title = if article.title.is_empty() {
        None
    } else {
        Some(article.title)
    };

    // byline may be Option<String> or String - handle both
    let author = article.byline.filter(|s| !s.is_empty());

    // text_content is a Tendril, convert to String
    let content = article.text_content.to_string();

    Ok((title, author, content))
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
