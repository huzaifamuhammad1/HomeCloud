# Security Policy

HomeCloud is currently an active personal engineering project and has **not** undergone a formal third-party security audit.

## Security model

The project currently uses:

- localhost-bound Flask application serving
- private Tailscale networking for remote transport
- HTTPS through Tailscale Serve
- one-time QR device pairing
- long-term per-device authorization tokens
- token hashing before database persistence
- HttpOnly/Secure browser cookies on the HTTPS path
- explicit protected routes for file operations
- safe randomized internal filenames
- upload validation
- SHA-256 content fingerprints
- device revocation

## Not supported

Do not deploy HomeCloud by publicly port-forwarding the Flask development server.

Do not commit:

- `HomeCloudStorage/`
- `HomeCloudData/`
- database files
- secrets
- private keys
- paired-device state
- personal photos or documents

## Reporting

If this repository is made public and you discover a security issue, avoid posting sensitive exploit details or personal data in a public issue. Contact the repository owner privately first.
