import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HDR Compositor",
  description: "Web interface for HDR processing",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
