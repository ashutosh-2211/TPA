import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { chatAPI, type ChatMessage, type ChatResponse } from '../services/api';

interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  lastMessage?: string;
}

interface ChatContextType {
  sessions: ChatSession[];
  currentSession: string | null;
  messages: ChatMessage[];
  dataStore: Record<string, any>;
  loading: boolean;
  createNewSession: () => void;
  switchSession: (sessionId: string) => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  sendMessageStream: (message: string, onChunk: (chunk: string) => void) => Promise<void>;
  clearCurrentData: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  // Load sessions from localStorage on mount
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('chat_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSession, setCurrentSession] = useState<string | null>(() => {
    return localStorage.getItem('current_session');
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [dataStore, setDataStore] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chat_sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Save current session to localStorage whenever it changes
  useEffect(() => {
    if (currentSession) {
      localStorage.setItem('current_session', currentSession);
    } else {
      localStorage.removeItem('current_session');
    }
  }, [currentSession]);

  // Load messages for current session when it changes
  useEffect(() => {
    const loadCurrentSession = async () => {
      if (currentSession) {
        try {
          const history = await chatAPI.getHistory(currentSession);
          // Convert backend message format to UI format
          const formattedMessages = history.messages.map((msg: any) => ({
            role: msg.role === 'human' ? 'user' : msg.role === 'ai' ? 'assistant' : msg.role,
            content: msg.content,
          }));
          setMessages(formattedMessages);
        } catch (error) {
          console.error('Failed to load session history:', error);
          // If history fails to load (e.g., new session), start with empty messages
          setMessages([]);
        }
      } else {
        setMessages([]);
      }
    };
    loadCurrentSession();
  }, [currentSession]); // Run when currentSession changes

  const generateSessionId = () => {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const createNewSession = () => {
    const newSessionId = generateSessionId();
    const newSession: ChatSession = {
      id: newSessionId,
      title: 'New Chat',
      createdAt: new Date(),
    };
    
    setSessions((prev) => [newSession, ...prev]);
    setCurrentSession(newSessionId);
    setMessages([]);
    setDataStore({});
  };

  const switchSession = async (sessionId: string) => {
    setLoading(true);
    try {
      // Just set the current session - the useEffect will handle loading messages
      setCurrentSession(sessionId);
    } catch (error) {
      console.error('Failed to switch session:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSessionTitle = (sessionId: string, firstMessage: string) => {
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              title: firstMessage.slice(0, 50) + (firstMessage.length > 50 ? '...' : ''),
              lastMessage: firstMessage,
            }
          : session
      )
    );
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    let sessionId = currentSession;
    
    // Create new session if none exists
    if (!sessionId) {
      sessionId = generateSessionId();
      const newSession: ChatSession = {
        id: sessionId,
        title: message.slice(0, 50) + (message.length > 50 ? '...' : ''),
        createdAt: new Date(),
        lastMessage: message,
      };
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSession(sessionId);
    } else if (messages.length === 0) {
      updateSessionTitle(sessionId, message);
    }

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response: ChatResponse = await chatAPI.sendMessage({
        message,
        thread_id: sessionId,
      });

      // Add assistant message with embedded data if available
      let messageContent = response.response;
      
      // If there's hotel data, append it to the message
      if (response.data_store?.hotels) {
        // Extract all hotel properties from all keys
        const allHotels: any[] = [];
        Object.values(response.data_store.hotels).forEach((hotelData: any) => {
          if (hotelData?.properties && Array.isArray(hotelData.properties)) {
            allHotels.push(...hotelData.properties);
          }
        });
        
        if (allHotels.length > 0) {
          messageContent += '\n\n__HOTEL_DATA__\n' + JSON.stringify(allHotels);
        }
      }
      
      // If there's flight data, append it
      if (response.data_store?.flights) {
        const allFlights: any[] = [];
        Object.values(response.data_store.flights).forEach((flightData: any) => {
          if (flightData?.flights && Array.isArray(flightData.flights)) {
            allFlights.push(...flightData.flights);
          }
        });
        
        if (allFlights.length > 0) {
          messageContent += '\n\n__FLIGHT_DATA__\n' + JSON.stringify(allFlights);
        }
      }
      
      // If there's news data, append it
      if (response.data_store?.news) {
        const allNews: any[] = [];
        Object.values(response.data_store.news).forEach((newsData: any) => {
          if (newsData?.articles && Array.isArray(newsData.articles)) {
            allNews.push(...newsData.articles);
          }
        });
        
        if (allNews.length > 0) {
          messageContent += '\n\n__NEWS_DATA__\n' + JSON.stringify(allNews);
        }
      }
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: messageContent,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setDataStore(response.data_store);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessageStream = async (message: string, onChunk: (chunk: string) => void) => {
    if (!message.trim()) return;

    let sessionId = currentSession;
    
    // Create new session if none exists
    if (!sessionId) {
      sessionId = generateSessionId();
      const newSession: ChatSession = {
        id: sessionId,
        title: message.slice(0, 50) + (message.length > 50 ? '...' : ''),
        createdAt: new Date(),
        lastMessage: message,
      };
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSession(sessionId);
    } else if (messages.length === 0) {
      updateSessionTitle(sessionId, message);
    }

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    // Add placeholder for assistant message
    const assistantMessageIndex = messages.length + 1;
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '',
      },
    ]);

    try {
      await chatAPI.sendMessageStream(
        {
          message,
          thread_id: sessionId,
        },
        (chunk) => {
          // Update the assistant message with new chunk
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: newMessages[assistantMessageIndex].content + chunk,
            };
            return newMessages;
          });
          onChunk(chunk);
        },
        (response) => {
          // Update with final response
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: response.response,
            };
            return newMessages;
          });
          setDataStore(response.data_store);
          setLoading(false);
        },
        (error) => {
          console.error('Stream error:', error);
          setMessages((prev) => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: 'Sorry, I encountered an error. Please try again.',
            };
            return newMessages;
          });
          setLoading(false);
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[assistantMessageIndex] = {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        };
        return newMessages;
      });
      setLoading(false);
    }
  };

  const clearCurrentData = async () => {
    try {
      await chatAPI.clearData();
      setDataStore({});
    } catch (error) {
      console.error('Failed to clear data:', error);
    }
  };

  const value: ChatContextType = {
    sessions,
    currentSession,
    messages,
    dataStore,
    loading,
    createNewSession,
    switchSession,
    sendMessage,
    sendMessageStream,
    clearCurrentData,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

