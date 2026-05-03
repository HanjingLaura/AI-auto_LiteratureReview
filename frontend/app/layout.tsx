import "./globals.css";

export const metadata = {
  title: "AI Literature Review",
  description: "LangGraph-powered literature review",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
