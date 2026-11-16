# Security

Terminal 1 holds SSH keys and cloud credentials, so security matters even for a prototype.

**Reporting a vulnerability** (in the firmware, the Linux setup, the image build or the website): use GitHub's private
**Security → Report a vulnerability** form on this repository. Please don't open a public issue. We'll acknowledge within a week.

**Hardware safety** problems (battery, charging, heat) are also welcome as private reports, or as public issues if no one is at risk.

Scope notes:

- The published Linux image is a development image (see `linux/README.md` for its default account and how to change it).
- The keyboard firmware is a USB keyboard: anyone who can reflash it can type into the device. Service mode needs physical access.
- Device hardening (disk encryption, screen lock, key handling): `linux/security.md`.
