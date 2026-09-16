HOMECLOUD — STAGE 3: SQLITE MEMORY

This update preserves HomeCloudStorage.

What changes:
- SQLite database created at:
  HomeCloudData/homecloud.db
- Every new upload gets:
  • stable ID
  • original filename
  • safe random stored filename
  • exact byte size
  • MIME type
  • date/time
  • relative disk path
  • SHA-256 fingerprint
  • category
- Existing Stage 1/2 files are imported automatically.
- New downloads restore the original filename.
- "Info" opens the metadata record in the UI.
- Delete removes both the real file and its SQLite record.

IMPORTANT MIGRATION NOTE:
Stage 1/2 did not save original filenames anywhere.
Existing older files therefore appear with their random stored filename.
New Stage 3 uploads preserve the real original filename correctly.

This remains a trusted-local-Wi-Fi prototype.
Stage 4 adds device pairing and access control.
