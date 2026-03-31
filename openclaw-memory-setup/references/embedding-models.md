# Embedding Models Reference

## Local Models (Ollama)

| Model | Dimensions | Size | Speed | Quality | Best For |
|-------|-----------|------|-------|---------|----------|
| `nomic-embed-text` | 768 | 275MB | Fast | Good | General purpose, English |
| `mxbai-embed-large` | 1024 | 670MB | Medium | Better | Multi-language, longer contexts |
| `all-minilm` | 384 | 23MB | Very Fast | Basic | Resource-constrained devices |

### Recommended

**Default choice**: `nomic-embed-text`
- Good balance of speed and quality
- English-focused but handles other languages
- Small enough for most devices

**Better quality**: `mxbai-embed-large`
- When you have 4GB+ RAM to spare
- Better for technical documents

**Minimal resource**: `all-minilm`
- Raspberry Pi or old hardware
- Sacrifices some accuracy

## Cloud APIs

| Provider | Model | Cost | Speed | Best For |
|----------|-------|------|-------|----------|
| OpenAI | text-embedding-3-small | $0.02/M tokens | Fast | Production, high accuracy |
| OpenAI | text-embedding-3-large | $0.13/M tokens | Fast | Maximum accuracy |
| Cohere | embed-english-v3 | $0.10/M tokens | Fast | English-only optimization |
| Jina | jina-embeddings-v2 | Free tier | Medium | Open source alternative |

## Configuration Examples

### Ollama

```bash
openclaw configure memory.embedding.provider=ollama
openclaw configure memory.embedding.ollama.model=nomic-embed-text
openclaw configure memory.embedding.ollama.baseUrl=http://localhost:11434
```

### OpenAI

```bash
openclaw configure memory.embedding.provider=openai
openclaw configure memory.embedding.openai.apiKey=sk-...
openclaw configure memory.embedding.openai.model=text-embedding-3-small
```

### Multiple Providers

You can configure multiple providers and switch between them:

```bash
# Set Ollama as default
openclaw configure memory.embedding.provider=ollama

# Later switch to OpenAI
openclaw configure memory.embedding.provider=openai
```

No restart needed for provider switching, but model changes require restart.

## Dimension Compatibility

⚠️ **Important**: Once you choose a model, stick with it.

Switching models with different dimensions requires re-indexing all vectors.

| Model | Dimensions |
|-------|-----------|
| nomic-embed-text | 768 |
| mxbai-embed-large | 1024 |
| all-minilm | 384 |
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |

## Performance Benchmarks

On a typical laptop (i5, 16GB RAM):

| Model | Index 100 docs | Query latency |
|-------|---------------|---------------|
| nomic-embed-text | 5s | 50ms |
| mxbai-embed-large | 12s | 80ms |
| OpenAI API | 3s | 200ms (network) |

## Troubleshooting Model Issues

### "Model not found" error

```bash
# Check available models
ollama list

# Pull if missing
ollama pull nomic-embed-text
```

### Out of memory

Switch to smaller model:
```bash
openclaw configure memory.embedding.ollama.model=all-minilm
openclaw gateway restart
```

### Slow indexing

- Reduce chunk size: `memory.chunkSize=300`
- Use API instead of local for large batches
- Index during off-peak hours
