import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, tokenStore, type User, type UserRole } from "./api";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (
    full_name: string,
    email: string,
    password: string,
    security_question: string,
    security_answer: string,
    role?: UserRole,
    phone?: string,
  ) => Promise<void>;
  signOut: () => void;
  refresh: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      return;
    }
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
      window.localStorage.setItem("mediai_user", JSON.stringify(data));
    } catch {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const raw = window.localStorage.getItem("mediai_user");
        if (raw) setUser(JSON.parse(raw));
        await fetchMe();
      } finally {
        setLoading(false);
      }
    })();
  }, [fetchMe]);

  const signIn = useCallback(async (email: string, password: string) => {
    const { data } = await api.post("/auth/login", { email, password });
    tokenStore.set(data.access_token, data.refresh_token);
    await fetchMe();
  }, [fetchMe]);

  const signUp = useCallback(
    async (
      full_name: string,
      email: string,
      password: string,
      security_question: string,
      security_answer: string,
      role: UserRole = "PATIENT",
      phone?: string,
    ) => {
      await api.post("/auth/register", {
        full_name, email, password, role, phone,
        security_question, security_answer,
      });
      await signIn(email, password);
    },
    [signIn],
  );

  const signOut = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  return (
    <Ctx.Provider value={{ user, loading, signIn, signUp, signOut, refresh: fetchMe }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth outside AuthProvider");
  return c;
}