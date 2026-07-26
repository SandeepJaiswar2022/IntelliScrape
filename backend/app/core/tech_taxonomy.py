"""
Curated taxonomy of tech-stack keywords used to tag jobs during
ingestion (see app/services/job_extraction_service.py).

=== Why this exists ===
Greenhouse's API gives us a job title and a free-text HTML description --
nothing structured like "required skills". To offer a tech-stack filter,
we have to derive it ourselves by matching known terms against that
text. This module is the single source of truth for what we look for.

=== Structure ===
TECH_TAXONOMY maps a canonical display name (what gets stored and shown
in the UI, e.g. "PostgreSQL") to a list of alias strings that should all
resolve to that same canonical name when found in text (e.g. "postgres",
"postgresql", "psql"). The canonical name itself does NOT need to be
repeated in its own alias list -- it's matched automatically.

=== The false-positive problem, and how this handles it ===
A larger keyword list covers more real postings, but it also raises the
odds of matching a term by accident inside an unrelated word (e.g. "Go"
the language matching inside "going", or "R" matching almost anywhere).
Two mitigations:
  1. All matching in job_extraction_service.py uses strict boundary
     checks (no alphanumeric character immediately before/after the
     match) -- this alone rules out "Go" matching inside "going".
  2. Terms short enough to still be risky even with boundaries (single
     letters, very common short words) are listed in
     CASE_SENSITIVE_TERMS below and matched case-sensitively instead of
     the default case-insensitive matching -- "R" the language is
     almost always written capitalized in a tech context, so requiring
     the exact case rules out most accidental matches against ordinary
     prose.
This is a real, known limitation of rule-based extraction, not a bug:
some postings will be under-tagged (a skill mentioned in an unusual
phrasing won't match) and rare edge cases may still over-tag. Accepted
tradeoff for an MVP -- see the README for the upgrade path (LLM-based
extraction) if this ever becomes the bottleneck.
"""

TECH_TAXONOMY: dict[str, list[str]] = {
    # --- Languages ---
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Java": ["java"],
    "Go": ["golang"],  # bare "go" handled via CASE_SENSITIVE_TERMS below
    "Rust": ["rust"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "C": [],  # bare "C" handled via CASE_SENSITIVE_TERMS below
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "Scala": ["scala"],
    "R": [],  # case-sensitive only, see CASE_SENSITIVE_TERMS
    "Elixir": ["elixir"],
    "Haskell": ["haskell"],
    "Perl": ["perl"],
    "Dart": ["dart"],
    "Shell/Bash": ["bash", "shell scripting"],

    # --- Frontend frameworks ---
    "React": ["react", "reactjs", "react.js"],
    "Vue.js": ["vue", "vuejs", "vue.js"],
    "Angular": ["angular", "angularjs"],
    "Svelte": ["svelte"],
    "Next.js": ["nextjs", "next.js"],
    "Nuxt.js": ["nuxtjs", "nuxt.js"],
    "jQuery": ["jquery"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],

    # --- Backend frameworks ---
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Spring Boot": ["spring boot", "springboot", "spring framework"],
    "Node.js": ["nodejs", "node.js", "node"],
    "Express.js": ["expressjs", "express.js"],
    "Ruby on Rails": ["rails", "ruby on rails", "ror"],
    "ASP.NET": ["asp.net", "dotnet", ".net"],
    "Laravel": ["laravel"],
    "NestJS": ["nestjs", "nest.js"],

    # --- Databases ---
    "PostgreSQL": ["postgres", "postgresql", "psql"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongo", "mongodb"],
    "Redis": ["redis"],
    "SQLite": ["sqlite"],
    "Cassandra": ["cassandra"],
    "DynamoDB": ["dynamodb"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "Microsoft SQL Server": ["sql server", "mssql", "ms sql"],
    "Oracle Database": ["oracle database", "oracle db"],
    "Neo4j": ["neo4j"],
    "CockroachDB": ["cockroachdb"],

    # --- Cloud / infrastructure ---
    "AWS": ["aws", "amazon web services"],
    "Google Cloud Platform": ["gcp", "google cloud platform", "google cloud"],
    "Microsoft Azure": ["azure"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Docker": ["docker"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "Jenkins": ["jenkins"],
    "GitHub Actions": ["github actions"],
    "CircleCI": ["circleci"],
    "Nginx": ["nginx"],
    "Helm": ["helm"],

    # --- Data / ML ---
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Apache Spark": ["apache spark", "spark"],
    "Apache Airflow": ["apache airflow", "airflow"],
    "Apache Kafka": ["apache kafka", "kafka"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Hugging Face": ["hugging face", "huggingface"],
    "LangChain": ["langchain"],

    # --- Mobile ---
    "React Native": ["react native"],
    "Flutter": ["flutter"],
    "Android SDK": ["android sdk"],

    # --- Tools / misc ---
    "Git": ["git"],
    "GraphQL": ["graphql"],
    "gRPC": ["grpc"],
    "RabbitMQ": ["rabbitmq"],
    "Celery": ["celery"],
    "Webpack": ["webpack"],
    "Vite": ["vite"],
}

# Canonical tags that are too short / too easily confused with ordinary
# English words to safely match case-insensitively. Matched with exact
# case only -- see the module docstring above for the reasoning.
CASE_SENSITIVE_TERMS: set[str] = {"Go", "R", "C"}

# Fixed experience-level buckets, checked against the job title in this
# priority order (most senior/specific first) -- see
# job_extraction_service.py. Deliberately does NOT include a "Mid"
# catch-all for titles with no explicit level signal: guessing "Mid"
# for an unlabeled title would be asserting something the posting never
# said. Unlabeled titles simply get experience_level = None.
EXPERIENCE_LEVEL_PATTERNS: dict[str, list[str]] = {
    "Principal": ["principal"],
    "Staff": ["staff"],
    "Lead": ["lead", "manager", "head of", "director"],
    "Senior": ["senior", "sr."],
    "Mid": ["mid level", "mid-level", "midlevel"],
    "Entry": ["entry level", "entry-level", "junior", "jr."],
    "Intern": ["intern", "internship"],
}
