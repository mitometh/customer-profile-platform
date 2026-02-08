# AI Engineer Assignment: Customer Insights Agent

## Overview

Build a small-scale "Customer 360" system that aggregates data from multiple sources and exposes it through an AI-powered conversational interface.

**Deadline:** 2 weeks from assignment date (expected effort: 2-3 days)

This assignment will be manually reviewed by our engineers to assess both your architectural thinking and hands-on implementation skills.

> **Note:** It is fine to use AI coding assistance for this challenge, although we will be checking the quality of the output, so it's up to you to review it.

---

## The Scenario


1. Ingest and store customer data from multiple sources
2. Allow an AI agent to answer natural language questions about customers
3. Provide a simple interface to interact with the agent

---

## Requirements

### Part 1: Architecture Document (submit as `ARCHITECTURE.md`)

Before coding, document your design decisions:

- **Data Model:** How will you structure the "Customer 360" schema? What tables/collections and relationships?
- **Pipeline Design:** How would this scale to handle real-time data from 5+ sources (Slack, Salesforce, Jira, etc.)? Describe the approach, not the implementation.
- **AI Strategy:** How will you prevent hallucination when the agent answers questions about customer data? What retrieval strategy will you use?
- **Trade-offs:** What shortcuts did you take for this assignment vs. what you'd do in production?

> *We're evaluating your ability to think through problems, not just code them.*

### Part 2: Working Implementation

#### Data Layer

- A database storing customer information from at least 2 simulated "sources":
  - **Source A - CRM Data:** Company name, contact person, email, contract value, signup date
  - **Source B - Activity Data:** Support tickets, meeting notes, or usage events (timestamp, type, description)
- Provide seed data for at least 5 customers with realistic activity history
- An API or query interface to retrieve customer data

#### AI Agent

- An agent that can answer natural language questions such as:
  - "What's the contract value for Acme Corp?"
  - "Show me recent activity for customers who signed up in 2024"
  - "Which customers have had support tickets in the last 30 days?"
- The agent must retrieve real data from your database (not make it up)
- Use any LLM (OpenAI, Anthropic, local model, etc.)

#### Interface

- A simple way to interact with the agent (CLI, web chat, or API endpoint)
- Show the data source/evidence alongside the agent's response

### General Requirements

- Include a `README.md` with:
  - Setup instructions (ideally `docker-compose up` or equivalent)
  - Example queries to test
  - Your reasoning on technical choices
- Use Python for backend logic
- Database choice is flexible (Postgres, SQLite, DuckDB, etc.)

---

## Bonus Ideas (optional, mention in README if not implemented)

- Implement a basic RAG pipeline with document embeddings
- Add a simple dashboard showing customer metrics
- Demonstrate how you'd handle a new data source being added
- Include tests for the data retrieval logic

---

## Evaluation Criteria

| Area                | What We're Looking For                                                        |
| ------------------- | ----------------------------------------------------------------------------- |
| Architecture Doc    | Clear thinking about data modeling, scalability, and AI reliability            |
| Data Foundation     | Clean schema design, realistic seed data, queryable API                       |
| AI Integration      | Agent retrieves real data, handles edge cases gracefully, shows sources        |
| Code Quality        | Readable, documented, follows best practices                                  |
| Pragmatism          | Ships a working v1; explains what production version would need               |
