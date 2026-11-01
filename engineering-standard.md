# Engineering standard

This is the working standard for the portfolio. Apply it in proportion to the risk and complexity of each project.

## Method

- Start with a clear problem, users, boundaries and explicit requirements. Separate facts, assumptions and open decisions.
- Document a simple baseline and consider alternatives before committing to an architecture. Record consequential decisions and why they were made.
- Define interfaces, data types, units, error handling and state transitions before relying on them. Keep modules cohesive and dependencies explicit.
- Implement in small, understandable changes. Prefer established, documented language features and libraries; pin versions and explain unusual dependencies.
- Review generated or assisted code line by line, understand it and validate it like any other code. AI assistance cannot honestly be described as human authored code; quality comes from accountable design, review and evidence, not from claiming no assistance was used.
- Do not invent results, customers, benchmarks, credentials or historical artefacts. Record limitations, failed runs and contrary evidence.

## Verification

- Map each requirement to a meaningful test, inspection or experiment, with input, expected behaviour and a repeatable command. Test boundaries and failure paths, not just implementation details.
- Use unit tests for domain logic and integration tests at meaningful boundaries. Add property, differential, concurrency or performance tests where the project warrants them.
- Keep deterministic tests independent of network services; use test doubles for external dependencies. Record seeds, data version, software versions and relevant machine details for experiments.
- Compare against a defensible baseline on the same cases. Keep development and held out cases separate where tuning occurs. Report sample sizes, uncertainty and negative cases.
- Run documented checks from a clean environment before declaring a release. Record what could not be verified.

## Design and operations

- Validate input at boundaries; use least privilege, avoid secrets in source and logs and provide safe failure behaviour. Do not introduce real personal or client data without authorisation and an appropriate design.
- Treat simulation, synthetic datasets and benchmark environments as bounded models. They do not establish certification, safety, business savings or production suitability.
- Keep the human decision point explicit for safety, payments, releases, entity merges and external publication. No automatic deployment or external action follows from a passing test alone.
- Use a README with setup, usage, test commands and limitations. Keep requirements, design decisions, results and the portfolio narrative in agreement.

## Definition of done

The agreed first release scope has working code, a documented design, checks mapped to requirements, repeatable setup and recorded results. A reviewer can follow claims to evidence and see unresolved risks. Independent human review and domain approval are recorded where they are required; an AI review is not a substitute.
