import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CampusPilot AI — Your AI Academic Companion",
  description: "An intelligent academic assistant that helps students understand subjects, explore study materials and prepare for examinations.",
  icons: {
    icon: "/logo.jpg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="h-full bg-[#FAFAF9] text-[#1C1917] selection:bg-[#E7E5E4] selection:text-[#0C0A09]">
        {children}
      </body>
    </html>
  );
}
