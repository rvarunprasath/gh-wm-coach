import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GH Wealth Coach | AI Financial Advisory & Knowledge Graph",
  description: "Continuous Memory AI Financial Coach powered by Dual-Store Knowledge Graph & Relational Ledger",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-slate-100 min-h-screen antialiased selection:bg-emerald-500/30 selection:text-emerald-300">
        {children}
      </body>
    </html>
  );
}
