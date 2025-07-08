import type { Metadata } from "next";
import "./globals.css";
import ClientThemeProvider from "../components/ClientThemeProvider";

export const metadata: Metadata = {
  title: "AEB ➡️ HDR Compositor",
  description: "Web interface for HDR processing",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ClientThemeProvider>{children}</ClientThemeProvider>
      </body>
    </html>
  );
}
