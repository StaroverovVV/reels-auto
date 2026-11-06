# OpenFilm: independent Reels Studio export pilot

Created 2026-11-06. No Hermes. Existing Reels Studio 5.3, Reels Brain and FFmpeg pipeline are unchanged.

This is an isolated, one-way Python exporter of an already prepared montage plan into an OpenFilm project:
- 1080x1920 film.html, source footage, optional separate voice, WebVTT sidecar.
- Validates cut timings and reviewed subtitles.
- Never overwrites an existing OpenFilm folder or its manual edits.
- No local AI models, keys, API calls or publishing.

Tests: python3 -m unittest discover -s tests -v

Manual cloud smoke-test: .github/workflows/openfilm-pilot.yml. The only remote test input is synthetic media created on the GitHub Actions runner. It generates synthetic footage on the runner, downloads OpenFilm only there, and attempts a render. Do not upload real/client media to public CI without separate consent.

Not yet validated: cloud render behavior, burned-in captions, real-world sound/video quality, 3-minute performance, current Reels Studio UI bridge.
