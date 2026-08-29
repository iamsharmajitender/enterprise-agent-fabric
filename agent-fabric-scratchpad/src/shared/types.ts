export type ChatRow = {
  id?: string;
  route_id: string;
  autonomy_mode: number;
  label: string;
  claims: string[];
  message: string;
  hint_contains?: string;
  expected_message?: string;
  expected_status?: string;
};

export type JobRow = {
  route_id: string;
  autonomy_mode: number;
  label: string;
  claims: string[];
  payload: Record<string, unknown>;
  expected_message?: string;
};

export type Claims = {
  sub: string;
  emts: Record<string, boolean>;
};

export type ClarifyOption = {
  id: string;
  label?: string;
};

export type MessageRole = "user" | "assistant" | "system" | "error";
