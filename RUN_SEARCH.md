# Run a supervised job search

Read `AGENTS.md`, `skills/job-discovery/SKILL.md`, `config/profile.json`, `config/companies.txt`, and `config/job.schema.json`.

Search the companies in batches of no more than 10. For each company:

1. Search the official company career page for backend, software engineering, SDE II, SDE III, platform, Java, Python, Go, Spring Boot, cloud, and distributed-systems roles.
2. Search approved public job sources such as Naukri, Instahyre, and visible LinkedIn job posts when available.
3. Do not search or scrape LinkedIn profiles, connection lists, or people-search pages during this task.
4. Capture only roles that are plausibly relevant to the profile. Mark uncertain roles `needs_verification: true`.
5. Keep salary `null` unless the source explicitly publishes fixed base salary.
6. Deduplicate against `data/jobs.json`.
7. Write the result and run:

```bash
python3 scripts/validate_jobs.py --jobs data/jobs.json
```

At the end, write `data/last_run.md` with counts for strong matches, potential matches, stretch roles, excluded roles, blocked sources, and roles requiring manual verification. Include direct source links for every retained role.

