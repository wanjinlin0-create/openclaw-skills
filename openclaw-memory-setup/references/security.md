# Memory Security Guide

## Scope Isolation

### Main Session vs Group Sessions

**Main Session** (Direct chat):
- Loads MEMORY.md ✅
- Can read/write personal context
- Full access to long-term memory

**Group Sessions** (Discord, group chats):
- Does NOT load MEMORY.md ❌
- Can only access session history
- SECURITY: Prevents personal data leakage to groups

## File Permissions

Memory files should have restricted permissions:

```bash
chmod 600 ~/.openclaw/workspace/MEMORY.md
chmod 700 ~/.openclaw/workspace/memory/
```

## What NOT to Store

Avoid in MEMORY.md:
- Passwords or API keys
- Private keys (SSH, crypto)
- Sensitive personal information about others
- Confidential business data (unless in secure environment)

## Safe to Store

Appropriate for MEMORY.md:
- Project context and decisions
- Your preferences and habits
- Publicly known information
- Learning notes and lessons

## Vector Privacy

### Local Models (Ollama)

✅ **Private**: All embeddings generated locally
- Text never leaves your machine
- No API calls to external services
- Recommended for sensitive content

### Cloud APIs (OpenAI, etc.)

⚠️ **Caution**: Text sent to external API
- Review provider's data retention policy
- Consider for non-sensitive content only
- Use local models for confidential material

## Audit Trail

Check what's in your memory:

```bash
# List all memory files
ls -la ~/.openclaw/workspace/memory/

# Preview MEMORY.md (first 50 lines)
head -50 ~/.openclaw/workspace/MEMORY.md

# Search for potentially sensitive terms
grep -i "password\|secret\|key" ~/.openclaw/workspace/memory/*.md
```

## Cleanup

### Remove Old Daily Notes

Daily notes older than 30 days can usually be removed:

```bash
# Archive old notes
mkdir -p ~/.openclaw/workspace/memory/archive/
find ~/.openclaw/workspace/memory/ -name "*.md" -mtime +30 -exec mv {} archive/ \;
```

### Clear Vector Index

If you need to completely reset:

```bash
# Stop gateway
openclaw gateway stop

# Remove vector database (location varies by setup)
rm -rf ~/.openclaw/vector-store/

# Restart
openclaw gateway start
```

## Multi-User Considerations

If multiple people use the same OpenClaw instance:

1. **Separate workspaces**: Each user gets their own workspace directory
2. **Shared MEMORY.md**: Only store non-sensitive, shared context
3. **Per-user memory**: Use `memory/<username>/` subdirectories
4. **Gateway-level isolation**: Consider separate gateway instances

## Backup

Memory files are just text - easy to backup:

```bash
# Backup to git (exclude sensitive info)
cd ~/.openclaw/workspace/
git init
git add MEMORY.md memory/
git commit -m "Memory backup $(date +%Y-%m-%d)"

# Or simple tarball
tar czf memory-backup-$(date +%Y%m%d).tar.gz MEMORY.md memory/
```

## Incident Response

**If sensitive data was accidentally stored:**

1. Remove from memory files immediately
2. Clear vector index (see above)
3. Check if any logs captured the data
4. Rotate any exposed credentials
5. Review access logs if in multi-user environment
