import "./globals.css";
import { Analytics } from "@vercel/analytics/react";

export default function RootLayout({ children }) {
  return (
    <html className="h-full w-full">
      <head>
        <link rel="icon" href="/logo.png" />
      </head>
      <body className="h-full w-full">
        {children}
        <Analytics />
      </body>
    </html>
  );
}