import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Contract Intelligence System',
  description: 'Automated contract parsing and intelligence system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

