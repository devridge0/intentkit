# Changelog

## 2025-01-06

### New Features
- Optional JWT Authentication for admin API

### Improvements
- Refactor the core ai agent engine for better architecture
- Telegram entrypoint greeting message

### Bug Fixes
- Fix bug that agent config update not taking effect sometimes

## 2025-01-05

### Improvements
- Telegram entrypoint support regenerate token
- Telegram entrypoint robust error handling

## 2025-01-03

### Improvements
- Telegram entrypoint support dynamic enable and disable
- Better conversation behavior about the wallet

## 2025-01-02

### New Features
- System Prompt, It will affect all agents in a deployment.
- Nation number in Agent model

### Improvements
- Share agent memory between all public entrypoints
- Auto timestamp in db model

### Bug Fixes
- Fix bug in db create from scratch

## 2025-01-01

### Bug Fixes
- Fix Telegram group bug

## 2024-12-31

### New Features
- Telegram Entrypoint

## 2024-12-30

### Improvements
- Twitter Integration Enchancement

## 2024-12-28

### New Features
- Twitter Entrypoint
- Admin cron for quota clear
- Admin API get all agents

### Improvements
- Change lint tools to ruff
- Improve CI
- Improve twitter skills

### Bug Fixes
- Fix bug in db base code

## 2024-12-27

### New Features
- Twitter Skills
    - Get Mentions
    - Get Timeline
    - Post Tweet
    - Reply Tweet

### Improvements
- CI/CD refactoring for better security

## 2024-12-26

### Improvements
- Change default plan to "self-hosted" from "free", new agent now has 9999 message limit for testing
- Add a flag "DEBUG_RESP", when set to true, the Agent will respond with thought processes and time costs
- Better DB session management

## 2024-12-25

### Improvements
- Use Poetry as package manager
- Docker Compose tutorial in readme

## 2024-12-24

### New Features
- Multiple Agent Support
- Autonomous Agent Management
- Blockchain Integration (CDP for now, will add more)
- Extensible Skill System
- Extensible Plugin System
