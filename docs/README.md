# 📚 FPT University 2025 - Documentation

This directory contains comprehensive documentation for the FPT University 2025 Student Admission System project.

## 📁 Directory Structure

```
docs/
├── README.md                           # This overview file
├── ROADMAP.md                          # Development roadmap & timeline
├── TECHNICAL_SPECS.md                  # Technical specifications
├── database/
│   ├── fpt_university_2025_init.sql   # Database schema (v2.1.0)
│   └── fpt_university_2025_data_migration.sql # Real FPT data
└── reference/
    └── fpt_university_2025_reference.md # Business requirements
```

## 🎯 Quick Start

### Database Setup
```bash
# Create database
createdb fpt_university

# Import MVP schema
psql -d fpt_university -f database/fpt_university_2025_mvp.sql
```

### Key Files

#### `database/fpt_university_2025_mvp.sql`
- **Purpose**: Production MVP database schema
- **Size**: ~300 lines (optimized)
- **Features**:
  - 6 core tables
  - 2 essential views
  - 2 utility functions
  - Complete 2025 official data

#### `reference/fpt_university_2025_reference.md`
- **Purpose**: Official FPT University 2025 data reference
- **Contents**:
  - Tuition fees by campus/program
  - Scholarship information
  - Admission methods
  - Contact information

## 🚀 MVP Architecture

### Core Tables
1. `programs` - All study programs
2. `campuses` - 5 campus locations
3. `progressive_tuition` - 3-tier pricing
4. `scholarships` - 2800 scholarships
5. `admission_methods` - 4 methods
6. `program_campus_availability` - Program availability matrix

### Key Functions
```sql
-- Get tuition information
SELECT * FROM get_tuition_info('AI', 'HN', 2025);

-- Search programs
SELECT * FROM search_programs('phần mềm');
```

## 📝 Notes

- **Aliases**: Handled by RAG/AI layer instead of database
- **Caching**: Application-level caching recommended
- **Complexity**: Focused on education domain only
- **Performance**: Optimized for read-heavy workload

## 🔄 Version History

- **v1.0 MVP** (Current) - Simplified schema for production
- **v2.1** (Archived) - Enterprise version with advanced features