# Citation Assistant Installation Guide

> This document is designed for AI Coding Agents to install the citation-assistant skill.

## Overview

This skill enables Claude Code to perform automated academic citation workflows using Semantic Scholar API with multi-dimensional quality ranking.

## Prerequisites

- Python 3.8+
- pip
- git
- Claude Code CLI installed

## Installation Steps

### Step 1: Create Skills Directory

```bash
mkdir -p ~/.claude/skills
```

### Step 2: Clone Repository

```bash
git clone https://github.com/ZhangNy301/citation-assistant.git ~/.claude/skills/citation-assistant
```

### Step 3: Install Python Dependencies

```bash
pip install python-dotenv requests impact_factor
```

Or using requirements.txt:

```bash
pip install -r ~/.claude/skills/citation-assistant/requirements.txt
```

### Step 4: Configure API Key

Create `.env` file from template:

```bash
cp ~/.claude/skills/citation-assistant/.env.example ~/.claude/skills/citation-assistant/.env
```

**Important**: The user needs to manually add their Semantic Scholar API Key to the `.env` file.

#### How to Get API Key (Free)

1. Visit https://www.semanticscholar.org/product/api
2. Scroll to the bottom and fill out the **API Key form** (api-key-form)
3. Submit - the API Key will be sent via email

#### Edit .env File

```bash
# Open the .env file in an editor
nano ~/.claude/skills/citation-assistant/.env

# Or directly set the key
echo 'S2_API_KEY=user_provided_key_here' > ~/.claude/skills/citation-assistant/.env
```

The `.env` file should contain:
```
S2_API_KEY=your_actual_api_key_here
```

**Note**: The skill works without API Key (anonymous mode with 10 req/min rate limit).

## Verification

### Check Installation

```bash
# Verify skill directory exists
ls -la ~/.claude/skills/citation-assistant/

# Verify SKILL.md exists (required for Claude Code to recognize the skill)
cat ~/.claude/skills/citation-assistant/SKILL.md

# Test Python imports
python3 -c "from dotenv import load_dotenv; import requests; print('Dependencies OK')"
```

### Test Skill Functionality

```bash
# Test CCF lookup
cd ~/.claude/skills/citation-assistant
python3 scripts/quality_ranker.py
```

Expected output: CCF info for TMI and ICML

## File Structure After Installation

```
~/.claude/skills/citation-assistant/
├── SKILL.md              # Skill definition (DO NOT MODIFY)
├── install.md            # This file
├── README.md             # User documentation
├── .env.example          # API Key template
├── .env                  # User's API Key (created from .env.example)
├── requirements.txt      # Python dependencies
├── data/
│   ├── ccf_2022.sqlite   # CCF ranking database
│   └── ccf_2022.jsonl    # CCF ranking data
├── scripts/
│   ├── s2_search.py
│   ├── quality_ranker.py
│   ├── doi_to_bibtex.py
│   └── tex_parser.py
└── references/
    ├── ccf_guide.md
    └── quality_metrics.md
```

## Post-Installation

1. **Restart Claude Code** to load the new skill
2. **Verify skill is loaded** by typing `/citation-assistant` in Claude Code
3. **Configure API Key** if not done already

## Troubleshooting

### Skill not recognized

- Ensure `SKILL.md` exists in `~/.claude/skills/citation-assistant/`
- Restart Claude Code
- Check file permissions

### Import errors

```bash
pip install --upgrade python-dotenv requests impact_factor
```

### API Key issues

- Verify `.env` file exists and contains `S2_API_KEY=xxx`
- Check for trailing spaces or quotes around the key

## Summary for Agent

After completing installation:
1. Confirm `~/.claude/skills/citation-assistant/SKILL.md` exists
2. Confirm Python dependencies are installed
3. Remind user to configure `S2_API_KEY` in `.env` file
4. Suggest restarting Claude Code

---

**Installation complete when**: User can trigger the skill with `/citation-assistant` in Claude Code.
