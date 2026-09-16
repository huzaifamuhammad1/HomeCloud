from homecloud import create_app

app = create_app()

if __name__ == "__main__":
    # Stage 6 security change:
    # HomeCloud no longer listens directly on the LAN.
    # Tailscale Serve proxies private HTTPS traffic to this localhost-only server.
    app.run(host="127.0.0.1", port=5050, debug=False)
