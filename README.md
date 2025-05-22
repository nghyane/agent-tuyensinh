# University Admissions Assistant Agent

An intelligent agent system built with Mastra.ai that provides automated assistance for university admissions processes, particularly tailored for Vietnamese universities.

## Features

- **Admissions Assistant**: Interactive AI agent to answer questions about academic programs, admission requirements, application deadlines, and campus life
- **Metadata Analysis**: Specialized agent for analyzing Vietnamese university admission documents
- **Vector Search**: RAG-based knowledge retrieval system for accurate information access
- **Multilingual Support**: Handles both English and Vietnamese queries

## Prerequisites

- Node.js (v16+)
- pnpm

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

Create vector indices:

```bash
pnpm index
```

### Building

Build for production:

```bash
pnpm build
```

## Project Structure

```
agent/
├── .mastra/             # Mastra.ai build artifacts
├── data/                # Knowledge base documents
├── src/
│   ├── mastra/
│   │   ├── agents/      # AI agent definitions
│   │   └── tools/       # Custom tools for agents
│   ├── scripts/         # Data ingestion and indexing scripts
│   ├── types/           # TypeScript type definitions
│   └── utils/           # Helper utilities
└── ...
```

## Technologies

- [Mastra.ai](https://mastra.ai/) - Agent framework
- [OpenAI](https://openai.com/) - LLM provider
- [LibSQL](https://turso.tech/libsql) - Vector database storage
- [TypeScript](https://www.typescriptlang.org/) - Programming language

## License

ISC 