package main

import (
	"compress/gzip"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/go-shiori/go-readability"
	"github.com/markusmobius/go-trafilatura"
)

type Result struct {
	ArticleBody string `json:"articleBody"`
}

func extractWithTrafilatura(html string) string {
	result, err := trafilatura.Extract(strings.NewReader(html), trafilatura.Options{})
	if err != nil || result == nil {
		return ""
	}
	return result.ContentText
}

func extractWithReadability(html string, url string) string {
	article, err := readability.FromReader(strings.NewReader(html), nil)
	if err != nil {
		return ""
	}
	return article.TextContent
}

func processFile(htmlPath string, extractor string) (string, string, error) {
	// Get file ID from path
	base := filepath.Base(htmlPath)
	fileID := strings.TrimSuffix(strings.TrimSuffix(base, ".gz"), ".html")

	// Open gzipped file
	f, err := os.Open(htmlPath)
	if err != nil {
		return fileID, "", err
	}
	defer f.Close()

	gz, err := gzip.NewReader(f)
	if err != nil {
		return fileID, "", err
	}
	defer gz.Close()

	htmlBytes, err := io.ReadAll(gz)
	if err != nil {
		return fileID, "", err
	}

	html := string(htmlBytes)

	var content string
	switch extractor {
	case "go-trafilatura":
		content = extractWithTrafilatura(html)
	case "go-readability":
		content = extractWithReadability(html, "")
	default:
		return fileID, "", fmt.Errorf("unknown extractor: %s", extractor)
	}

	return fileID, content, nil
}

func main() {
	extractor := flag.String("extractor", "go-trafilatura", "Extractor to use: go-trafilatura or go-readability")
	htmlDir := flag.String("html", "html", "Directory containing HTML files")
	output := flag.String("output", "", "Output JSON file")
	workers := flag.Int("workers", 8, "Number of parallel workers")
	flag.Parse()

	if *output == "" {
		*output = fmt.Sprintf("output/%s.json", *extractor)
	}

	// Find all HTML files
	files, err := filepath.Glob(filepath.Join(*htmlDir, "*.html.gz"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error finding files: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Processing %d files with %s...\n", len(files), *extractor)
	start := time.Now()

	// Process files in parallel
	results := make(map[string]Result)
	var mu sync.Mutex
	var wg sync.WaitGroup

	// Create worker pool
	fileChan := make(chan string, len(files))
	for _, f := range files {
		fileChan <- f
	}
	close(fileChan)

	// Progress tracking
	processed := 0
	var progressMu sync.Mutex

	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for htmlPath := range fileChan {
				fileID, content, err := processFile(htmlPath, *extractor)
				if err != nil {
					fmt.Fprintf(os.Stderr, "Error processing %s: %v\n", fileID, err)
				}

				mu.Lock()
				results[fileID] = Result{ArticleBody: content}
				mu.Unlock()

				progressMu.Lock()
				processed++
				if processed%100 == 0 {
					fmt.Printf("Processed %d/%d files...\n", processed, len(files))
				}
				progressMu.Unlock()
			}
		}()
	}

	wg.Wait()

	// Write results
	outFile, err := os.Create(*output)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating output file: %v\n", err)
		os.Exit(1)
	}
	defer outFile.Close()

	encoder := json.NewEncoder(outFile)
	encoder.SetIndent("", "  ")
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(results); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing JSON: %v\n", err)
		os.Exit(1)
	}

	elapsed := time.Since(start)
	fmt.Printf("Done! Processed %d files in %v\n", len(results), elapsed)
	fmt.Printf("Results saved to %s\n", *output)
}
