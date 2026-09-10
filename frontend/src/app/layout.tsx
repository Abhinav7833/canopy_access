import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/providers";
import { TopBar } from "@/components/layout/TopBar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Canopy",
  description: "Green-finance evidence for tracked assets.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      {/* Browser extensions (ColorZilla's `cz-shortcut-listen`, Grammarly, etc.) inject
          attributes onto <body> before React hydrates, which trips a hydration warning.
          suppressHydrationWarning only covers this element's own attributes, one level deep,
          so it silences the extension noise without hiding real mismatches in the tree. */}
      <body className="min-h-full bg-canvas text-ink" suppressHydrationWarning>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var k='canopy-theme';var t=localStorage.getItem(k);" +
              "if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}" +
              "document.documentElement.setAttribute('data-theme',t);}catch(e){}})();",
          }}
        />
        <Providers>
          <TopBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
