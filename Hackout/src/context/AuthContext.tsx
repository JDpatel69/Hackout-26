import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import type { User, UserRole } from '../types/models';
import { authService } from '../services/authService';

export interface AuthContextValue { user: User | null; role: UserRole | null; isAuthenticated: boolean; isLoading: boolean; signIn:(email:string,password:string)=>Promise<void>; signOut:()=>Promise<void>; refreshSession:()=>Promise<void>; }
export const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({children}:{children:React.ReactNode}) { const [user,setUser]=useState<User|null>(null); const [isLoading,setLoading]=useState(true);
  const refreshSession=useCallback(async()=>{ setLoading(true); try { const next=await authService.refreshSession();setUser(next.user); } catch { setUser(null); } finally { setLoading(false); } },[]);
  useEffect(()=>{void refreshSession();},[refreshSession]);
  const signIn=useCallback(async(email:string,password:string)=>{const next=await authService.signIn(email,password);setUser(next.user);},[]);
  const signOut=useCallback(async()=>{await authService.signOut();setUser(null);},[]);
  const value=useMemo(()=>({user,role:user?.role??null,isAuthenticated:Boolean(user),isLoading,signIn,signOut,refreshSession}),[user,isLoading,signIn,signOut,refreshSession]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
