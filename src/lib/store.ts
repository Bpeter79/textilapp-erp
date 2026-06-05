import { create } from 'zustand'

type FilterState = {
  search: string
  clientId: string | null
  status: 'all' | 'terv' | 'jovahagyva' | 'gyartasban'
  set: (key: keyof Omit<FilterState, 'set'>, val: any) => void
  reset: () => void
}

export const useFilter = create<FilterState>((set) => ({
  search: '',
  clientId: null,
  status: 'all',
  set: (key, val) => set({ [key]: val }),
  reset: () => set({ search: '', clientId: null, status: 'all' })
}))