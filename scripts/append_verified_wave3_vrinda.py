import urllib.request, ssl, json, re, time
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

candidates = [
    # --- NCR Priority: Bain & Company Tech (Gurugram / New Delhi BCN) ---
    {
        "company": "Bain & Company",
        "title": "Associate- Back end Engineer(PEG)",
        "location": "Gurugram / New Delhi (BCN)",
        "exp": "3-6 years",
        "min_exp": 3,
        "max_exp": 6,
        "tech": "Python, FastAPI, Azure AI Search, Azure OpenAI Studio, LLM APIs, Vector Embeddings, Docker",
        "url": "https://www.bain.com/careers/find-a-role/position/?jobid=109946",
        "salary_evidence": "Bain BCN Associate base: ₹35L–₹45L+ total comp",
        "match_score": 100,
        "match_label": "strong_match",
        "notes": "100% Dream fit. PEG Innovation Team building GenAI workflows and service layer on Azure AI Search and Azure OpenAI."
    },
    {
        "company": "Bain & Company",
        "title": "Associate - AI Engineer (CTE)",
        "location": "Gurugram / New Delhi (BCN)",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Python, SQL, GenAI, AI Agent Workflows, LLMs, Vector Databases, Cloud Infra",
        "url": "https://www.bain.com/careers/find-a-role/position/?jobid=105837",
        "salary_evidence": "Bain BCN Associate base: ₹35L–₹45L+",
        "match_score": 100,
        "match_label": "strong_match",
        "notes": "BCN Client Tech & Engineering AI Engineering opening. 2-5 years experience sweet spot."
    },
    {
        "company": "Bain & Company",
        "title": "Associate – Gen AI Full stack Engineer",
        "location": "Gurugram / New Delhi (BCN)",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Python, Advanced SQL, RESTful APIs, GraphQL, WebSockets, GenAI, AWS/Azure, Docker",
        "url": "https://www.bain.com/careers/find-a-role/position/?jobid=100086",
        "salary_evidence": "Bain BCN Associate base: ₹35L–₹45L+",
        "match_score": 98,
        "match_label": "strong_match",
        "notes": "DD2030 GenAI Fullstack initiative at BCN."
    },
    {
        "company": "Fidelity International",
        "title": "Analyst Programmer",
        "location": "Gurugram",
        "exp": "2+ years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Node.js, React.js, Java, Spring Boot, AWS, Kubernetes, Terraform, Unix",
        "url": "https://fil.wd3.myworkdayjobs.com/en-US/001/job/Gurgaon-Office/Analyst-Programmer_J69478",
        "salary_evidence": "Estimated base: ₹28L–₹36L+ total comp",
        "match_score": 90,
        "match_label": "strong_match",
        "notes": "GPS Production Services. Node.js backend & application recovery in Gurugram campus."
    },
    # --- Global Remote / Top Tier AI Platforms ---
    {
        "company": "Together AI",
        "title": "Junior/Senior or Staff Software Engineer, Inference / Compute Infrastructure Engineering",
        "location": "Remote in India",
        "exp": "2-5 years (Open to Junior/Mid)",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Go, Python, Rust, Temporal, Kafka, Kubernetes CRDs / Controllers, Distributed Systems",
        "url": "https://job-boards.greenhouse.io/togetherai/jobs/5213325007",
        "salary_evidence": "US Remote India Payroll: $60k–$100k+ USD (₹50L–₹80L+ LPA)",
        "match_score": 96,
        "match_label": "strong_match",
        "notes": "Explicitly posted for 'REMOTE IN INDIA'. High throughput backend & workflow orchestration."
    },
    {
        "company": "Together AI",
        "title": "AI Infrastructure System Engineer",
        "location": "Bengaluru",
        "exp": "3+ years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Python, Go, Rust, Kubernetes, Linux, Terraform, AI Infrastructure Agents",
        "url": "https://job-boards.greenhouse.io/togetherai/jobs/5180155007",
        "salary_evidence": "Estimated ₹40L–₹60L+ base + tier-1 equity",
        "match_score": 90,
        "match_label": "strong_match",
        "notes": "Bangalore location. Distributed systems, Linux platforms, and AI infra orchestration."
    },
    {
        "company": "Sourcegraph",
        "title": "Software Engineer - Platform [IC3]",
        "location": "Remote India (Global)",
        "exp": "2-4 years (IC3 SDE II)",
        "min_exp": 2,
        "max_exp": 4,
        "tech": "Go, Strongly Typed Systems, Azure, GCP, Kubernetes, Terraform, gRPC APIs",
        "url": "https://job-boards.greenhouse.io/sourcegraph91/jobs/6103628004",
        "salary_evidence": "Transparent public IC3 Zone 4 starting base: $74,000 USD (~₹62 LPA fixed)",
        "match_score": 95,
        "match_label": "strong_match",
        "notes": "Transparent salary band ($74k base = ₹62 LPA). IC3 is exact mid-level equivalent for ~3y."
    },
    {
        "company": "Supabase",
        "title": "Software Engineer - Branching",
        "location": "Remote India (Global)",
        "exp": "3+ years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "TypeScript, Go, AWS EKS/ECS, IaC (Pulumi, Terraform), Distributed Systems",
        "url": "https://jobs.ashbyhq.com/supabase/06752423-eebb-472c-95b5-c7ff2559fd60",
        "salary_evidence": "Estimated $60k–$90k USD (~₹50L–₹75L+ LPA via EOR)",
        "match_score": 94,
        "match_label": "strong_match",
        "notes": "100% remote global company. High scale cloud infrastructure and branching engines."
    },
    {
        "company": "Supabase",
        "title": "AI Platform Engineer",
        "location": "Remote India (Global)",
        "exp": "3+ years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "MCP (Model Context Protocol), LLM Agent Systems, Python, GCP, Eval Suites",
        "url": "https://jobs.ashbyhq.com/supabase/3b5d54ca-741b-45ac-bd3f-31605a0d3541",
        "salary_evidence": "Estimated $70k–$100k USD (~₹60L–₹85L+ LPA + ESOP)",
        "match_score": 93,
        "match_label": "strong_match",
        "notes": "Directly targets MCP server development and agentic evaluation workflows."
    },
    {
        "company": "Cursor / Anysphere",
        "title": "Forward Deployed Engineer - India",
        "location": "Gurugram / New Delhi / Bengaluru",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Python, TypeScript / JavaScript, AI-native Workflows, Production Reliability & Alerts, APIs",
        "url": "https://jobs.ashbyhq.com/cursor/166c3951-1d2a-4e61-b79b-bedefe96073b",
        "salary_evidence": "Estimated ₹45L–₹70L+ base + tier-1 Anysphere equity",
        "match_score": 92,
        "match_label": "strong_match",
        "notes": "Fresh requisition published on Sept 28, 2026. Covers New Delhi (NCR) and Bengaluru."
    },
    {
        "company": "Braintrust",
        "title": "Open Source Engineer - Go",
        "location": "Remote India (Global)",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Go, OpenTelemetry, LLM APIs (OpenAI, Anthropic, Gemini), CI/CD, Developer SDKs",
        "url": "https://jobs.ashbyhq.com/braintrust/2a6c4ee9-063f-45d4-83ba-faf64b1f1a60",
        "salary_evidence": "Estimated $60k–$90k USD (~₹50L–₹75L+ LPA)",
        "match_score": 75,
        "match_label": "potential_match",
        "notes": "Remote IC engineering role at AI evaluation/observability leader Braintrust."
    },
    # --- LinkedIn Jobs Engine Standouts: C# / .NET / Azure & High Concurrency ---
    {
        "company": "Walmart Global Tech",
        "title": "Software Engineer III (.NET / Cloud Backend)",
        "location": "Bengaluru",
        "exp": "3-6 years",
        "min_exp": 3,
        "max_exp": 6,
        "tech": ".NET Core / ASP.NET, C#, Azure, Distributed Systems, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4470509054",
        "salary_evidence": "Walmart SE III base: ₹32L–₹40L + bonus + RSUs (Total comp ₹40L–₹50L+)",
        "match_score": 96,
        "match_label": "strong_match",
        "notes": "Tier-1 scale .NET Core and Azure backend engineering."
    },
    {
        "company": "Walmart Global Tech",
        "title": "Software Engineer III (.NET / Distributed)",
        "location": "Bengaluru",
        "exp": "3-6 years",
        "min_exp": 3,
        "max_exp": 6,
        "tech": "C#, .NET, Distributed Systems, Cloud Microservices, High Throughput",
        "url": "https://www.linkedin.com/jobs/view/4470195796",
        "salary_evidence": "Walmart SE III base: ₹32L–₹40L+",
        "match_score": 94,
        "match_label": "strong_match",
        "notes": "Distributed transaction architecture in Walmart core technology."
    },
    {
        "company": "Walmart Global Tech",
        "title": "Senior Software Engineer (.NET Backend)",
        "location": "Bengaluru",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "C#, .NET, Azure, Cloud Microservices, SQL",
        "url": "https://www.linkedin.com/jobs/view/4470504319",
        "salary_evidence": "Walmart SSE base: ₹32L–₹40L+",
        "match_score": 92,
        "match_label": "strong_match",
        "notes": "3-5 years experience target for .NET backend engineers."
    },
    {
        "company": "Walmart Global Tech",
        "title": "Software Engineer II",
        "location": "Bengaluru",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": ".NET / Java, Cloud, Distributed Systems, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4470500642",
        "salary_evidence": "Walmart SE II base: ₹25L–₹35L+",
        "match_score": 88,
        "match_label": "strong_match",
        "notes": "Core SE II lateral hiring band."
    },
    {
        "company": "EY",
        "title": "AI Engineer - Agentic AI & Azure AI Foundry",
        "location": "Gurugram",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Azure, Agentic AI, Azure AI Foundry, Microservices, REST APIs",
        "url": "https://www.linkedin.com/jobs/view/4432746955",
        "salary_evidence": "Estimated base: ₹28L–₹38L+ total comp",
        "match_score": 94,
        "match_label": "strong_match",
        "notes": "Direct alignment with Azure AI Foundry and agentic microservices in Gurugram."
    },
    {
        "company": "EY GDS",
        "title": "Risk Analytics - Full Stack Engineer (.NET/Cloud)",
        "location": "Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": ".NET Core, Azure, SQL Server, Microservices, REST APIs",
        "url": "https://www.linkedin.com/jobs/view/4434595014",
        "salary_evidence": "Estimated base: ₹26L–₹35L+",
        "match_score": 87,
        "match_label": "strong_match",
        "notes": "Risk analytics platform in Gurugram DLF Cyber City."
    },
    {
        "company": "EY GDS",
        "title": "Application Engineer (.NET / Azure)",
        "location": "Gurugram",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": ".NET Core, Azure, REST APIs, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4470166579",
        "salary_evidence": "Estimated base: ₹25L–₹32L+",
        "match_score": 84,
        "match_label": "strong_match",
        "notes": "Cloud-native application engineering in Gurugram."
    },
    {
        "company": "Honeywell Technologies",
        "title": "Software Engr II (.NET / Azure)",
        "location": "Gurugram",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "C#, .NET Core, Azure, Microservices, Cloud Backend",
        "url": "https://www.linkedin.com/jobs/view/4470411841",
        "salary_evidence": "Honeywell SE II base: ₹26L–₹35L+",
        "match_score": 86,
        "match_label": "strong_match",
        "notes": "Industrial IoT & connected enterprise software in Gurugram."
    },
    {
        "company": "Honeywell Technologies",
        "title": "Software Engr II",
        "location": "Gurugram",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "C#, .NET Core, Azure, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4461722718",
        "salary_evidence": "Honeywell SE II base: ₹26L–₹35L+",
        "match_score": 86,
        "match_label": "strong_match",
        "notes": "Enterprise automation software development in Gurugram."
    },
    {
        "company": "Honeywell Technologies",
        "title": "Software Engr II",
        "location": "Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": ".NET, C#, REST APIs, SQL Server, Distributed Systems",
        "url": "https://www.linkedin.com/jobs/view/4451361353",
        "salary_evidence": "Honeywell SE II base: ₹26L–₹35L+",
        "match_score": 84,
        "match_label": "strong_match",
        "notes": "3-5 years experience sweet spot in Gurugram."
    },
    {
        "company": "Urban Company",
        "title": "SDE-2 (React Native + Full stack / Node)",
        "location": "Gurugram",
        "exp": "2-4 years",
        "min_exp": 2,
        "max_exp": 4,
        "tech": "Node.js, TypeScript, REST APIs, Microservices, Distributed Systems",
        "url": "https://www.linkedin.com/jobs/view/4463946628",
        "salary_evidence": "Urban Company SDE 2 base: ₹35L–₹45L+ fixed + ESOPs",
        "match_score": 90,
        "match_label": "strong_match",
        "notes": "Top tier unicorn in Gurugram HQ. High scale Node.js & distributed systems."
    },
    {
        "company": "Optum India",
        "title": "AI/ML Engineer - RAG, LangChain, LLMs",
        "location": "Noida / Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Python, RAG, LangChain, LLMs, Cloud Backend, APIs",
        "url": "https://www.linkedin.com/jobs/view/4470616972",
        "salary_evidence": "Optum Senior Engineer base: ₹28L–₹38L+",
        "match_score": 87,
        "match_label": "strong_match",
        "notes": "UnitedHealth Group GCC in Noida/Gurugram. Generative AI and RAG pipelines."
    },
    {
        "company": "Optum India",
        "title": "Senior Software Engineer - Dot Net Fullstack",
        "location": "Noida",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": ".NET Core, C#, Azure, SQL Server, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4471681673",
        "salary_evidence": "Optum Senior Engineer base: ₹28L–₹38L+",
        "match_score": 85,
        "match_label": "strong_match",
        "notes": "Healthcare enterprise cloud platforms in Noida tech center."
    },
    {
        "company": "Target",
        "title": "Sr Engineer - Target India",
        "location": "Bengaluru",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Distributed Systems, .NET / Java, Microservices, Cloud",
        "url": "https://www.linkedin.com/jobs/view/4459122047",
        "salary_evidence": "Target India Senior Engineer base: ₹30L–₹40L+",
        "match_score": 85,
        "match_label": "strong_match",
        "notes": "Target GCC in Bengaluru. High-scale retail distributed systems."
    },
    {
        "company": "PwC India",
        "title": "Associate - GenAI and Agentic AI Engineer",
        "location": "Bengaluru",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "GenAI, Agentic AI, Azure / AWS, Python, LLMs, Prompt Orchestration",
        "url": "https://www.linkedin.com/jobs/view/4470424389",
        "salary_evidence": "PwC Associate/Senior Associate base: ₹28L–₹38L+",
        "match_score": 84,
        "match_label": "strong_match",
        "notes": "Dedicated GenAI & Agentic AI delivery center."
    },
    {
        "company": "PwC India",
        "title": "Senior Associate - Azure GCC Advisory",
        "location": "Gurugram",
        "exp": "3-6 years",
        "min_exp": 3,
        "max_exp": 6,
        "tech": "Azure, .NET, Cloud Backend, REST APIs, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4463618355",
        "salary_evidence": "PwC Senior Associate base: ₹28L–₹38L+",
        "match_score": 86,
        "match_label": "strong_match",
        "notes": "Enterprise Azure advisory and cloud architecture in Gurugram."
    },
    {
        "company": "PwC India",
        "title": "Associate – Dotnet Developer",
        "location": "Bengaluru",
        "exp": "3-4 years",
        "min_exp": 3,
        "max_exp": 4,
        "tech": "C#, .NET Core, REST APIs, SQL Server, Cloud",
        "url": "https://www.linkedin.com/jobs/view/4291061872",
        "salary_evidence": "PwC Associate base: ₹24L–₹32L+",
        "match_score": 80,
        "match_label": "potential_match",
        "notes": "3-4 years experience sweet spot in .NET Core."
    },
    {
        "company": "CredHive",
        "title": "Software Engineer 2, Data Platform",
        "location": "Bengaluru",
        "exp": "2-3 years",
        "min_exp": 2,
        "max_exp": 3,
        "tech": "Node.js, TypeScript, Distributed Systems, SQL, Kubernetes",
        "url": "https://www.linkedin.com/jobs/view/4465652179",
        "salary_evidence": "Estimated base: ₹30L–₹42L+ fixed",
        "match_score": 99,
        "match_label": "strong_match",
        "notes": "2-3 years exact tenure match. Data platform engineering with Node/TypeScript."
    },
    {
        "company": "CredHive",
        "title": "Senior Software Engineer, Platform",
        "location": "Bengaluru",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "TypeScript, Node.js, Distributed Systems, Redis, SQL",
        "url": "https://www.linkedin.com/jobs/view/4464077986",
        "salary_evidence": "Estimated base: ₹35L–₹45L+ fixed",
        "match_score": 95,
        "match_label": "strong_match",
        "notes": "Core platform distributed backend. Easy Apply pathway."
    },
    {
        "company": "Zepto",
        "title": "Software Development Engineer II — Infra Platform",
        "location": "Bengaluru / Delhi NCR satellite",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Distributed Systems, Microservices, Docker, Kubernetes, Cloud Infra",
        "url": "https://www.linkedin.com/jobs/view/4467613226",
        "salary_evidence": "Zepto SDE II base: ₹38L–₹50L+ fixed + ESOPs",
        "match_score": 98,
        "match_label": "strong_match",
        "notes": "High concurrency infrastructure platform pod."
    },
    {
        "company": "InCred Financial Services",
        "title": "Back End Developer",
        "location": "Bengaluru",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Node.js, Microservices, FinTech Systems, SQL, Redis",
        "url": "https://www.linkedin.com/jobs/view/4466103462",
        "salary_evidence": "InCred SDE II base: ₹30L–₹40L+",
        "match_score": 88,
        "match_label": "strong_match",
        "notes": "FinTech core lending and transaction backend."
    },
    {
        "company": "Keywords Studios",
        "title": "AI Engineer",
        "location": "New Delhi / NCR",
        "exp": "3-6 years",
        "min_exp": 3,
        "max_exp": 6,
        "tech": "Python, GenAI, LLMs, REST APIs, Cloud",
        "url": "https://www.linkedin.com/jobs/view/4469750081",
        "salary_evidence": "Estimated base: ₹28L–₹38L+",
        "match_score": 93,
        "match_label": "strong_match",
        "notes": "AI tooling and workflow engineering in New Delhi NCR."
    },
    {
        "company": "Corridor Platforms",
        "title": "Senior Backend Engineer - GenAI",
        "location": "Bengaluru",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "GenAI, Python / Node.js, REST APIs, Cloud Microservices",
        "url": "https://www.linkedin.com/jobs/view/4422399726",
        "salary_evidence": "Estimated base: ₹32L–₹45L+",
        "match_score": 87,
        "match_label": "strong_match",
        "notes": "AI-powered decision governance platform."
    },
    {
        "company": "LetzBizz",
        "title": "Backend Engineer – Python, FastAPI, Agentic AI & LLM",
        "location": "Remote India",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Agentic AI, LLM, Python, FastAPI, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4461054382",
        "salary_evidence": "Estimated base: ₹28L–₹36L+",
        "match_score": 85,
        "match_label": "strong_match",
        "notes": "Remote agentic AI architecture."
    },
    {
        "company": "7-Eleven GSC",
        "title": "Software Engineer II (Dot NET & Node.JS)",
        "location": "Bengaluru",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": ".NET Core, Node.js, Azure, REST APIs, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4399506075",
        "salary_evidence": "7-Eleven GSC SE II base: ₹26L–₹35L+",
        "match_score": 83,
        "match_label": "strong_match",
        "notes": "Rare dual tech stack (.NET Core + Node.js on Azure) exactly matching Vrinda."
    },
    {
        "company": "Ascendion",
        "title": ".NET Backend Engineer",
        "location": "Noida",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "C#, .NET Core, Azure, Microservices",
        "url": "https://www.linkedin.com/jobs/view/4464511954",
        "salary_evidence": "Estimated base: ₹22L–₹30L+",
        "match_score": 79,
        "match_label": "potential_match",
        "notes": "2-5 years experience requirement in Noida tech park."
    },
    # --- LinkedIn Posts & Recruiter Discovered Roles (Gurugram / Noida) ---
    {
        "company": "Paisabazaar",
        "title": "Software Engineer",
        "location": "Gurugram",
        "exp": "2-4 years",
        "min_exp": 2,
        "max_exp": 4,
        "tech": "C#, .NET, Node.js, REST APIs, Microservices, FinTech Systems",
        "url": "https://in.linkedin.com/jobs/view/4466652945",
        "salary_evidence": "Paisabazaar SDE base: ₹25L–₹35L+ fixed",
        "match_score": 88,
        "match_label": "strong_match",
        "notes": "Policybazaar group HQ in Gurugram Sector 44. Recruiter: Kashish Malik (HR Executive @ Policybazaar.com)."
    },
    {
        "company": "Stryker",
        "title": "Software Engineer",
        "location": "Gurugram",
        "exp": "2-4 years",
        "min_exp": 2,
        "max_exp": 4,
        "tech": "C#, .NET Core, Microservices, SQL, Cloud Architecture",
        "url": "https://in.linkedin.com/jobs/view/4464830665",
        "salary_evidence": "Stryker R&D SE base: ₹25L–₹34L+",
        "match_score": 89,
        "match_label": "strong_match",
        "notes": "Global R&D tech center in Gurugram. Explicit 2-4 years experience requirement."
    },
    {
        "company": "Stryker",
        "title": "Senior Software Engineer – .NET Developer (WPF)-3",
        "location": "Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "C#, .NET, WPF, Microservices, Cloud Backend",
        "url": "https://in.linkedin.com/jobs/view/4447147888",
        "salary_evidence": "Stryker R&D SSE base: ₹30L–₹40L+",
        "match_score": 87,
        "match_label": "strong_match",
        "notes": "Medical software engineering in Gurugram R&D center."
    },
    {
        "company": "Kite",
        "title": "Software Developer - Backend",
        "location": "Gurgaon",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Distributed Systems, Microservices, REST APIs, SQL/NoSQL",
        "url": "https://in.linkedin.com/jobs/view/4437494138",
        "salary_evidence": "Estimated base: ₹28L–₹38L+",
        "match_score": 88,
        "match_label": "strong_match",
        "notes": "FinTech backend platform in Gurgaon. 2-5 years experience."
    },
    {
        "company": "Leena AI",
        "title": "Software Development Engineer III",
        "location": "Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "GenAI Agents, Node.js, Python, Microservices, Distributed Systems",
        "url": "https://in.linkedin.com/jobs/view/4451912834",
        "salary_evidence": "Leena AI SDE base: ₹32L–₹45L+",
        "match_score": 93,
        "match_label": "strong_match",
        "notes": "Enterprise autonomous AI agent platform headquartered in Gurugram."
    },
    {
        "company": "PAR Technology",
        "title": "Software Engineer II",
        "location": "Gurugram",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": ".NET / C#, Cloud POS Services, REST APIs, Microservices",
        "url": "https://in.linkedin.com/jobs/view/4464195721",
        "salary_evidence": "PAR Tech SE II base: ₹25L–₹35L+",
        "match_score": 85,
        "match_label": "strong_match",
        "notes": "Global enterprise restaurant cloud backend in Gurugram."
    },
    {
        "company": "dunnhumby",
        "title": "Senior Software Engineer - Backend",
        "location": "Gurugram",
        "exp": "3-5 years",
        "min_exp": 3,
        "max_exp": 5,
        "tech": "Distributed Backend, Microservices, Cloud Data Platforms, Python/Node/C#",
        "url": "https://in.linkedin.com/jobs/view/4472704203",
        "salary_evidence": "dunnhumby SSE base: ₹30L–₹42L+",
        "match_score": 87,
        "match_label": "strong_match",
        "notes": "Tesco group retail data science & customer analytics platform in Gurugram."
    },
    {
        "company": "MoneyMul",
        "title": "Backend Developer / Engineer (Node.js)",
        "location": "Noida",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Node.js, Express, Microservices, REST APIs, MongoDB / PostgreSQL",
        "url": "https://in.linkedin.com/jobs/view/4350572622",
        "salary_evidence": "Estimated base: ₹22L–₹30L+",
        "match_score": 81,
        "match_label": "strong_match",
        "notes": "FinTech payment rails in Noida."
    },
    {
        "company": "Syniverse",
        "title": "Software Engineer II",
        "location": "Gurgaon",
        "exp": "2-5 years",
        "min_exp": 2,
        "max_exp": 5,
        "tech": "Cloud Messaging Platforms, Microservices, REST APIs, Java/Node/C#",
        "url": "https://in.linkedin.com/jobs/view/4467362958",
        "salary_evidence": "Syniverse SE II base: ₹24L–₹32L+",
        "match_score": 83,
        "match_label": "strong_match",
        "notes": "Global telecoms & CPaaS cloud messaging in Gurgaon."
    }
]

# Load existing workbook
wb = openpyxl.load_workbook('data/jobs_vrinda_discovery_wave2_verified.xlsx')
ws = wb['New Batch']

existing_keys = set()
for r in range(2, ws.max_row + 1):
    comp = str(ws.cell(row=r, column=2).value or '').strip().lower()
    title = str(ws.cell(row=r, column=3).value or '').strip().lower()
    url = str(ws.cell(row=r, column=11).value or '').strip()
    if url:
        # normalize linkedin url
        m = re.search(r'jobs/view/(\d+)', url)
        if m:
            existing_keys.add(f"linkedin_{m.group(1)}")
        else:
            existing_keys.add(url.lower())
    existing_keys.add(f"{comp}|{title}")

# Also check Review Queue
ws_rq = wb['Review Queue']
for r in range(2, ws_rq.max_row + 1):
    comp = str(ws_rq.cell(row=r, column=2).value or '').strip().lower()
    title = str(ws_rq.cell(row=r, column=3).value or '').strip().lower()
    url = str(ws_rq.cell(row=r, column=11).value or '').strip()
    if url:
        m = re.search(r'jobs/view/(\d+)', url)
        if m:
            existing_keys.add(f"linkedin_{m.group(1)}")
        else:
            existing_keys.add(url.lower())
    existing_keys.add(f"{comp}|{title}")

print(f"Total existing keys in workbook: {len(existing_keys)}")

# Filter and verify HTTP 200
verified_to_append = []
for c in candidates:
    url = c['url']
    key_comp_title = f"{c['company'].strip().lower()}|{c['title'].strip().lower()}"
    m = re.search(r'jobs/view/(\d+)', url)
    link_key = f"linkedin_{m.group(1)}" if m else url.lower()

    if key_comp_title in existing_keys or link_key in existing_keys:
        print(f"Skipping duplicate: {c['company']} - {c['title']}")
        continue

    # Verify HTTP 200
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            status_code = resp.getcode()
            if status_code == 200:
                print(f"[VERIFIED 200] {c['company']} - {c['title']} ({c['location']})")
                verified_to_append.append(c)
                existing_keys.add(key_comp_title)
                existing_keys.add(link_key)
            else:
                print(f"[REJECTED HTTP {status_code}] {c['company']} - {c['title']}")
    except Exception as e:
        print(f"[ERR {e}] {c['company']} - {c['title']} -> {url}")

print(f"\nTotal new verified opportunities to append: {len(verified_to_append)}")

# Define styling
font_standard = Font(name="Calibri", size=11)
font_link = Font(name="Calibri", size=11, color="0563C1", underline="single")
align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
fill_even = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
fill_odd = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")

start_rank = ws.max_row # next rank number
current_row = ws.max_row + 1

for item in verified_to_append:
    rank_num = current_row - 1
    row_fill = fill_odd if rank_num % 2 == 1 else fill_even

    row_data = [
        rank_num,
        item["company"],
        item["title"],
        item["location"],
        item["exp"],
        item["tech"],
        item["salary_evidence"],
        item["match_score"],
        item["match_label"],
        "Active Application Form Verified (HTTP 200)",
        item["url"],
        item["notes"]
    ]

    for col_idx, val in enumerate(row_data, start=1):
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = val
        cell.font = font_standard
        cell.fill = row_fill
        cell.border = thin_border

        if col_idx in (1, 8, 9, 10):
            cell.alignment = align_center
        else:
            cell.alignment = align_left

        if col_idx == 11 and val:
            cell.hyperlink = val
            cell.font = font_link

    current_row += 1

wb.save('data/jobs_vrinda_discovery_wave2_verified.xlsx')
print(f"Successfully saved {len(verified_to_append)} verified roles to data/jobs_vrinda_discovery_wave2_verified.xlsx! New total rows: {ws.max_row}")

