# Xfce Desktop Environment for Render.com

A browser-based Xfce Linux desktop environment that can be deployed to any Docker-compatible hosting platform.

## Quick Deploy to Render.com

1. **Create a Render Account**: Go to [render.com](https://render.com) and sign up

2. **Create a New Web Service**:
   - Connect your GitHub repository
   - Select "Web Service"
   - Choose the repository with these files

3. **Configure the Service**:
   - Name: `xfce-desktop` (or your preferred name)
   - Environment: `Docker`
   - Region: Choose closest to you
   - Instance Type: `Small` (recommended for desktop) or `Medium`

4. **Set Environment Variables**:
   - `VNC_PASSWORD`: Set your desired password (default: huggingface)
   - `RESOLUTION`: Desktop resolution (default: 1280x720)

5. **Deploy**: Click "Create Web Service"

## Accessing the Desktop

After deployment, your desktop will be available at:
- **Main URL**: `https://your-service-name.onrender.com`
- **Desktop**: `https://your-service-name.onrender.com/desktop`
- **Terminal**: `https://your-service-name.onrender.com/terminal`

## Architecture

```
┌─────────────────────────────────────────┐
│           Docker Container              │
│  ┌─────────────────────────────────┐   │
│  │      Xfce4 Desktop Env          │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │    x11vnc Server          │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
│              │                         │
│  ┌─────────────────────────────────┐   │
│  │      noVNC (Web Interface)      │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │   Flask Web Server        │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VNC_PASSWORD` | Password for VNC access | `huggingface` |
| `RESOLUTION` | Desktop resolution | `1280x720` |
| `VNC_PORT` | VNC server port | `5900` |

## Features

- **Xfce4 Desktop Environment** - Fast and lightweight Linux desktop
- **Web-based VNC Access** - Access through browser via noVNC
- **Integrated Terminal** - Web-based terminal interface
- **Persistent Sessions** - Desktop state persists

## Included Applications

- Xfce4 Desktop (window manager, panel)
- Xfce4 Terminal
- Thunar (file manager)
- Mousepad (text editor)
- Ristretto (image viewer)

## Troubleshooting

### Slow Performance
- Try reducing resolution: Set `RESOLUTION=1024x768`
- Upgrade to a larger instance type

### Connection Issues
- Refresh the page
- Check browser console for errors
- Ensure WebSocket support is enabled

## Cost

Render.com Free Tier: $0/month (sleeps after 15 min of inactivity)
Render.com Paid Plans: Starting at $7/month (always-on)

## License

MIT License
