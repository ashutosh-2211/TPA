import React from 'react';
import { motion } from 'framer-motion';
import { useChat } from '../../contexts/ChatContext';

const Sidebar: React.FC = () => {
  const { sessions, currentSession, createNewSession, switchSession } = useChat();

  const handleNewChat = () => {
    createNewSession();
  };

  const handleSessionClick = (sessionId: string) => {
    if (sessionId !== currentSession) {
      switchSession(sessionId);
    }
  };

  return (
    <motion.div className="sidebar glass">
      <div className="sidebar-header">
        <h3>Chat History</h3>
      </div>

      <motion.button
        className="new-chat-btn glass"
        onClick={handleNewChat}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        New Chat
      </motion.button>

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No chat history yet</p>
            <p className="empty-hint">Start a new conversation!</p>
          </div>
        ) : (
          sessions.map((session, index) => (
            <motion.div
              key={session.id}
              className={`session-item glass ${
                session.id === currentSession ? 'active' : ''
              }`}
              onClick={() => handleSessionClick(session.id)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.02, x: 4 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="session-icon">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <div className="session-content">
                <div className="session-title">{session.title}</div>
                <div className="session-date">
                  {new Date(session.createdAt).toLocaleDateString()}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default Sidebar;

