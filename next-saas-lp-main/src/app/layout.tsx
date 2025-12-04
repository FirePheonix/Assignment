import type { Metadata } from "next";
import { Instrument_Serif } from "next/font/google";
import "./globals.css";
import LenisProvider from "@/providers/lenis";
import ThemeProvider from "@/providers/theme";

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: ["400"],
});


export const metadata: Metadata = {
  title: "Next SaaS",
  description: "Change this"
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${instrumentSerif.className} antialiased w-full min-h-screen overflow-x-hidden`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <LenisProvider>
            {children}
          </LenisProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
