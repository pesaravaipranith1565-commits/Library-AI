import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { studentAPI } from '../services/api';

const LibraryContext = createContext(null);

export function LibraryProvider({ children }) {
  const [currentStudent, setCurrentStudent] = useState(null);
  const [allStudents, setAllStudents] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadStudent = useCallback(async (id) => {
    try {
      const { data } = await studentAPI.getById(id);
      setCurrentStudent(data);
      localStorage.setItem('libraryai_student_id', id);
    } catch {
      localStorage.removeItem('libraryai_student_id');
    }
  }, []);

  // Persist selected student in localStorage
  useEffect(() => {
    const savedId = localStorage.getItem('libraryai_student_id');
    if (savedId) loadStudent(savedId);
  }, [loadStudent]);

  const selectStudent = useCallback((student) => {
    setCurrentStudent(student);
    if (student) {
      localStorage.setItem('libraryai_student_id', student.id);
    } else {
      localStorage.removeItem('libraryai_student_id');
    }
  }, []);

  const refreshStudents = useCallback(async () => {
    try {
      const { data } = await studentAPI.getAll();
      setAllStudents(data);
    } catch (err) {
      console.error('Failed to load students:', err);
    }
  }, []);

  useEffect(() => { refreshStudents(); }, [refreshStudents]);

  return (
    <LibraryContext.Provider value={{
      currentStudent,
      setCurrentStudent: selectStudent,
      allStudents,
      refreshStudents,
      loading,
      setLoading,
    }}>
      {children}
    </LibraryContext.Provider>
  );
}

export const useLibrary = () => {
  const ctx = useContext(LibraryContext);
  if (!ctx) throw new Error('useLibrary must be used inside LibraryProvider');
  return ctx;
};
