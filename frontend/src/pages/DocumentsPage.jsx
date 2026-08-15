import { useEffect, useRef, useState } from 'react'

import { useAuth } from '../context/AuthContext'
import api, { getApiErrorMessage } from '../services/api'

const documentTypeOptions = [
  'LAB_REPORT',
  'PRESCRIPTION',
  'DIAGNOSIS_REPORT',
  'RADIOLOGY_REPORT',
  'DISCHARGE_SUMMARY',
  'MEDICAL_HISTORY',
  'OTHER',
]

export default function DocumentsPage() {
  const { user, token } = useAuth()
  const fileInputRef = useRef(null)
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [patientId, setPatientId] = useState('')
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    document_type: 'OTHER',
  })

  const fetchDocuments = async (targetPatientId) => {
    if (!targetPatientId) {
      setDocuments([])
      setLoading(false)
      return
    }

    try {
      const response = await api.get(`/medical-documents/patients/${targetPatientId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      setDocuments(Array.isArray(response.data) ? response.data : response.data?.data || [])
    } catch (fetchError) {
      setError(getApiErrorMessage(fetchError))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    if (user.role === 'DOCTOR') {
      setPatientId('')
      setDocuments([])
      setLoading(false)
      return
    }

    const nextPatientId = user?.profile?.id || user?.profile?.patient_id || user?.profile?.patientId || ''
    setPatientId(nextPatientId)
    fetchDocuments(nextPatientId)
  }, [user, token])

  const handleUpload = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    const targetPatientId = user?.role === 'DOCTOR'
      ? patientId
      : user?.profile?.id || user?.profile?.patient_id || user?.profile?.patientId

    if (!targetPatientId) {
      setError('Please provide a patient ID before uploading a document.')
      return
    }

    if (!selectedFile) {
      setError('Please choose a file to upload.')
      return
    }

    setUploading(true)

    try {
      const uploadUrlResponse = await api.post(
        `/medical-documents/upload-url?file_name=${encodeURIComponent(selectedFile.name)}&mime_type=${encodeURIComponent(selectedFile.type || 'application/octet-stream')}&file_size=${selectedFile.size}`,
        {
          patient_id: targetPatientId,
          encounter_id: null,
          document_type: uploadForm.document_type,
          title: uploadForm.title || selectedFile.name,
          description: uploadForm.description || null,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )

      const payload = uploadUrlResponse.data || {}
      const documentId = payload.document_id || payload.data?.document_id
      const uploadUrl = payload.upload_url || payload.data?.upload_url

      if (!documentId || !uploadUrl) {
        throw new Error('The backend did not return a document upload URL.')
      }

      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': selectedFile.type || 'application/octet-stream',
        },
        body: selectedFile,
      })

      if (!uploadResponse.ok) {
        throw new Error('The file upload to storage failed.')
      }

      await api.post(
        `/medical-documents/${documentId}/confirm`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      )

      setSuccess('Document uploaded and queued for processing.')
      setUploadForm({ title: '', description: '', document_type: 'OTHER' })
      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      await fetchDocuments(targetPatientId)
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError))
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="screen-shell">
      <div className="page-header">
        <div>
          <span className="badge">Documents</span>
          <h1>Medical documents</h1>
        </div>
      </div>

      <section className="panel-card">
        <h2>Upload a medical document</h2>
        <form className="stack-form" onSubmit={handleUpload}>
          {user?.role === 'DOCTOR' ? (
            <>
              <label>
                <span>Patient ID</span>
                <input
                  value={patientId}
                  onChange={(event) => setPatientId(event.target.value)}
                  placeholder="Enter patient UUID"
                />
              </label>
              <button type="button" className="secondary-button" onClick={() => fetchDocuments(patientId)}>
                Load patient documents
              </button>
            </>
          ) : null}

          <div className="upload-grid">
            <label>
              <span>Document type</span>
              <select
                value={uploadForm.document_type}
                onChange={(event) => setUploadForm((current) => ({ ...current, document_type: event.target.value }))}
              >
                {documentTypeOptions.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>

            <label>
              <span>File</span>
              <input
                ref={fileInputRef}
                type="file"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
            </label>
          </div>

          <label>
            <span>Document title</span>
            <input
              value={uploadForm.title}
              onChange={(event) => setUploadForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="Optional title"
            />
          </label>

          <label>
            <span>Description</span>
            <textarea
              rows="4"
              value={uploadForm.description}
              onChange={(event) => setUploadForm((current) => ({ ...current, description: event.target.value }))}
              placeholder="Optional notes about this document"
            />
          </label>

          {selectedFile ? <p className="file-selected">Selected: {selectedFile.name}</p> : null}
          {error ? <p className="form-error">{error}</p> : null}
          {success ? <p className="success-message">{success}</p> : null}

          <button type="submit" className="primary-button" disabled={uploading}>
            {uploading ? 'Uploading...' : 'Upload document'}
          </button>
        </form>
      </section>

      {loading ? (
        <section className="panel-card">
          <p>Loading documents...</p>
        </section>
      ) : documents.length === 0 ? (
        <section className="panel-card">
          <p>No documents are available for this patient yet.</p>
        </section>
      ) : (
        <section className="panel-card">
          <div className="list-table">
            <div className="list-row list-header">
              <span>Title</span>
              <span>Type</span>
              <span>Status</span>
            </div>
            {documents.map((document) => (
              <div key={document.id || document.document_id} className="list-row">
                <span>{document.title || document.file_name || 'Untitled document'}</span>
                <span>{document.document_type || document.mime_type || 'OTHER'}</span>
                <span>{document.processing_status || document.status || 'PENDING'}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
