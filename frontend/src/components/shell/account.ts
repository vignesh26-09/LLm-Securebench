import { createContext, useContext } from "react";

export type User = { name: string; email: string };
export const Account = createContext<{ user: User; logout: () => void } | null>(null);
export function useAccount() { return useContext(Account); }
