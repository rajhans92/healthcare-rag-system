import { useState } from 'react'

import { useAuth } from '../context/AuthContext'
import api, { getApiErrorMessage } from '../services/api'

export default function ChatPage() {
  const { user, token } = useAuth()
  const [patientId, setPatientId] = useState('')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Ask about a patient record, medications, diagnoses, or recent reports.',
    },
  ])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const submitQuestion = async () => {
    if (!question.trim()) {
      return
    }

    const trimmedQuestion = question.trim()
    const trimmedPatientId = patientId.trim()
    setError('')
    setMessages((current) => [...current, { role: 'user', content: trimmedQuestion }])
    setQuestion('')
    setIsSubmitting(true)

    try {
      const response = await api.post(
        '/chat/ask',
        {
          patient_id: trimmedPatientId || undefined,
          question: trimmedQuestion,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content:
            response?.data?.answer ||
            response?.data?.message ||
            'I could not produce an answer for this query.',
        },
      ])
    } catch (submitError) {
      setError(getApiErrorMessage(submitError))
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: 'I was unable to answer because the request failed. Please verify access and try again.',
        },
      ])
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="screen-shell chat-layout">
      <section className="panel-card chat-panel">
        <div className="page-header compact">
          <div>
            <span className="badge">Clinical chat</span>
            <h1>Grounded medical assistant</h1>
          </div>
        </div>

        <div className="chat-box">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`chat-bubble ${message.role}`}>
              {message.content}
            </div>
          ))}
        </div>

        {error ? <p className="form-error">{error}</p> : null}

        <div className="chat-controls">
          <input
            type="text"
            placeholder="Patient ID (optional for doctors with access)"
            value={patientId}
            onChange={(event) => setPatientId(event.target.value)}
          />
          <textarea
            rows="4"
            placeholder="Ask a clinical question..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button className="primary-button" onClick={submitQuestion} disabled={isSubmitting}>
            {isSubmitting ? 'Thinking...' : 'Send question'}
          </button>
        </div>
      </section>

      <aside className="panel-card sidebar-panel">
        <h2>Context notes</h2>
        <ul className="bullet-list">
          <li>Uses authorized patient context only.</li>
          <li>Retrieves structured facts and documents before answer generation.</li>
          <li>Recommended for clinician review with evidence attached.</li>
        </ul>
        <div className="mini-meta">
          <span>Signed in as</span>
          <strong>{user?.first_name} {user?.last_name}</strong>
          <small>{user?.role}</small>
        </div>
      </aside>
    </div>
  )
}
