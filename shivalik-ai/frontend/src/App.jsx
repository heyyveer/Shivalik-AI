
import { useEffect, useRef, useState } from "react";
import {
  GraduationCap,
  MessageSquare,
  Plus,
  Send,
  Menu,
  X,
  Bot,
  User,
  BookOpen,
  BriefcaseBusiness,
  Wallet,
  ArrowUpRight,
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { sendChatMessage } from "./services/api";

const suggestions = [
  {
    icon: BookOpen,
    title: "Admissions",
    question: "What is the admission process at Shivalik University?",
  },
  {
    icon: Wallet,
    title: "Fee Structure",
    question: "What is the BCA fee at Shivalik University?",
  },
  {
    icon: BriefcaseBusiness,
    title: "Placements",
    question: "What placement opportunities does Shivalik University offer?",
  },
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const requestControllerRef = useRef(null);
  const conversationIdRef = useRef(0);
  const backendSessionIdRef = useRef(null);
  const loadingRef = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  useEffect(() => {
    return () => {
      requestControllerRef.current?.abort();
    };
  }, []);

  const sendMessage = async (question = input) => {
    const text = question.trim();

    if (!text || loadingRef.current) return;

    const conversationId = conversationIdRef.current;
    const controller = new AbortController();

    requestControllerRef.current = controller;
    loadingRef.current = true;

    setMessages((previous) => [
      ...previous,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
      },
    ]);

    setInput("");
    setSidebarOpen(false);
    setIsLoading(true);

    try {
      const result = await sendChatMessage(
        text,
        controller.signal,
        backendSessionIdRef.current
      );

      if (conversationId !== conversationIdRef.current) {
        return;
      }

      // Store backend session ID for follow-up questions.
      backendSessionIdRef.current = result.conversation_id;

      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          sources: result.sources || [],
        },
      ]);
    } catch (error) {
      if (
        conversationId !== conversationIdRef.current ||
        error.name === "AbortError"
      ) {
        return;
      }

      console.error("Chat API error:", error);
      if (
        error.status === 400 &&
        error.message === "Unknown conversation session"
      ) {
        backendSessionIdRef.current = null;

        setMessages((previous) => [
          ...previous,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              "The server restarted, so your previous conversation context is no longer available. Please start a new chat.",
            sources: [],
            isError: true,
          },
        ]);

        return;
      }
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "Sorry, I couldn't process your request. Please try again.",
          sources: [],
          isError: true,
        },
      ]);
    } finally {
      if (conversationId === conversationIdRef.current) {
        loadingRef.current = false;
        requestControllerRef.current = null;
        setIsLoading(false);
      }
    }
  };

  const startNewChat = () => {
    conversationIdRef.current += 1;

    // Start a completely new backend conversation.
    backendSessionIdRef.current = null;

    requestControllerRef.current?.abort();
    requestControllerRef.current = null;
    loadingRef.current = false;

    setMessages([]);
    setInput("");
    setSidebarOpen(false);
    setIsLoading(false);
  };

  return (
    <div className="flex h-dvh bg-white text-slate-900">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-40 flex w-72 flex-col
          border-r border-slate-200 bg-slate-50
          transition-transform duration-200
          md:static md:translate-x-0
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="flex items-center justify-between px-5 py-6">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-700 p-2 text-white">
              <GraduationCap size={23} />
            </div>

            <div>
              <h1 className="text-lg font-bold">
                Shivalik AI
              </h1>
              <p className="text-xs text-slate-500">
                University Assistant
              </p>
            </div>
          </div>

          <button
            onClick={() => setSidebarOpen(false)}
            className="text-slate-500 md:hidden"
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4">
          <button
            onClick={startNewChat}
            className="flex w-full items-center justify-center gap-2
              rounded-xl bg-blue-700 px-4 py-3 font-medium text-white
              transition hover:bg-blue-800"
          >
            <Plus size={18} />
            New Chat
          </button>
        </div>

        <div className="mt-8 px-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Conversations
          </p>

          <div className="mt-4 flex items-center gap-3 rounded-lg bg-blue-50 px-3 py-3 text-sm text-blue-700">
            <MessageSquare size={17} />
            <span>Current Conversation</span>
          </div>
        </div>

        <div className="mt-auto border-t border-slate-200 px-5 py-5">
          <p className="text-xs text-slate-500">
            Powered by Retrieval-Augmented Generation
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Shivalik AI • Version 1.0
          </p>
        </div>
      </aside>

      {/* Main area */}
      <main className="flex min-w-0 flex-1 flex-col">
        {/* Header */}
        <header className="flex h-18 shrink-0 items-center justify-between border-b border-slate-100 px-5 md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-slate-600 md:hidden"
              aria-label="Open sidebar"
            >
              <Menu size={23} />
            </button>

            <div>
              <h2 className="font-semibold">
                Shivalik AI Assistant
              </h2>
              <p className="text-xs text-slate-500">
                Ask questions about university information
              </p>
            </div>
          </div>

          <span className="hidden rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 sm:block">
            AI Powered
          </span>
        </header>

        {/* Conversation */}
        <div className="min-h-0 flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-full max-w-4xl flex-col items-center justify-center px-5 py-12">
              <div className="mb-6 rounded-2xl bg-blue-50 p-5 text-blue-700">
                <GraduationCap size={40} />
              </div>

              <h2 className="text-center text-3xl font-bold tracking-tight md:text-4xl">
                Welcome to Shivalik AI
              </h2>

              <p className="mt-4 max-w-xl text-center text-slate-500">
                Your intelligent university assistant. Explore
                admissions, courses, fees, placements, and more.
              </p>

              <div className="mt-10 grid w-full gap-4 md:grid-cols-3">
                {suggestions.map((item) => {
                  const Icon = item.icon;

                  return (
                    <button
                      key={item.title}
                      onClick={() => sendMessage(item.question)}
                      className="group rounded-2xl border border-slate-200
                        bg-white p-5 text-left transition
                        hover:border-blue-300 hover:shadow-md"
                    >
                      <Icon
                        size={22}
                        className="text-blue-700"
                      />

                      <div className="mt-4 flex items-center justify-between">
                        <h3 className="font-semibold">
                          {item.title}
                        </h3>

                        <ArrowUpRight
                          size={17}
                          className="text-slate-400 group-hover:text-blue-700"
                        />
                      </div>

                      <p className="mt-2 text-sm text-slate-500">
                        {item.question}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-7 px-5 py-8">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                    }`}
                >
                  {message.role === "assistant" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                      <Bot size={19} />
                    </div>
                  )}

                  <div className="min-w-0 max-w-[85%]">
                    <div
                      className={`whitespace-pre-wrap break-words rounded-2xl px-5 py-3 text-sm leading-7 ${message.role === "user"
                        ? "bg-blue-700 text-white"
                        : message.isError
                          ? "bg-red-50 text-red-700"
                          : "bg-slate-100 text-slate-800"
                        }`}
                    >
                      {message.role === "assistant" && !message.isError ? (
                        <div className="space-y-3 [&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-1 [&_strong]:font-semibold [&_h1]:text-xl [&_h2]:text-lg [&_h3]:font-semibold [&_a]:text-blue-700 [&_a]:underline [&_table]:w-full [&_table]:text-left [&_th]:border [&_th]:p-2 [&_td]:border [&_td]:p-2">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({ node: _node, ...props }) => (
                                <a
                                  {...props}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                />
                              ),
                              table: ({ node: _node, ...props }) => (
                                <div className="overflow-x-auto">
                                  <table {...props} />
                                </div>
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        message.content
                      )}

                    </div>

                    {/* Source citations */}
                    {message.sources?.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold text-slate-500">
                          Sources
                        </p>

                        {message.sources.map((source) => (
                          <a
                            key={`${source.citation_id}-${source.url}`}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs text-blue-700 transition hover:border-blue-300 hover:bg-blue-50"
                          >
                            <span className="font-semibold">
                              [{source.citation_id}]
                            </span>

                            <span className="truncate">
                              {source.title || "University Source"}
                            </span>

                            <ArrowUpRight
                              size={14}
                              className="ml-auto shrink-0"
                            />
                          </a>
                        ))}
                      </div>
                    )}
                  </div>

                  {message.role === "user" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                      <User size={19} />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                    <Bot size={19} />
                  </div>

                  <div className="flex items-center gap-2 rounded-2xl bg-slate-100 px-5 py-4">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-blue-400 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-blue-300 [animation-delay:300ms]" />

                    <span className="ml-2 text-xs text-slate-500">
                      Shivalik AI is thinking...
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="shrink-0 border-t border-slate-100 bg-white px-4 py-4 md:px-8">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
            className="mx-auto flex max-w-3xl items-end gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm focus-within:border-blue-400"
          >
            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              disabled={isLoading}
              maxLength={2000}
              placeholder="Ask anything about Shivalik University..."
              rows={1}
              className="max-h-36 min-h-7 flex-1 resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-slate-400 disabled:opacity-60"
            />

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="rounded-xl bg-blue-700 p-3 text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </form>

          <p className="mx-auto mt-3 max-w-3xl text-center text-xs text-slate-400">
            AI-generated answers may contain errors. Verify important
            information with the university.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
