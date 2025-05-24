# University Admissions Assistant Agent

An intelligent agent system built with Mastra.ai that provides automated assistance for university admissions processes, particularly tailored for Vietnamese universities.

## Features

- **Admissions Assistant**: Interactive AI agent to answer questions about academic programs, admission requirements, application deadlines, and campus life
- **Metadata Analysis**: Specialized agent for analyzing Vietnamese university admission documents
- **Vector Search**: RAG-based knowledge retrieval system using Google text-embedding-004 (768 dimensions)
- **Multilingual Support**: Handles both English and Vietnamese queries
- **Intent Detection**: Smart routing of queries to appropriate data sources

## Prerequisites

- Node.js (v16+)
- pnpm
- Google AI Studio API key (for embeddings - FREE tier available)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agent
```

2. Install dependencies:
```bash
pnpm install
```

3. Set up environment variables:
```bash
cp .env.development .env.local
```

4. Edit `.env.local` with your API keys and configuration

## Usage

### Development

Run the development server:

```bash
pnpm dev
```

### Data Management

Ingest knowledge documents:

```bash
pnpm ingest
```

Create vector indices with Google text-embedding-004:

```bash
pnpm index
```

Index intent examples for smart routing:

```bash
pnpm index-intents
```

### Building

Build for production:

```
```

## Technologies

- [Mastra.ai](https://mastra.ai/) - Agent framework
- [Google AI Studio](https://aistudio.google.com/) - Embedding provider (text-embedding-004)
- [OpenAI](https://openai.com/) - LLM provider
- [LibSQL](https://turso.tech/libsql) - Vector database storage
- [TypeScript](https://www.typescriptlang.org/) - Programming language

## Embedding Configuration

This project uses **Google text-embedding-004** which provides:
- **768 dimensions** (more efficient than OpenAI's 1536)
- **FREE usage** through Google AI Studio
- **Competitive performance** for most embedding tasks
- **Multilingual support** ideal for Vietnamese content