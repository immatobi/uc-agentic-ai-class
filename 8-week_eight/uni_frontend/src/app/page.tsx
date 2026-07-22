"use client";

import { useEffect, useState } from "react";

export default function Home() {
    const [mounted, setMounted] = useState(false);
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    const isDisabled = mounted ? loading || !question.trim() : false;

    async function askQuestion() {
        if (!question.trim()) return;

        setLoading(true);
        setAnswer("");
        setSources([]);

        try {
            const response = await fetch("http://127.0.0.1:8000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ question }),
            });

            if (!response.ok) {
                throw new Error("Request failed");
            }

            const data = await response.json();

            setAnswer(data.answer);
            setSources(data.sources || []);
        } catch (error) {
            setAnswer("Sorry, something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 px-6 py-10 text-white">
            <div className="mx-auto max-w-4xl">
                <section className="mb-10 text-center">
                    <div className="mb-4 inline-flex rounded-full border border-blue-400/30 bg-blue-400/10 px-4 py-2 text-sm text-blue-200">
                        University AI Assistant
                    </div>

                    <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
                        Student Services RAG Assistant
                    </h1>

                    <p className="mx-auto mt-4 max-w-2xl text-slate-300">
                        Ask questions about tuition, GPA, registration, housing,
                        international students, financial aid, and campus support.
                    </p>
                </section>

                <section className="rounded-3xl border border-white/10 bg-white/10 p-6 shadow-2xl backdrop-blur">
                    <label className="mb-3 block text-sm font-medium text-slate-200">
                        Ask a university-related question
                    </label>

                    <textarea
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        placeholder="Example: What GPA do I need to graduate?"
                        rows={5}
                        className="w-full resize-none rounded-2xl border border-white/10 bg-slate-950/70 p-4 text-white outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30"
                    />

                    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <p className="text-sm text-slate-400">
                            Answers are generated from university knowledge base.
                        </p>

                        <button
                            onClick={askQuestion}
                            disabled={isDisabled}
                            className="rounded-2xl bg-blue-500 px-6 py-3 font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? "Thinking..." : "Ask Assistant"}
                        </button>
                    </div>
                </section>

                {answer && (
                    <section className="mt-8 rounded-3xl border border-emerald-400/20 bg-emerald-400/10 p-6 shadow-xl">
                        <div className="mb-3 flex items-center gap-2">
                            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-400/20">
                                ✨
                            </span>
                            <h2 className="text-xl font-semibold">Answer</h2>
                        </div>

                        <p className="whitespace-pre-line leading-8 text-slate-100">
                            {answer}
                        </p>
                    </section>
                )}

                {sources.length > 0 && (
                    <section className="mt-8">
                        <h2 className="mb-4 text-xl font-semibold">Sources</h2>

                        <div className="grid gap-4 md:grid-cols-2">
                            {sources.map((source, index) => (
                                <div
                                    key={index}
                                    className="rounded-2xl border border-white/10 bg-white/10 p-5 shadow-lg backdrop-blur"
                                >
                                    <div className="mb-2 inline-flex rounded-full bg-blue-400/10 px-3 py-1 text-sm font-medium text-blue-200">
                                        {source.source}
                                    </div>

                                    <p className="line-clamp-4 text-sm leading-6 text-slate-300">
                                        {source.content_preview}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </main>
    );
}