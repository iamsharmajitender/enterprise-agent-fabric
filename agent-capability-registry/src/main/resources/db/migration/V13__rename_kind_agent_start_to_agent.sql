-- Rename capability kind agent_start → agent. Idempotent if seed already used agent.
UPDATE registry.capabilities
SET kind = 'agent'
WHERE kind = 'agent_start';
