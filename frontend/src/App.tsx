import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);
  
  // Global state for form configurations
  const [effort, setEffort] = useState("medium");
  const [model, setModel] = useState("google/gemini-2.5-pro-preview");


  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onFinish: (event: any) => {
      console.log("Stream finished:", event);
      console.log("Final processed events:", processedEventsTimeline);
      // Ensure finalize event is set if not already
      if (!hasFinalizeEventOccurredRef.current && processedEventsTimeline.length > 0) {
        hasFinalizeEventOccurredRef.current = true;
      }
    },
    onError: (error: any) => {
      console.error("Stream error:", error);
    },
    onUpdateEvent: (event: any) => {
      console.log("Received event:", event); // Debug log
      
      let processedEvent: ProcessedEvent | null = null;
      
      // Handle different event structures
      if (event.data && event.data.node) {
        const nodeData = event.data.output || event.data.input || {};
        const nodeName = event.data.node;
        
        switch (nodeName) {
          case "generate_query":
            if (nodeData.query_list) {
              processedEvent = {
                title: "Generating Search Queries",
                data: Array.isArray(nodeData.query_list) 
                  ? nodeData.query_list.join(", ")
                  : String(nodeData.query_list),
              };
            }
            break;
            
          case "web_research":
            if (nodeData.sources_gathered) {
              const sources = nodeData.sources_gathered || [];
              const numSources = sources.length;
              const uniqueLabels = [
                ...new Set(sources.map((s: any) => s.label || s.title || "").filter(Boolean)),
              ];
              const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
              processedEvent = {
                title: "Web Research",
                data: `Gathered ${numSources} sources${exampleLabels ? `. Related to: ${exampleLabels}` : ""}.`,
              };
            }
            break;
            
          case "reflection":
            if (nodeData.is_sufficient !== undefined) {
              processedEvent = {
                title: "Reflection",
                data: nodeData.is_sufficient
                  ? "Search successful, generating final answer."
                  : `Need more information${nodeData.follow_up_queries ? `, searching for ${nodeData.follow_up_queries.join(", ")}` : ""}`,
              };
            }
            break;
            
          case "finalize_answer":
            processedEvent = {
              title: "Finalizing Answer",
              data: "Composing and presenting the final answer.",
            };
            hasFinalizeEventOccurredRef.current = true;
            break;
        }
      }
      
      // Fallback to original structure for backward compatibility
      if (!processedEvent) {
        if (event.generate_query) {
          processedEvent = {
            title: "Generating Search Queries",
            data: event.generate_query.query_list?.join(", ") || "Generating queries...",
          };
        } else if (event.web_research) {
          const sources = event.web_research.sources_gathered || [];
          const numSources = sources.length;
          const uniqueLabels = [
            ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
          ];
          const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
          processedEvent = {
            title: "Web Research",
            data: `Gathered ${numSources} sources. Related to: ${
              exampleLabels || "N/A"
            }.`,
          };
        } else if (event.reflection) {
          processedEvent = {
            title: "Reflection",
            data: event.reflection.is_sufficient
              ? "Search successful, generating final answer."
              : `Need more information, searching for ${event.reflection.follow_up_queries?.join(
                  ", "
                ) || "additional information"}`,
          };
        } else if (event.finalize_answer) {
          processedEvent = {
            title: "Finalizing Answer",
            data: "Composing and presenting the final answer.",
          };
          hasFinalizeEventOccurredRef.current = true;
        }
      }
      
      if (processedEvent) {
        console.log("Adding processed event:", processedEvent); // Debug log
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    console.log("Messages effect triggered:", {
      messagesLength: thread.messages.length,
      isLoading: thread.isLoading,
      hasFinalizeEvent: hasFinalizeEventOccurredRef.current,
      eventsTimelineLength: processedEventsTimeline.length
    });

    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      console.log("Last message:", lastMessage);
      
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        console.log("Saving historical activities for message:", lastMessage.id);
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
      // Clear timeline after saving to historical
      setProcessedEventsTimeline([]);
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, newEffort?: string, newModel?: string) => {
      if (!submittedInputValue.trim()) return;
      
      // Update global state if new values are provided
      const currentEffort = newEffort || effort;
      const currentModel = newModel || model;
      
      if (newEffort && newEffort !== effort) setEffort(newEffort);
      if (newModel && newModel !== model) setModel(newModel);
      
      console.log("Submitting new query:", {
        input: submittedInputValue,
        effort: currentEffort,
        model: currentModel,
        currentMessagesLength: thread.messages?.length || 0
      });
      
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // convert effort to, initial_search_query_count and max_research_loops
      // low means max 1 loop and 1 query
      // medium means max 3 loops and 3 queries
      // high means max 10 loops and 5 queries
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      switch (currentEffort) {
        case "low":
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      console.log("Submitting to thread with config:", {
        messagesLength: newMessages.length,
        initial_search_query_count,
        max_research_loops,
        reasoning_model: currentModel,
      });

      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: currentModel,
      });
    },
    [thread, effort, model]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const handleNewSearch = useCallback(() => {
    // Optionally reset configurations to defaults
    setEffort("medium");
    setModel("google/gemini-2.5-pro-preview");
    window.location.reload();
  }, []);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">

        
        <div
          className={`flex-1 overflow-y-auto ${
            thread.messages.length === 0 ? "flex" : ""
          }`}
        >
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
              effort={effort}
              model={model}
              setEffort={setEffort}
              setModel={setModel}
            />
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
              effort={effort}
              model={model}
              setEffort={setEffort}
              setModel={setModel}
              onNewSearch={handleNewSearch}
            />
          )}
        </div>
      </main>
    </div>
  );
}
