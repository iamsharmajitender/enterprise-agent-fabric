-- ticket_draft_reply — remove catalogue rows for this child route pack.

\c adp
DELETE FROM dataplane.routes WHERE route_id = 'ticket_draft_reply';
DELETE FROM dataplane.prompt_packs WHERE prompt_id = 'ticket_draft_reply';
