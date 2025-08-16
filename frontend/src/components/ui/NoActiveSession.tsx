export const NoActiveSession = () => {
  return (
    <div className="no-session-message">
      <div className="message-content">
        <h2>No Active Session</h2>
        <p>Create a session from the sidebar to start coding</p>
        <div className="arrow-indicator">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M7 17l5-5-5-5M12 19h7" />
          </svg>
        </div>
      </div>
    </div>
  )
}