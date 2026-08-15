import { useMemo, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import api, { getApiErrorMessage } from '../services/api'

export default function ChatPage() {
  const { user } = useAuth()
  const isDoctor = user?.role === 'DOCTOR'

  const [patientId, setPatientId] = useState('')
  const [doctorContext, setDoctorContext] = useState('Summarize the patient history for follow-up care.')
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: isDoctor
        ? 'Ask about this patient record, recent progress, diagnoses, medications, or follow-up planning.'
        : 'Ask about a patient record, medications, diagnoses, or recent reports.',
    },
  ])
  const [citations, setCitations] = useState([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const endpoint = useMemo(
    () => (isDoctor ? '/chat/doctor/ask' : '/chat/ask'),
    [isDoctor],
  )

  const submitQuestion = async () => {
    const trimmedQuestion = question.trim()
    const trimmedPatientId = patientId.trim()

    if (!trimmedQuestion) {
      setError('Please enter a question before sending.')
      return
    }

    if (!trimmedPatientId) {
      setError('Patient ID is required for this chat.')
      return
    }

    setError('')
    setMessages((current) => [...current, { role: 'user', content: trimmedQuestion }])
    setQuestion('')
    setIsSubmitting(true)

    try {
      const payload = {
        patient_id: trimmedPatientId,
        question: trimmedQuestion,
        include_patient_summary: true,
        include_medical_knowledge: false,
      }

      if (isDoctor) {
        payload.doctor_context = doctorContext.trim() || 'Summarize the patient history for follow-up care.'
      }

      const response = await api.post(endpoint, payload)
      const answer = response?.data?.answer || response?.data?.message || 'I could not produce an answer for this query.'

      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: answer,
        },
      ])
      setCitations(response?.data?.citations || [])
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
            <h1>{isDoctor ? 'Doctor patient summary assistant' : 'Grounded medical assistant'}</h1>
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
            placeholder='Patient ID (required)'
            value={patientId}
            onChange={(event) => setPatientId(event.target.value)}
          />

          {isDoctor ? (
            <textarea
              rows="2"
              placeholder="Doctor context (optional)"
              value={doctorContext}
              onChange={(event) => setDoctorContext(event.target.value)}
            />
          ) : null}

          <textarea
            rows="4"
            placeholder={isDoctor ? 'Ask about this patient history, symptoms, medications, or follow-up plan...' : 'Ask a clinical question...'}
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
          <li>{isDoctor ? 'Doctor mode uses approved patient access checks before retrieval.' : 'Recommended for clinician review with evidence attached.'}</li>
        </ul>

        {citations.length > 0 ? (
          <div>
            <h3>Evidence</h3>
            <ul className="bullet-list">
              {citations.map((citation, index) => (
                <li key={`${citation.source_type}-${index}`}>
                  <strong>{citation.title || citation.source_type}</strong>
                  <br />
                  <small>{citation.snippet}</small>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="mini-meta">
          <span>Signed in as</span>
          <strong>
            {user?.first_name} {user?.last_name}
          </strong>
          <small>{user?.role}</small>
        </div>
      </aside>
    </div>
  )
}
