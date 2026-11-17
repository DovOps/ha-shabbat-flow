# Implementation plan
1. Add provider-discovered, bounded read-only event adapter and pure snapshot assembler.
2. Expose authenticated upcoming-calendar endpoint through the existing panel bridge.
3. Default to a readable automatic summary; hide explicit manual override in Advanced settings.
4. Add synthetic regression/real-provider compatibility tests; package with a new static version.
5. Back up and upgrade installed integration, restart, verify sourced dated sunrise and summaries; commit and merge checkpoint.
