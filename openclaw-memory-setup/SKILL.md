---
name: openclaw-memory-setup
description: Configure and optimize OpenClaw memory system (FTS full-text search and Vector semantic search). Use when setting up memory search, configuring embedding models, organizing memory files, or troubleshooting memory_search functionality. Covers FTS vs Vector comparison, embedding provider setup (Ollama/OpenAI), and best practices for MEMORY.md and daily notes organization.
---

# OpenClaw Memory Setup

Complete guide to configuring OpenClaw's memory system for effective long-term memory retrieval.

## Quick Start

Check current memory status:
```bash
openclaw status | grep -A2 "Memory"
```

Expected output:
```
Memory │ 0 files · 0 chunks · sources memory · plugin memory-core · vector unknown · fts ready · cache on
```

- `fts ready` = Full-text search is working ✅
- `vector unknown` = Semantic search needs configuration ⚠️

## FTS vs Vector Search

| Feature | FTS (Full-Text Search) | Vector (Semantic Search) |
|---------|------------------------|--------------------------|
| **Matching** | Exact keyword match | Semantic similarity |
| **Example** | Search "Python" finds "Python" | Search "coding" finds "programming" |
| **Setup** | Works out of the box ✅ | Requires embedding model |
| **Speed** | Fast (local SQLite) | Depends on embedding provider |
| **Use case** | Precise retrieval | Fuzzy/conceptual matching |

**Recommendation**: Start with FTS. Add Vector when you need semantic understanding.

## Configuration

### 1. FTS Configuration (Default)

FTS is enabled by default. No configuration needed.

Verify it's working:
```bash
openclaw memory search "test query"
```

### 2. Vector Configuration

Vector search requires an embedding model. Two options:

#### Option A: Local Ollama (Recommended for privacy)

1. Install Ollama:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. Pull an embedding model:
```bash
ollama pull nomic-embed-text
# or
ollama pull mxbai-embed-large
```

3. Configure OpenClaw:
```bash
openclaw configure --section memory
```

Set values:
```
embedding.provider = ollama
embedding.ollama.model = nomic-embed-text
embedding.ollama.baseUrl = http://localhost:11434
```

4. Restart gateway:
```bash
openclaw gateway restart
```

5. Verify:
```bash
openclaw status | grep vector
# Should show: vector ready
```

#### Option B: OpenAI API

1. Get API key from https://platform.openai.com

2. Configure:
```bash
openclaw configure --section memory
```

Set values:
```
embedding.provider = openai
embedding.openai.apiKey = sk-your-key-here
embedding.openai.model = text-embedding-3-small
```

3. Restart and verify as above.

## Memory File Organization

### Directory Structure

```
~/.openclaw/workspace/
├── MEMORY.md              # Curated long-term memory
├── memory/
│   ├── 2026-03-27.md     # Daily raw notes
│   ├── 2026-03-26.md
│   └── ...
└── AGENTS.md             # Workspace rules (auto-loaded)
```

### MEMORY.md Best Practices

- **What goes here**: Important decisions, project context, user preferences, lessons learned
- **Format**: Use headers and bullet points for easy scanning
- **Update**: Review weekly, distill from daily notes
- **Security**: Only loaded in main (direct) sessions, not in groups

Example structure:
```markdown
# MEMORY.md - Long-term Memory

## Projects

### Project Name
- Start date: 2026-03-27
- Key decisions: ...
- Next actions: ...

## User Preferences
- Name: ...
- Communication style: ...

## Lessons Learned
- ...
```

### Daily Notes (memory/YYYY-MM-DD.md)

- **What goes here**: Raw logs of what happened today
- **Format**: Freeform, timestamped entries
- **Auto-created**: Some contexts auto-create these
- **Purpose**: Temporary holding area before distilling to MEMORY.md

## Troubleshooting

### memory_search returns "disabled=true"

Memory retrieval is unavailable. Check:
1. Is the memory plugin loaded? `openclaw status | grep memory`
2. Are memory files present? `ls ~/.openclaw/workspace/memory/`

### Vector search not working

Symptoms: `vector unknown` in status

Solutions:
1. Check embedding provider is configured: `openclaw configure --section memory`
2. Verify Ollama is running: `ollama list`
3. Check model is pulled: `ollama pull nomic-embed-text`
4. Restart gateway: `openclaw gateway restart`

### FTS returns no results

1. Check files exist: `ls ~/.openclaw/workspace/memory/`
2. Check file permissions
3. Re-index: Files are indexed automatically on access

## Advanced

### Custom Memory Sources

Add additional memory directories:
```bash
openclaw configure memory.sources.extra=/path/to/extra/memory
```

### Chunking Configuration

Control how documents are split for vector search:
```bash
openclaw configure memory.chunkSize=500
openclaw configure memory.chunkOverlap=50
```

### Cache Control

Memory search results are cached by default. To disable:
```bash
openclaw configure memory.cache=false
```

## Migration Notes

### From FTS-only to FTS+Vector

1. Configure embedding provider
2. Restart gateway
3. Existing files will be auto-indexed on next search
4. No manual re-indexing needed

## References

- Full configuration options: See `openclaw configure --help`
- Available embedding models: See references/embedding-models.md
- Memory security: See references/security.md
