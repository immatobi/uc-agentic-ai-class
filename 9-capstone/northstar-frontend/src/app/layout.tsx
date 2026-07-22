import type { Metadata } from "next";
import localFont from "next/font/local";
import "../../public/css/globals.css";
import "../../public/css/custom.css";
import "../../public/fonts/mona/style.css";
import { Suspense } from 'react'

const monasans = localFont({
    variable: "--font-mona-sans",
    display: "swap",
    src: [
        {
            path: "../../public/fonts/mona/MonaSans-ExtraLight.woff2",
            weight: "200",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Light.woff2",
            weight: "300",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Regular.woff2",
            weight: "400",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Italic.woff2",
            weight: "400",
            style: "italic",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Medium.woff2",
            weight: "500",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-SemiBold.woff2",
            weight: "600",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Bold.woff2",
            weight: "700",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-ExtraBold.woff2",
            weight: "800",
            style: "normal",
        },
        {
            path: "../../public/fonts/mona/MonaSans-Black.woff2",
            weight: "900",
            style: "normal",
        },
    ],
});

export const metadata: Metadata = {
    title: "Northstar AI",
    description: "Customer Support AI Agent for Northstar CRM",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html
            lang="en"
            className={`${monasans.variable} ${monasans.variable} ${monasans.variable} h-full antialiased`}
        >
            <body className="min-h-full flex flex-col antialiased body">
                <Suspense fallback={<></>}>
                    {children}
                </Suspense>
            </body>
        </html>
    );
}
