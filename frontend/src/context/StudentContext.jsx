import { createContext, useContext, useState, useEffect } from "react";

const StudentContext = createContext(null);

export function StudentProvider({ children }) {
  const [student, setStudentState] = useState(() => {
    try {
      const raw = localStorage.getItem("ai_teacher_student");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const setStudent = (s) => {
    setStudentState(s);
    try {
      if (s) localStorage.setItem("ai_teacher_student", JSON.stringify(s));
      else localStorage.removeItem("ai_teacher_student");
    } catch {
      /* ignore storage errors */
    }
  };

  return (
    <StudentContext.Provider value={{ student, setStudent }}>
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent() {
  const ctx = useContext(StudentContext);
  if (!ctx) throw new Error("useStudent must be used inside StudentProvider");
  return ctx;
}
