import './globals.css'
import { Sidebar } from '@/components/layout/Sidebar'
import Providers from './providers'

export const metadata = { title: 'Optitex Studio' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hu">
      <body className="bg-[#0e1117] text-gray-200">
        <Providers>
          <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}