import { createContext, useContext, useEffect, useState } from "react";
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from "firebase/auth";

import { login as loginApi, setAuthToken } from "../api/invoiceApi";
import { auth } from "./firebaseConfig";

const AuthContext = createContext(null);

/**
 * 登入狀態與角色權限的全域 Context（前端狀態管理採用 React Context API，
 * 對應 docs/程式架構文件.md 的技術選型決定，MVP 規模不需要 Redux/Zustand）。
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // 後端回傳的使用者資料（含 role）
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (!firebaseUser) {
        setAuthToken(null);
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const firebaseToken = await firebaseUser.getIdToken();
        const { access_token, user: backendUser } = await loginApi(firebaseToken);
        setAuthToken(access_token);
        setUser(backendUser);
        setError(null);
      } catch (err) {
        setAuthToken(null);
        setUser(null);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    });

    return unsubscribe;
  }, []);

  const login = () => {
    setError(null);
    return signInWithPopup(auth, new GoogleAuthProvider()).catch((err) => {
      setError(`${err.code ?? "登入失敗"}：${err.message}`);
    });
  };
  const logout = () => signOut(auth);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth 必須在 AuthProvider 內使用");
  }
  return context;
}
