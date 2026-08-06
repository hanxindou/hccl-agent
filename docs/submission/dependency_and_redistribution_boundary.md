# Dependency and redistribution boundary

The default CPU_SIM build needs no CANN SDK and links no `libhccl.so`,
`libhcomm.so`, or `libacl_rt.so`. Its observed ELF dependencies are recorded by
G3-B rather than inferred from filenames.

The direct readiness build may reference locally installed CANN 9.1.0 headers
and `libhccl.so`, `libhcomm.so`, and `libacl_rt.so` for signature and
non-executed link inspection. Official headers, binaries, CANN SDK files, and
HCOMM/HCCL source are excluded from staging by default. Their redistribution
status is `NOT_AUTHORIZED` until `UA-B-002` is resolved.

The project license and copyright owner are also unresolved (`UA-B-001`). The
controlled competition DOCX is an internal reference and is excluded by
default (`UA-B-003`). Platform archive format and size constraints remain
`UA-B-004`. These decisions keep release readiness `PARTIAL`.
