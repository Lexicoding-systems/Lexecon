# Troubleshooting

Common issues and their solutions.

---

## Installation Issues

### Error: "command 'lexecon' not found"

**Cause:** Lexecon not installed or not in PATH.

**Solution:**
```bash
# Check if installed
pip list | grep lexecon

# If not installed
pip install lexecon

# If installed but not in PATH
python -m lexecon.cli.main --version

# Or add to PATH (Linux/Mac)
export PATH="$HOME/.local/bin:$PATH"

# Or add to PATH (Windows)
# Add %APPDATA%\Python\Scripts to PATH
```

### Error: "No module named 'lexecon'"

**Cause:** Package not installed correctly.

**Solution:**
```bash
# Reinstall
pip uninstall lexecon
pip install lexecon

# Or install from source
git clone https://github.com/Lexicoding-systems/Lexecon.git
cd Lexecon
pip install -e .
```

### Error: "Permission denied"

**Cause:** Installing to system Python without sudo.

**Solution:**
```bash
# Install for current user only
pip install --user lexecon

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install lexecon
```

### Dependency conflicts

**Cause:** Incompatible package versions.

**Solution:**
```bash
# Create fresh virtual environment
python -m venv lexecon-env
source lexecon-env/bin/activate
pip install lexecon

# Or use conda
conda create -n lexecon python=3.11
conda activate lexecon
pip install lexecon
```

---

## Server Issues

### Server won't start: "Address already in use"

**Cause:** Port 8000 is already in use.

**Check what's using the port:**
```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

**Solution:**
```bash
# Option 1: Kill the process
kill <PID>

# Option 2: Use different port
lexecon server --port 8080

# Option 3: Specify different host
lexecon server --host 127.0.0.1 --port 8001
```

### Server crashes on startup

**Check logs:**
```bash
# View logs
lexecon logs --node-id my-node

# Or check system logs
tail -f ~/.lexecon/nodes/my-node/logs/server.log
```

**Common causes:**
1. **No node initialized:**
   ```bash
   lexecon init --node-id my-node
   ```

2. **No policy loaded:**
   ```bash
   lexecon policy load --file examples/example_policy.json
   ```

3. **Corrupted configuration:**
   ```bash
   # Backup and reinitialize
   mv ~/.lexecon/nodes/my-node ~/.lexecon/nodes/my-node.bak
   lexecon init --node-id my-node
   ```

### Server is slow

**Diagnose:**
```bash
# Check resource usage
top  # or htop

# Check disk I/O
iostat -x 1

# Check logs for errors
lexecon logs --node-id my-node --level ERROR
```

**Solutions:**
1. **Optimize policy:**
   - Simplify complex conditions
   - Reduce number of rules
   
2. **Use faster storage:**
   - Move ledger to SSD
   - Use in-memory storage for testing
   
3. **Increase resources:**
   ```bash
   # Increase worker threads
   lexecon server --workers 4
   ```

---

## Policy Issues

### "Policy not loaded" error

**Cause:** No policy loaded into the node.

**Solution:**
```bash
# Load a policy
lexecon policy load --file examples/example_policy.json --node-id my-node

# Verify it loaded
lexecon policy list --node-id my-node
```

### Policy validation fails

**Check syntax:**
```bash
# Validate JSON
python -m json.tool my_policy.json

# Validate against schema
lexecon policy validate --file my_policy.json
```

**Common errors:**
```json
// ❌ Missing comma
{
  "policy_id": "pol_001"
  "version": "1.0.0"
}

// ✅ Correct
{
  "policy_id": "pol_001",
  "version": "1.0.0"
}

// ❌ Trailing comma
{
  "mode": "strict",
}

// ✅ Correct
{
  "mode": "strict"
}
```

### Policy not taking effect

**Cause:** Server not restarted after policy change.

**Solution:**
```bash
# Stop server
pkill -f "lexecon server"

# Reload policy
lexecon policy load --file my_policy.json

# Restart server
lexecon server --node-id my-node
```

### Unexpected denials

**Debug the decision:**
```bash
# Make decision with verbose output
lexecon decide \
  --actor model \
  --action test \
  --verbose \
  --node-id my-node
```

**Check policy:**
```bash
# View loaded policy
lexecon policy show --policy-id pol_001 --node-id my-node

# Check specific rule
lexecon policy check --actor model --action test
```

**Common issues:**
1. **Strict mode with no permit rule:**
   ```json
   {
     "mode": "strict",  // Denies by default
     "relations": {
       "permits": []  // No permits = everything denied
     }
   }
   ```

2. **Forbid takes precedence:**
   ```json
   {
     "permits": [
       {"actor": "model", "action": "test"}
     ],
     "forbids": [
       {"actor": "model", "action": "test"}  // This wins
     ]
   }
   ```

3. **Case sensitivity:**
   ```json
   // Policy says "Model" but request says "model"
   {"actor": "Model", "action": "test"}  // Won't match
   ```

---

## Decision & Token Issues

### "Invalid token" error

**Possible causes:**

1. **Token expired:**
   ```bash
   # Check token expiration
   lexecon verify --token <token> --verbose
   ```

2. **Wrong node:**
   ```bash
   # Token is node-specific
   # Ensure using same node that issued token
   ```

3. **Policy version changed:**
   ```bash
   # Tokens are bound to policy version
   # Check current policy version
   lexecon policy show --policy-id pol_001
   ```

4. **Invalid signature:**
   ```bash
   # Token may be corrupted or tampered
   # Request new token
   ```

### Decision takes too long

**Check policy complexity:**
```bash
# Analyze policy performance
lexecon policy analyze --policy-id pol_001

# Test specific decision
time lexecon decide --actor model --action test
```

**Optimize:**
- Simplify conditions
- Cache policy evaluations
- Use faster storage

### "REQUIRES_REVIEW" not working

**Cause:** No review system configured.

**Solution:**
```bash
# Configure review webhook
lexecon config set review_webhook "https://myapp.com/review"

# Or handle programmatically
```

```python
decision = client.decide(actor="model", action="high_risk")

if decision.decision == "REQUIRES_REVIEW":
    # Send to review queue
    review_system.queue(decision)
```

---

## Ledger Issues

### Ledger verification fails

**This is serious** - indicates possible tampering.

**Steps:**
1. **Stop using the node immediately**
   ```bash
   pkill -f "lexecon server"
   ```

2. **Export ledger for analysis**
   ```bash
   lexecon ledger export --output /tmp/ledger_backup.json
   ```

3. **Check for tampering**
   ```bash
   lexecon ledger verify --detailed --node-id my-node
   ```

4. **Investigate**
   - Check file system access logs
   - Review user access
   - Check for unauthorized modifications
   - Review recent decisions

5. **If tampered:**
   - Do NOT continue using
   - Restore from backup
   - Rotate keys
   - Create incident report

6. **If false alarm:**
   ```bash
   # Rebuild ledger indices
   lexecon ledger rebuild --node-id my-node
   ```

### Ledger growing too large

**Check size:**
```bash
du -sh ~/.lexecon/nodes/my-node/ledger/
```

**Solutions:**
1. **Archive old entries:**
   ```bash
   lexecon ledger archive --before 2024-01-01
   ```

2. **Export and rotate:**
   ```bash
   lexecon ledger export --output archive_2024.json
   lexecon ledger rotate --keep-days 90
   ```

3. **Configure retention:**
   ```bash
   lexecon config set ledger_retention_days 90
   ```

### Ledger write failures

**Check disk space:**
```bash
df -h
```

**Check permissions:**
```bash
ls -la ~/.lexecon/nodes/my-node/ledger/
```

**Fix permissions:**
```bash
chmod 700 ~/.lexecon/nodes/my-node/
chmod 600 ~/.lexecon/nodes/my-node/ledger/*
```

---

## Integration Issues

### OpenAI integration not working

**Check API key:**
```bash
echo $OPENAI_API_KEY
```

**Verify adapter:**
```python
from lexecon.adapters import OpenAIAdapter

adapter = OpenAIAdapter(api_key="sk-...")
result = adapter.test_connection()
print(result)
```

**Common issues:**
1. **Wrong API key**
2. **Rate limiting**
3. **Network issues**
4. **Model not available**

### Claude integration not working

Similar to OpenAI:

```python
from lexecon.adapters import AnthropicAdapter

adapter = AnthropicAdapter(api_key="sk-ant-...")
result = adapter.test_connection()
```

### Tool execution blocked

**Ensure token is included:**
```python
# Request decision first
decision = lexecon_client.decide(
    actor="model",
    action="search_web",
    tool="web_search"
)

# Include token in tool execution
if decision.decision == "ALLOWED":
    result = execute_tool(
        tool="web_search",
        token=decision.capability_token  # Must include!
    )
```

---

## Performance Issues

### High latency

**Measure components:**
```bash
# Policy evaluation time
time lexecon decide --actor model --action test --no-ledger

# Ledger write time
time lexecon ledger add --entry test

# Full decision time
time lexecon decide --actor model --action test
```

**Optimize:**
1. **Policy**: Simplify rules
2. **Ledger**: Use faster storage
3. **Network**: Reduce round trips
4. **Caching**: Enable policy cache

### High memory usage

**Check memory:**
```bash
# Linux
ps aux | grep lexecon

# macOS
top -l 1 | grep lexecon
```

**Solutions:**
1. **Reduce cache size:**
   ```bash
   lexecon config set cache_max_size 100
   ```

2. **Limit worker threads:**
   ```bash
   lexecon server --workers 2
   ```

3. **Archive old ledger entries**

### High CPU usage

**Profile the server:**
```bash
# Install profiling tools
pip install py-spy

# Profile running server
py-spy top --pid <lexecon-pid>

# Generate flame graph
py-spy record -o profile.svg --pid <lexecon-pid>
```

**Common causes:**
- Complex policy evaluation
- Frequent signature operations
- Ledger verification

---

## Database/Storage Issues

### SQLite locked error

**Cause:** Multiple processes accessing database.

**Solution:**
```bash
# Use single server instance
# Or configure connection pool
lexecon config set database_pool_size 5
```

### Corrupted database

**Check integrity:**
```bash
sqlite3 ~/.lexecon/nodes/my-node/lexecon.db "PRAGMA integrity_check;"
```

**Restore from backup:**
```bash
cp ~/.lexecon/nodes/my-node/lexecon.db.backup \
   ~/.lexecon/nodes/my-node/lexecon.db
```

---

## Network Issues

### Connection refused

**Check server is running:**
```bash
ps aux | grep "lexecon server"
```

**Check firewall:**
```bash
# Linux
sudo iptables -L

# macOS
sudo pfctl -s rules
```

**Test connectivity:**
```bash
curl http://localhost:8000/health
```

### SSL certificate errors

**Use HTTPS in production:**
```bash
lexecon server \
  --ssl-cert /path/to/cert.pem \
  --ssl-key /path/to/key.pem
```

**For testing, disable SSL verification:**
```python
client = LexeconClient(
    base_url="http://localhost:8000",
    verify_ssl=False  # Only for testing!
)
```

---

## Development Issues

### Tests failing

**Run specific test:**
```bash
pytest tests/test_policy.py::test_strict_mode -v
```

**Check test environment:**
```bash
# Clean test artifacts
make clean

# Reinstall in dev mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Import errors in development

**Ensure editable install:**
```bash
pip install -e .
```

**Check PYTHONPATH:**
```bash
echo $PYTHONPATH
export PYTHONPATH=/path/to/Lexecon/src:$PYTHONPATH
```

---

## Getting More Help

If you can't solve your issue:

1. **Check logs:**
   ```bash
   lexecon logs --node-id my-node --tail 100
   ```

2. **Enable debug mode:**
   ```bash
   lexecon server --log-level DEBUG
   ```

3. **Collect diagnostic info:**
   ```bash
   lexecon doctor --output diagnostics.txt
   ```

4. **Search existing issues:**
   [GitHub Issues](https://github.com/Lexicoding-systems/Lexecon/issues)

5. **Ask the community:**
   [GitHub Discussions](https://github.com/Lexicoding-systems/Lexecon/discussions)

6. **Report a bug:**
   [New Issue](https://github.com/Lexicoding-systems/Lexecon/issues/new)

Include:
- Lexecon version: `lexecon --version`
- Python version: `python --version`
- OS: `uname -a` (Linux/Mac) or `ver` (Windows)
- Logs: `lexecon logs --tail 50`
- Steps to reproduce

---

## See Also

- [[FAQ]] - Frequently asked questions
- [[Getting Started]] - Setup guide
- [[API Reference]] - API documentation
- [[Architecture]] - System architecture
