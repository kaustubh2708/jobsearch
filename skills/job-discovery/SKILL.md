# Job-discovery skill

Use this skill whenever the task is to find jobs for the candidate from a company list.

## Collection order

1. Official employer careers page.
2. Official ATS pages such as Greenhouse, Lever, Workday, or the employer's own system.
3. Public job-board pages and visible job posts.
4. User-assisted logged-in browser pages only when the user has already opened the page and can see the content.

## Browser behavior

Use the browser to navigate and read pages, not to run a background scraper. Keep one company or source in focus at a time. If login, CAPTCHA, or a consent prompt appears, pause for the user. Never guess credentials or attempt to defeat a control.

For LinkedIn, allowed data is limited to visible job posts or job-search results: title, company, location, requirements, public job URL, and posting metadata. Do not open or collect personal profiles for this job-discovery task. Do not collect connection lists or mutual connections.

## Extraction contract

For every retained role, record:

- company and exact title;
- location and work mode;
- job ID when shown;
- experience requirement;
- technologies and role family;
- canonical application URL;
- source type;
- retrieval time and posting time if shown;
- fixed base salary only if explicitly published;
- concise evidence and match reasons;
- verification and review status.

Do not copy full descriptions. If a role is seen on a third-party page but not confirmed on the employer page, keep it as a lead with `source_type: third_party` and `needs_verification: true`.

## Matching rules

Prefer backend, platform, infrastructure, distributed systems, Java, Python, Go, Spring Boot, APIs, databases, cloud, and SDE roles. Penalize roles requiring substantially more experience than the candidate profile. Treat SDE III as a stretch unless the requirements are compatible with approximately three years of unusually strong experience.

Base salary is a hard review field, not a guessed field. A missing salary should lower confidence but should not automatically reject a role.

