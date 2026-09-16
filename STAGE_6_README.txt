HOMECLOUD — STAGE 6: PRIVATE REMOTE ACCESS

Architecture:
iPhone -> Tailscale private network -> HTTPS / Tailscale Serve
       -> HomeCloud on 127.0.0.1:5050 -> SQLite + your files

Security changes:
- Flask now binds to 127.0.0.1 only.
- HomeCloud no longer exposes port 5050 directly to your LAN.
- Remote traffic uses Tailscale Serve.
- Tailscale Serve URL is HTTPS and private to your tailnet.
- Device pairing still applies on top of Tailscale access.
- Device cookies are Secure + HttpOnly.
- Mac-only admin pages distinguish direct localhost from Tailscale Serve.
- Do NOT use Tailscale Funnel for HomeCloud.

Requirements:
- Tailscale installed on Mac.
- Tailscale installed on iPhone.
- Both signed into the same tailnet/account.
- Mac awake, online, Tailscale connected, and HomeCloud running.

After Stage 6 works:
You can turn off iPhone Wi-Fi and use cellular to reach the private HTTPS
HomeCloud URL while the Mac stays at home.
