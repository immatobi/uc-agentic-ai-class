'use client'


import React, { useEffect, useState, useRef } from "react"
import { ArrowUpIcon } from "lucide-react";
import { UIPrompts } from "@/_data/seed";
import { motion, AnimatePresence } from 'framer-motion'
import Link from "next/link";
import useChat from "@/hooks/useChat";
import EmptyState from "@/components/EmptyState";
import ReactMarkdown from "react-markdown";
import helper from "@/utils/helper.util";
import { v4 as uuid } from 'uuid'

const ChatPage = ({ }) => {

    const msgEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLDivElement>(null);

    const { chat, loading } = useChat()

    const [input, setInput] = useState<string>('')
    const [chatStarted, setChatStarted] = useState<boolean>(false)

    const [question, setQuestion] = useState<string>('')
    const [customerId, setCustomerId] = useState<string>('')
    const [threadId, setThreadId] = useState<string>('')
    const [route, setRoute] = useState<string>('')
    const [answer, setAnswer] = useState<any>(null)
    const [review, setReview] = useState<any>(null)
    const [confidence, setConfidence] = useState<number | string>(0)
    const [priority, setPriority] = useState<string>('')
    const [team, setTeam] = useState<string>('')
    const [sources, setSources] = useState<Array<any>>([])
    const [memory, setMemory] = useState<Array<any>>([])

    useEffect(() => {

        let storedCID = localStorage.getItem("northstar_customer_id");
        let storedTID = localStorage.getItem("northstar_thread_id");

        if (!storedCID) {
            storedCID = uuid();
            localStorage.setItem("northstar_customer_id", storedCID);
        }

        if (!storedTID) {
            storedTID = uuid();
            localStorage.setItem("northstar_thread_id", storedTID);
        }

        setCustomerId(storedCID);
        setThreadId(storedTID);

        scrollToBottom()

    }, [])

    const scrollToBottom = () => {
        if (msgEndRef.current) {
            msgEndRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }

    const handlePromptClick = (text: string) => {
        setInput(text)
        if (inputRef.current) {
            inputRef.current.textContent = text;
        }
    }

    const handleChat = async (e: any) => {
        if (e) {
            e.preventDefault()
        }

        if (!input.trim() || loading) {
            return
        }

        const chatData = {
            question: input.trim(),
            customer_id: customerId,
            thread_id: threadId
        }

        setChatStarted(true)
        setInput('')
        const response = await chat(chatData)

        if (!response.error) {

            // setChatStarted(false)

            setQuestion(response.data.question || '')
            setRoute(response.data.route || '')
            setReview(response.data.review || null)
            setAnswer(response.data.answer || '')
            setConfidence(response.data.confidence || 0)
            setPriority(response.data.priority || '')
            setTeam(response.data.assigned_team || '')
            setSources(response.data.sources || [])
            setMemory(response.data.memory_updates || [])

        } else {

            // setChatStarted(false)

        }

    }

    return (
        <>
            <main className="w-full h-dvh bg-color-white">
                <div className="max-w-4xl mx-auto h-full">

                    <div className="relative h-full flex flex-col items-center">

                        {/* Message Section */}
                        <div className="flex-1 w-full max-w-3xl px-4">

                            {
                                !chatStarted &&
                                <>
                                    <div className="flex flex-col justify-end h-full space-y-8">
                                        <div className="text-center space-y-4">

                                            <h1 className="text-4xl font-mona-semibold text-gray-800">Hi there 👋</h1>
                                            <h2 className="text-xl text-gray-500 font-mona">What can i help you with?</h2>

                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-3 gap-y-4">

                                            <AnimatePresence>
                                                {
                                                    UIPrompts.map((prompt, index) => (
                                                        <motion.button
                                                            initial={{ opacity: 0, y: 20 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            whileTap={{ scale: 0.95 }}
                                                            transition={{ duration: 0.4, delay: index * 0.05, type: 'spring', bounce: 0.25 }}
                                                            key={index}
                                                            className="flex cursor-pointer items-center gap-3 p-4 text-left border border-gray-200 rounded-xl transition-all text-sm"
                                                            onClick={() => handlePromptClick(prompt.text)}
                                                        >
                                                            {prompt.icon}
                                                            <span className="text-gray-500">{prompt.text}</span>
                                                        </motion.button>
                                                    ))
                                                }
                                            </AnimatePresence>

                                        </div>
                                    </div>
                                </>
                            }

                            {
                                chatStarted &&
                                <>
                                    <motion.div
                                        animate={{ paddingBottom: input ? input.split('\n').length > 3 ? '260px' : '110px' : '80px' }}
                                        transition={{ duration: 0.2 }}
                                        className="pt-8 space-y-4"
                                    >
                                        <motion.div
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className={``}
                                        >
                                            {
                                                loading &&
                                                <EmptyState bgColor="bg-gray-50" className="h-[70vh] space-y-[1rem]">
                                                    <span className="loader lg primary"></span>
                                                    <p className="font-mona-medium text-gray-700">Thinking</p>
                                                </EmptyState>
                                            }

                                            {
                                                !loading &&
                                                <>
                                                    {
                                                        answer &&
                                                        <div className={`max-w-[100%] rounded-xl px-4 py-3 bg-gray-100`}>
                                                            <ReactMarkdown
                                                                components={{
                                                                    h2: ({ children }) => (
                                                                        <h2 className="mb-2 mt-4 text-base font-mona-semibold text-gray-900">
                                                                            {children}
                                                                        </h2>
                                                                    ),
                                                                    h3: ({ children }) => (
                                                                        <h3 className="mb-2 mt-3 text-sm font-mona-semibold text-gray-900">
                                                                            {children}
                                                                        </h3>
                                                                    ),
                                                                    p: ({ children }) => (
                                                                        <p className="mb-3 text-sm leading-6 text-gray-700">
                                                                            {children}
                                                                        </p>
                                                                    ),
                                                                    ul: ({ children }) => (
                                                                        <ul className="mb-3 list-disc space-y-1 pl-5 text-sm leading-6 text-gray-700">
                                                                            {children}
                                                                        </ul>
                                                                    ),
                                                                    ol: ({ children }) => (
                                                                        <ol className="mb-3 list-decimal space-y-1 pl-5 text-sm leading-6 text-gray-700">
                                                                            {children}
                                                                        </ol>
                                                                    ),
                                                                    li: ({ children }) => (
                                                                        <li className="pl-1">
                                                                            {children}
                                                                        </li>
                                                                    ),
                                                                    strong: ({ children }) => (
                                                                        <strong className="font-mona-semibold text-gray-900">
                                                                            {children}
                                                                        </strong>
                                                                    ),
                                                                    code: ({ children }) => (
                                                                        <code className="rounded bg-gray-200 px-1 py-0.5 text-[0.85em] text-gray-900">
                                                                            {children}
                                                                        </code>
                                                                    ),
                                                                    a: ({ href, children }) => (
                                                                        <a
                                                                            href={href}
                                                                            target="_blank"
                                                                            rel="noreferrer"
                                                                            className="text-blue-700 underline underline-offset-2"
                                                                        >
                                                                            {children}
                                                                        </a>
                                                                    ),
                                                                }}
                                                            >
                                                                {String(answer)}
                                                            </ReactMarkdown>
                                                        </div>
                                                    }
                                                    <div className="w-full py-[1.3rem]">

                                                        <div className="grid grid-cols-4 gap-x-[0.5rem]">
                                                            {
                                                                route &&
                                                                <div className="flex items-center gap-x-[0.2rem] bg-blue-50 py-[0.2rem] px-[0.4rem] rounded-full justify-center">
                                                                    <span className="font-mona-medium text-gray-500 text-[13px]">Route:</span>
                                                                    <span className="font-mona-medium text-gray-800 text-[13px]">{helper.capitalize(route) || ''}</span>
                                                                </div>
                                                            }
                                                            {
                                                                priority &&
                                                                <div className="flex items-center gap-x-[0.2rem] bg-blue-50 py-[0.2rem] px-[0.4rem] rounded-full justify-center">
                                                                    <span className="font-mona-medium text-gray-500 text-[13px]">Priority:</span>
                                                                    <span className="font-mona-medium text-gray-800 text-[13px]">{helper.capitalize(priority) || ''}</span>
                                                                </div>
                                                            }
                                                            {
                                                                team &&
                                                                <div className="flex items-center gap-x-[0.2rem] bg-blue-50 py-[0.2rem] px-[0.4rem] rounded-full justify-center">
                                                                    <span className="font-mona-medium text-gray-500 text-[13px]">Team:</span>
                                                                    <span className="font-mona-medium text-gray-800 text-[13px]">{helper.humanizeLabel(team) || ''}</span>
                                                                </div>
                                                            }
                                                            {
                                                                confidence &&
                                                                <div className="flex items-center gap-x-[0.2rem] bg-blue-50 py-[0.2rem] px-[0.4rem] rounded-full justify-center">
                                                                    <span className="font-mona-medium text-gray-500 text-[13px]">Confidence:</span>
                                                                    <span className="font-mona-medium text-gray-800 text-[13px]">{confidence.toString() || ''}</span>
                                                                </div>
                                                            }
                                                        </div>


                                                        {
                                                            sources && sources.length > 0 &&
                                                            <div className="mt-8">
                                                                <h2 className="mb-4 text-xl font-mona-semibold text-gray-800">Sources</h2>

                                                                <div className="grid gap-4 md:grid-cols-2">
                                                                    {sources.map((source, index) => (
                                                                        <div
                                                                            key={index}
                                                                            className="rounded-2xl border bg-white p-5 border-gray-100"
                                                                        >
                                                                            <div className="mb-2 inline-flex rounded-full bg-blue-400/10 px-3 py-1 text-[13px] font-mona-medium text-blue-500">
                                                                                {source.source}
                                                                            </div>

                                                                            <p className="line-clamp-4 text-sm leading-6 text-gray-400">
                                                                                {source.content_preview}
                                                                            </p>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        }

                                                    </div>
                                                </>
                                            }


                                        </motion.div>

                                        <div ref={msgEndRef} />

                                    </motion.div>
                                </>
                            }

                        </div>

                        {/* Input Section */}
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0, position: chatStarted ? "fixed" : 'relative' }}
                            className="w-full bg-white pb-4 pt-6 bottom-0 mt-auto"
                        >
                            <div className="max-w-3xl mx-auto px-4">

                                <motion.div
                                    animate={{ height: 'auto' }}
                                    whileFocus={{ scale: 0.1 }}
                                    transition={{ duration: 0.2 }}
                                    className="relative border border-gray-300 rounded-[8px] p-2.5 flex items-end gap-2 bg-color-white">
                                    <div
                                        ref={(elem) => {
                                            inputRef.current = elem;
                                            if (elem && !input) {
                                                elem.textContent = ''
                                            }
                                        }}
                                        contentEditable
                                        role="textbox"
                                        data-placeholder="Message..."
                                        className="text-gray-900 flex min-w-[94%] min-h-[36px] overflow-y-auto px-3 py-2 focus:outline-none text-sm bg-color-white rounded-[8px] empty:before:bg-pag-500 empty:before:content-[attr(data-placeholder] whitespace-pre-wrap break-words"
                                        onInput={(e) => {
                                            setInput(e.currentTarget.textContent || '')
                                            scrollToBottom()
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault()
                                                handleChat(e)
                                                scrollToBottom()
                                            }
                                        }}
                                    />
                                    <Link
                                        href={''}
                                        aria-label="Send message"
                                        className={`min-w-[2.2rem] min-h-[2.2rem] inline-flex items-center justify-center rounded-full cursor-pointer ${input ? 'bg-blue-700' : 'bg-gray-200'}`}
                                        onClick={(e) => {
                                            handleChat(e)
                                        }}
                                    >
                                        <ArrowUpIcon size={15} className="text-white" />
                                    </Link>
                                </motion.div>

                            </div>

                        </motion.div>

                    </div>

                </div>
            </main>
        </>
    );
}

export default ChatPage;
