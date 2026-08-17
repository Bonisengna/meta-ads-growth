import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "DescompliADS", description: "Inteligência clara para campanhas Meta Ads." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
