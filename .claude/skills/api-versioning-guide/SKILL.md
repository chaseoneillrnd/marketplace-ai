---
name: api-versioning-guide
description: Use when making API changes that affect versioning or backward compatibility
---

# API Versioning Guide

## Current Convention

All endpoints: `/api/v1/...`

## Breaking vs Non-Breaking

Breaking (requires v2): removing fields, changing types, removing endpoints.
Non-breaking (safe in v1): adding optional fields, adding endpoints, adding query params.

## MCP Compatibility

MCP server is a consumer. Breaking API changes break MCP tools. Test both.

## References

- API routers: `apps/api/skillhub/routers/`
- MCP client: `apps/mcp-server/skillhub_mcp/api_client.py`
