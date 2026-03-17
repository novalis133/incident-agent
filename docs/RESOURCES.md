# IncidentAgent Resources

> Reference URLs and resources for the project

---

## DigitalOcean Gradient

### Documentation
- Platform Overview: https://docs.digitalocean.com/products/gradient-ai-platform/
- Agent Development Kit: https://docs.digitalocean.com/products/gradient-ai-platform/agents/
- Knowledge Bases: https://docs.digitalocean.com/products/gradient-ai-platform/knowledge-bases/
- Serverless Inference: https://docs.digitalocean.com/products/gradient-ai-platform/inference/
- GPU Droplets: https://docs.digitalocean.com/products/gpu-droplets/

### GitHub
- Gradient ADK: https://github.com/digitalocean/gradient-adk
- ADK Examples: https://github.com/digitalocean/gradient-adk-examples

### Hackathon
- DevPost Page: https://digitalocean.devpost.com/
- MLH Partner Page: https://www.mlh.com/partners/digitalocean
- Free Credits ($200): https://mlh.link/digitalocean-signup

---

## Open Source References

### HolmesGPT (Primary Reference)
- Repository: https://github.com/HolmesGPT/holmesgpt
- Documentation: https://holmesgpt.dev/
- License: Apache 2.0
- Stars: 1.8k
- Key Files:
  - Investigation loop: `holmes/core/investigation.py`
  - Toolsets: `holmes/plugins/toolsets/`
  - Runbooks: `holmes/core/runbooks.py`
  - CLI: `holmes_cli.py`

### Keep (Alert Ingestion)
- Repository: https://github.com/keephq/keep
- License: Apache 2.0
- Stars: 11.4k
- Key Feature: 100+ alert integrations

### Other Projects
- k8sgpt: https://github.com/k8sgpt-ai/k8sgpt
- Robusta: https://github.com/robusta-dev/robusta
- Drain3: https://github.com/logpai/Drain3
- AIOpsLab: https://github.com/microsoft/AIOpsLab
- Phoenix: https://github.com/Arize-ai/phoenix

---

## Academic Papers

### Core Papers (Must Read)

1. **Exploring LLM-based Agents for Root Cause Analysis**
   - Authors: Microsoft Research
   - Venue: FSE 2024
   - arXiv: https://arxiv.org/abs/2403.04123
   - PDF: https://arxiv.org/pdf/2403.04123

2. **RCAgent: Cloud Root Cause Analysis by Autonomous Agents**
   - Authors: Alibaba
   - Venue: CIKM 2024
   - arXiv: https://arxiv.org/abs/2310.16340
   - PDF: https://arxiv.org/pdf/2310.16340

3. **AIOps Solutions for Incident Management** (Survey)
   - arXiv: https://arxiv.org/abs/2404.01363
   - PDF: https://arxiv.org/pdf/2404.01363

4. **Agentic AIOps Framework**
   - Venue: MDPI Electronics, April 2025
   - URL: https://www.mdpi.com/2079-9292/14/9/1775

### Additional Papers

5. **Agentic Diagnostic Reasoning** (MCP-based)
   - arXiv: https://arxiv.org/abs/2601.07342

6. **TimeRAG** (Time-series + RAG)
   - arXiv: https://arxiv.org/abs/2601.04709

### Paper Collection
- Awesome LLM-AIOps: https://github.com/Jun-jie-Huang/awesome-LLM-AIOps

---

## Industry White Papers

1. **AIOps: Intelligent Advancement of IT Operations**
   - Source: AAC (August 2025)
   - URL: https://www.aac.com/wp-content/uploads/2025/08/AIOps-Intelligent-Advancement-of-IT-Operations-2.pdf

2. **AI Incident Tracker**
   - Source: MIT AI Risk Initiative
   - URL: https://airisk.mit.edu/ai-incident-tracker

---

## Competitor Analysis

### Funded Startups
| Company | Funding | URL |
|---------|---------|-----|
| Resolve AI | $125M | https://resolve.ai |
| NeuBird | $44.5M | https://neubird.ai |
| Cleric | $9.8M | https://cleric.io |
| Causely | $10M+ | https://causely.ai |

### Enterprise Platforms
| Platform | Feature |
|----------|---------|
| Datadog Bits AI | https://www.datadoghq.com/blog/bits-ai-sre/ |
| Dynatrace Davis AI | https://www.dynatrace.com/platform/artificial-intelligence/ |
| incident.io AI SRE | https://incident.io/ai-sre |
| BigPanda | https://www.bigpanda.io/ |
| LogicMonitor Edwin AI | https://www.logicmonitor.com/edwin-ai |

---

## Tools & Libraries

### Python Packages
```
gradient-adk>=0.1.4
langchain>=0.1.0
langgraph>=0.0.1
elasticsearch>=8.0.0
fastapi>=0.100.0
streamlit>=1.28.0
pydantic>=2.0.0
httpx>=0.25.0
```

### Evaluation Tools
- Braintrust: https://braintrust.dev/
- Arize Phoenix: https://github.com/Arize-ai/phoenix

---

## Demo Data Sources

### Public Datasets
- Loghub (log datasets): https://github.com/logpai/loghub
- AIOps Challenge: https://github.com/NetManAIOps

### Synthetic Data Generation
- Use templates from real incident reports
- Generate with realistic patterns
- Include multiple severity levels

---

## DevPost Submission

### Required
- [x] Project name
- [x] Elevator pitch (175 chars)
- [x] Full description (Markdown)
- [x] Tech stack list
- [x] GitHub URL
- [x] Demo video URL (~3 min)
- [ ] Screenshots/images

### Judging Criteria
1. Technological Implementation (25%)
2. Design / UX (25%)
3. Potential Impact (25%)
4. Quality / Creativity (25%)

---

## Contact & Support

- DigitalOcean Community: https://www.digitalocean.com/community
- Gradient Docs: https://docs.digitalocean.com/products/gradient-ai-platform/
- HolmesGPT Slack: https://cloud-native.slack.com/archives/C0A1SPQM5PZ
