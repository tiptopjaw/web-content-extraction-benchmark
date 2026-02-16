# Future Extractor Considerations

## LLM-based Extractors

### Schematron:3B (Ollama)
- **Model**: Llama 3.2-3B fine-tuned for HTML→JSON extraction
- **Availability**: Available on Ollama (`ollama pull schematron:3b`)
- **Approach**: Takes JSON Schema + HTML, returns structured JSON
- **Pros**: Flexible, can adapt to any schema without code changes
- **Cons**: Slower (requires LLM inference), needs GPU/CPU resources

To add to benchmark:
1. Install Ollama and pull model
2. Create wrapper extractor that sends HTML + schema to Ollama
3. Define schema matching GT format (title, main_content)

This would provide an interesting "apples to oranges" comparison between traditional rule-based extractors and LLM-based approaches.
