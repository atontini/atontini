# Andrea Tontini

**Software engineer · Systems programming and hardware/software integration**

I work with Rust, C/C++ and C#/.NET, from application architecture to embedded systems and hardware interfaces. I care about performance, reliability, security and maintainability, especially under load or with limited resources. I contribute to open source to improve tools I use and solve real-world engineering problems.

Beyond code, I contribute articles and help organize events with [Italian Embedded](https://www.italianembedded.com). I’m also an organizer of [Rust Milano](https://www.meetup.com/rust-language-milan/), the Milan Rust community.

## Technical focus

| Area | Experience and interests |
| :--- | :--- |
| Systems programming and developer tooling | Rust, C/C++; CLI and MCP tooling, filesystem boundaries and resource ownership |
| Embedded systems and hardware integration | Embedded Linux and firmware; CAN communication, industrial automation and end-of-line testing |
| Performance, testing and reliability | Workflow benchmarking, profiling, regression tests and recovery mechanisms |
| Software architecture and cross-platform development | C#/.NET application architecture; Unix and Windows APIs and hardware interfaces |

## Selected Open-Source Contributions

A few merged upstream changes, motivated by problems encountered while using these tools:

- **TokenSave — edit boundaries ([#975](https://github.com/aovestdipaperino/tokensave/pull/975)):** Added canonical path checks for MCP edits, recognizing Git worktrees while rejecting unrelated paths and protected state. A refused target blocks the whole rename to avoid partial changes.
- **TokenSave — indexed-data security ([#1003](https://github.com/aovestdipaperino/tokensave/pull/1003)):** Blocked reads into `.git`, added a legacy source-cache purge without a schema change, and tested file-visibility and diagnostic boundaries. Added guidance to treat repository content as untrusted data.
- **TokenSave — agent workflow benchmarking ([#967](https://github.com/aovestdipaperino/tokensave/pull/967)):** Built a harness with pinned tasks, independent correctness checks and baseline/MCP/guidance comparisons. Separated startup, model and tool time to identify bottlenecks in complete agent workflows.
- **TokenSave — incremental synchronization ([#979](https://github.com/aovestdipaperino/tokensave/pull/979)):** Added an opt-in filesystem watcher that reuses indexing rules and incremental sync, with bounded queues and reconciliation scans after overflow or watcher errors.
- **serial2 — explicit resource release ([#69](https://github.com/de-vri-es/serial2-rs/pull/69)):** Added a consuming `SerialPort::close` API that reports native Unix and Windows errors. Ownership transfer prevents double-close; Unix close is not retried because the descriptor may already have been reused.
- **Turso — query correctness ([#10555](https://github.com/tursodatabase/turso/pull/10555)):** Fixed premature `LIMIT` pushdown when an index method’s ordering differs from the query. Added regression coverage so full-text results are sorted before the limit is applied.

## Upstream contributions

Public upstream projects where I have authored merged pull requests, grouped by repository and refreshed weekly. Open or unmerged PRs, issues, reviews and direct commits are not included.

<!-- PROJECTS:START -->
### Contributed projects (merged pull requests)

- [aovestdipaperino/tokensave](https://github.com/aovestdipaperino/tokensave) — [134 merged PRs](https://github.com/aovestdipaperino/tokensave/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [aovestdipaperino/plank](https://github.com/aovestdipaperino/plank) — [7 merged PRs](https://github.com/aovestdipaperino/plank/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [alvarogaiotti/FIGBGET](https://github.com/alvarogaiotti/FIGBGET) — [1 merged PR](https://github.com/alvarogaiotti/FIGBGET/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [de-vri-es/serial2-rs](https://github.com/de-vri-es/serial2-rs) — [1 merged PR](https://github.com/de-vri-es/serial2-rs/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [DevelopersLife/DevelopersLife.github.io](https://github.com/DevelopersLife/DevelopersLife.github.io) — [1 merged PR](https://github.com/DevelopersLife/DevelopersLife.github.io/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [josephmisiti/awesome-machine-learning](https://github.com/josephmisiti/awesome-machine-learning) — [1 merged PR](https://github.com/josephmisiti/awesome-machine-learning/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [kushagra10025/OpenGL-Starter](https://github.com/kushagra10025/OpenGL-Starter) — [1 merged PR](https://github.com/kushagra10025/OpenGL-Starter/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [rylev/DMG-01](https://github.com/rylev/DMG-01) — [1 merged PR](https://github.com/rylev/DMG-01/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
- [tursodatabase/turso](https://github.com/tursodatabase/turso) — [1 merged PR](https://github.com/tursodatabase/turso/pulls?q=is%3Apr+is%3Amerged+author%3Aatontini)
<!-- PROJECTS:END -->

## Recent public activity

A rolling snapshot of my public GitHub work, refreshed weekly. [All activity](https://github.com/atontini?tab=overview).

<!-- ACTIVITY:START -->
- 2026-11-15 — Opened pull request [zephyrproject-rtos/zephyr-lang-rust#193](https://github.com/zephyrproject-rtos/zephyr-lang-rust/pull/193)
- 2026-11-15 — Opened pull request [zephyrproject-rtos/zephyr-lang-rust#192](https://github.com/zephyrproject-rtos/zephyr-lang-rust/pull/192)
- 2026-11-15 — Opened pull request [zephyrproject-rtos/zephyr-lang-rust#191](https://github.com/zephyrproject-rtos/zephyr-lang-rust/pull/191)
- 2026-11-15 — Merged pull request [aovestdipaperino/tokensave#990](https://github.com/aovestdipaperino/tokensave/pull/990)
- 2026-11-15 — Merged pull request [aovestdipaperino/tokensave#1019](https://github.com/aovestdipaperino/tokensave/pull/1019)
<!-- ACTIVITY:END -->

## Connect

[GitHub](https://github.com/atontini) · [LinkedIn](https://www.linkedin.com/in/andreatontini/) · [Website](https://atontini.github.io/)

I’m happy to exchange ideas about software design, embedded development, and tools that help engineers understand and improve their code.
