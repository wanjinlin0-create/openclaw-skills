# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Black Screen in Browser

**Symptoms:** VNC connects but shows black screen

**Causes & Solutions:**

1. **Xfce4 not started**
   ```bash
   # Check if xfce4-session is running
   pgrep -a xfce4-session
   
   # If not, start it manually
   export DISPLAY=:1
   xfce4-session &
   ```

2. **Wrong display number**
   ```bash
   # Check Xvfb display
   ps aux | grep Xvfb
   
   # Ensure x11vnc uses correct display
   x11vnc -display :1 -rfbport 5901 ...
   ```

### Issue: VNC Connection Refused

**Symptoms:** Browser shows "Connection refused" or cannot connect

**Solutions:**

1. **Check if x11vnc is running**
   ```bash
   netstat -tuln | grep 5901
   # or
   ss -tuln | grep 5901
   ```

2. **Restart x11vnc**
   ```bash
   pkill x11vnc
   x11vnc -display :1 -rfbport 5901 -rfbauth ~/.vnc/passwd -forever -shared -bg
   ```

3. **Check firewall**
   ```bash
   sudo ufw status
   # Allow VNC port if needed
   sudo ufw allow 5901/tcp
   sudo ufw allow 6080/tcp
   ```

### Issue: Cloudflare Tunnel Not Working

**Symptoms:** Local access works but tunnel URL doesn't

**Solutions:**

1. **Check tunnel status**
   ```bash
   cloudflared tunnel list
   cloudflared tunnel info <tunnel-id>
   ```

2. **Restart tunnel**
   ```bash
   pkill cloudflared
   cloudflared tunnel run <tunnel-name>
   ```

3. **Verify config file**
   ```bash
   cat ~/.cloudflared/config.yml
   # Should contain:
   # tunnel: <id>
   # credentials-file: /path/to/creds.json
   # ingress:
   #   - service: http://localhost:6080
   ```

### Issue: High Memory Usage

**Symptoms:** System slows down, out of memory

**Solutions:**

1. **Check memory usage**
   ```bash
   ps aux | grep -E "(Xvfb|xfce4|x11vnc)" | awk '{print $1, $2, $4, $11}'
   ```

2. **Reduce Xvfb resolution**
   ```bash
   # Edit setup.sh, change:
   Xvfb :1 -screen 0 1280x720x24  # Instead of 1920x1080x24
   ```

3. **Use lighter desktop**
   ```bash
   # Install LXDE instead of Xfce4
   sudo apt-get install lxde
   # Then modify setup.sh to use lxsession
   ```

### Issue: "Can't open display"

**Symptoms:** xfce4-session fails with display error

**Solutions:**

1. **Export DISPLAY variable**
   ```bash
   export DISPLAY=:1
   ```

2. **Check Xvfb socket**
   ```bash
   ls -la /tmp/.X11-unix/
   # Should see X1
   ```

3. **Remove stale lock files**
   ```bash
   rm -f /tmp/.X1-lock
   rm -f /tmp/.X11-unix/X1
   ```

### Issue: Password Not Working

**Symptoms:** VNC prompts for password but rejects it

**Solutions:**

1. **Reset VNC password**
   ```bash
   x11vnc -storepasswd ~/.vnc/passwd
   # Enter new password when prompted
   
   # Restart x11vnc
   pkill x11vnc
   x11vnc -display :1 -rfbport 5901 -rfbauth ~/.vnc/passwd -forever -shared -bg
   ```

2. **Check password file permissions**
   ```bash
   ls -la ~/.vnc/passwd
   # Should be readable by current user
   chmod 600 ~/.vnc/passwd
   ```

## Diagnostic Commands

```bash
# Check all related processes
ps aux | grep -E "(Xvfb|xfce|x11vnc|websockify|cloudflared)"

# Check listening ports
netstat -tuln | grep -E "(5901|6080)"

# View logs
tail -f ~/remote-desktop-logs/*.log

# Check display
xdpyinfo -display :1 2>/dev/null | head -20

# Test VNC locally
vncviewer localhost:5901
```

## Log File Locations

| Service | Log Location |
|---------|--------------|
| Xvfb | ~/remote-desktop-logs/xvfb.log |
| Xfce4 | ~/remote-desktop-logs/xfce4.log |
| x11vnc | ~/remote-desktop-logs/x11vnc.log |
| websockify | ~/remote-desktop-logs/websockify.log |

## Getting Help

If issues persist:

1. Collect logs: `tar czf remote-desktop-logs.tar.gz ~/remote-desktop-logs/`
2. Check system info: `uname -a && lsb_release -a`
3. Document steps to reproduce the issue
