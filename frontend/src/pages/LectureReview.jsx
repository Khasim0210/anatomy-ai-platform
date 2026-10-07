import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";


const BACKEND_URL =
  "http://127.0.0.1:8000";


function LectureReview() {
  const navigate = useNavigate();


  // -------------------------------------------------------
  // FILE / DOCUMENT STATE
  // -------------------------------------------------------

  const [
    selectedFile,
    setSelectedFile,
  ] = useState(null);

  const [
    extractedText,
    setExtractedText,
  ] = useState("");

  const [
    claims,
    setClaims,
  ] = useState([]);

  const [
    documentId,
    setDocumentId,
  ] = useState(null);

  const [
    currentDocument,
    setCurrentDocument,
  ] = useState(null);


  // -------------------------------------------------------
  // SAVED DOCUMENTS STATE
  // -------------------------------------------------------

  const [
    savedDocuments,
    setSavedDocuments,
  ] = useState([]);

  const [
    loadingDocuments,
    setLoadingDocuments,
  ] = useState(false);

  const [
    loadingDocumentId,
    setLoadingDocumentId,
  ] = useState(null);

  const [
    deletingDocumentId,
    setDeletingDocumentId,
  ] = useState(null);


  // -------------------------------------------------------
  // GENERAL PAGE STATE
  // -------------------------------------------------------

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    reviewingClaimId,
    setReviewingClaimId,
  ] = useState(null);

  const [
    savingDecisionClaimId,
    setSavingDecisionClaimId,
  ] = useState(null);

  const [
    editingClaimId,
    setEditingClaimId,
  ] = useState(null);

  const [
    editCorrectionText,
    setEditCorrectionText,
  ] = useState("");


  // -------------------------------------------------------
  // AUTH HELPERS
  // -------------------------------------------------------

  const getProfessorToken = () => {
    return localStorage.getItem(
      "professor_token"
    );
  };


  const clearProfessorSession = () => {
    localStorage.removeItem(
      "professor_token"
    );

    localStorage.removeItem(
      "professor_email"
    );
  };


  const handleUnauthorized = () => {
    clearProfessorSession();

    navigate(
      "/professor/login",
      {
        replace: true,
      }
    );
  };


  const parseResponse = async (
    response
  ) => {
    let result = {};

    try {
      result =
        await response.json();
    } catch {
      result = {};
    }

    if (
      response.status === 401
    ) {
      handleUnauthorized();

      throw new Error(
        "Your professor session has expired. Please sign in again."
      );
    }

    return result;
  };


  // -------------------------------------------------------
  // NORMALIZE CLAIM
  // -------------------------------------------------------

  const normalizeClaim = (
    claim
  ) => {
    return {
      ...claim,

      ai_status:
        claim.ai_status ||
        "not_reviewed",

      reason:
        claim.ai_reason ||
        claim.reason ||
        "—",

      suggested_correction:
        claim.suggested_correction ||
        null,

      sources:
        claim.sources || [],

      instructor_decision:
        claim.instructor_decision ||
        "pending",

      professor_correction:
        claim.professor_correction ||
        null,

      reviewed_at:
        claim.reviewed_at ||
        null,
    };
  };


  // -------------------------------------------------------
  // LOAD SAVED DOCUMENT LIST
  // -------------------------------------------------------

  const loadSavedDocuments =
    async () => {

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      try {
        setLoadingDocuments(
          true
        );

        const response =
          await fetch(
            `${BACKEND_URL}/documents`,
            {
              method: "GET",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Could not load saved documents."
          );
        }

        setSavedDocuments(
          result.documents || []
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setLoadingDocuments(
          false
        );
      }
    };


  // -------------------------------------------------------
  // LOAD ONE SAVED DOCUMENT
  // -------------------------------------------------------

  const loadSavedDocument =
    async (savedDocumentId) => {

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      try {
        setLoadingDocumentId(
          savedDocumentId
        );

        setMessage("");

        setEditingClaimId(
          null
        );

        setEditCorrectionText(
          ""
        );

        const response =
          await fetch(
            `${BACKEND_URL}/documents/${savedDocumentId}/claims`,
            {
              method: "GET",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Could not load saved lecture."
          );
        }

        const preparedClaims =
          (result.claims || []).map(
            normalizeClaim
          );

        setClaims(
          preparedClaims
        );

        setDocumentId(
          result.document.id
        );

        setCurrentDocument(
          result.document
        );

        setExtractedText("");

        setMessage(
          `${result.total_claims} saved claims loaded from ${result.document.filename}.`
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setLoadingDocumentId(
          null
        );
      }
    };


  // -------------------------------------------------------
  // DELETE SAVED DOCUMENT
  // -------------------------------------------------------

  const deleteSavedDocument =
    async (document) => {

      const confirmed =
        window.confirm(
          `Delete "${document.filename}"?\n\nThis will also delete its saved claims, AI reviews, sources, and instructor decisions.`
        );

      if (!confirmed) {
        return;
      }

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      try {
        setDeletingDocumentId(
          document.id
        );

        setMessage("");

        const response =
          await fetch(
            `${BACKEND_URL}/documents/${document.id}`,
            {
              method: "DELETE",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Could not delete document."
          );
        }

        // If the document currently open on screen
        // was deleted, clear the review screen.
        if (
          documentId ===
          document.id
        ) {
          setClaims([]);

          setDocumentId(null);

          setCurrentDocument(null);

          setExtractedText("");

          setEditingClaimId(
            null
          );

          setEditCorrectionText(
            ""
          );
        }

        // Immediately remove it from the visible list.
        setSavedDocuments(
          (currentDocuments) =>
            currentDocuments.filter(
              (item) =>
                item.id !==
                document.id
            )
        );

        setMessage(
          `Document ${document.id} deleted successfully.`
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setDeletingDocumentId(
          null
        );
      }
    };


  // -------------------------------------------------------
  // LOAD DOCUMENT LIST WHEN PAGE OPENS
  // -------------------------------------------------------

  useEffect(() => {
    loadSavedDocuments();
  }, []);


  // -------------------------------------------------------
  // FILE SELECTION
  // -------------------------------------------------------

  const handleFileChange = (
    event
  ) => {
    const file =
      event.target.files[0];

    setSelectedFile(
      file || null
    );

    setExtractedText("");

    setClaims([]);

    setDocumentId(null);

    setCurrentDocument(null);

    setMessage("");

    setEditingClaimId(null);

    setEditCorrectionText("");
  };


  // -------------------------------------------------------
  // EXTRACT RAW DOCUMENT TEXT
  // -------------------------------------------------------

  const extractText =
    async () => {

      if (!selectedFile) {
        setMessage(
          "Please choose a DOCX or PDF file first."
        );

        return;
      }

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );

      try {
        setLoading(true);

        setMessage("");

        const response =
          await fetch(
            `${BACKEND_URL}/upload`,
            {
              method: "POST",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },

              body: formData,
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Document processing failed."
          );
        }

        setExtractedText(
          result.text
        );

        setMessage(
          `Document processed successfully. ${result.characters_extracted} characters extracted.`
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setLoading(false);
      }
    };


  // -------------------------------------------------------
  // EXTRACT CLAIMS + SAVE DOCUMENT
  // -------------------------------------------------------

  const extractClaimsFromDocument =
    async () => {

      if (!selectedFile) {
        setMessage(
          "Please choose a DOCX or PDF file first."
        );

        return;
      }

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );

      try {
        setLoading(true);

        setMessage("");

        const response =
          await fetch(
            `${BACKEND_URL}/analyze-claims`,
            {
              method: "POST",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },

              body: formData,
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Claim extraction failed."
          );
        }

        const preparedClaims =
          (result.claims || []).map(
            normalizeClaim
          );

        setDocumentId(
          result.document_id
        );

        setCurrentDocument({
          id:
            result.document_id,

          filename:
            result.filename,

          file_type:
            result.file_type,

          course_id:
            result.course?.id ??
            null,
        });

        setClaims(
          preparedClaims
        );

        setMessage(
          `${result.total_claims} claims extracted and saved successfully.`
        );

        await loadSavedDocuments();

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setLoading(false);
      }
    };


  // -------------------------------------------------------
  // REVIEW CLAIM WITH AI
  // -------------------------------------------------------

  const reviewClaimWithAI =
    async (claimId) => {

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      try {
        setReviewingClaimId(
          claimId
        );

        setMessage("");

        const response =
          await fetch(
            `${BACKEND_URL}/claims/${claimId}/review`,
            {
              method: "POST",

              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "AI review failed."
          );
        }

        setClaims(
          (currentClaims) =>
            currentClaims.map(
              (claim) =>
                claim.id === claimId
                  ? {
                      ...claim,

                      ai_status:
                        result.status,

                      reason:
                        result.reason,

                      suggested_correction:
                        result.suggested_correction,

                      sources:
                        result.sources || [],
                    }
                  : claim
            )
        );

        setMessage(
          `Claim ${claimId} reviewed and saved successfully.`
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setReviewingClaimId(
          null
        );
      }
    };


  // -------------------------------------------------------
  // SAVE PROFESSOR DECISION
  // -------------------------------------------------------

  const saveProfessorDecision =
    async (
      claimId,
      decision,
      professorCorrection = null
    ) => {

      const token =
        getProfessorToken();

      if (!token) {
        handleUnauthorized();
        return;
      }

      try {
        setSavingDecisionClaimId(
          claimId
        );

        setMessage("");

        const response =
          await fetch(
            `${BACKEND_URL}/claims/${claimId}/decision`,
            {
              method: "PATCH",

              headers: {
                "Content-Type":
                  "application/json",

                Authorization:
                  `Bearer ${token}`,
              },

              body: JSON.stringify({
                decision:
                  decision,

                professor_correction:
                  professorCorrection,
              }),
            }
          );

        const result =
          await parseResponse(
            response
          );

        if (!response.ok) {
          throw new Error(
            result.detail ||
              "Could not save professor decision."
          );
        }

        setClaims(
          (currentClaims) =>
            currentClaims.map(
              (claim) =>
                claim.id === claimId
                  ? {
                      ...claim,

                      instructor_decision:
                        result.decision,

                      professor_correction:
                        result.professor_correction,

                      reviewed_at:
                        result.reviewed_at,
                    }
                  : claim
            )
        );

        setEditingClaimId(
          null
        );

        setEditCorrectionText(
          ""
        );

        setMessage(
          `Professor decision saved for claim ${claimId}.`
        );

      } catch (error) {
        setMessage(
          error.message
        );

      } finally {
        setSavingDecisionClaimId(
          null
        );
      }
    };


  // -------------------------------------------------------
  // EDIT PROFESSOR CORRECTION
  // -------------------------------------------------------

  const startEditingCorrection =
    (claim) => {

      setEditingClaimId(
        claim.id
      );

      setEditCorrectionText(
        claim.professor_correction ||
          claim.suggested_correction ||
          ""
      );
    };


  const saveEditedCorrection =
    async (claimId) => {

      const cleanedText =
        editCorrectionText.trim();

      if (!cleanedText) {
        setMessage(
          "Please enter the professor-approved correction before saving."
        );

        return;
      }

      await saveProfessorDecision(
        claimId,
        "edited",
        cleanedText
      );
    };


  // -------------------------------------------------------
  // FORMAT AI STATUS
  // -------------------------------------------------------

  const formatAIStatus = (
    status
  ) => {

    if (
      status ===
      "likely_correct"
    ) {
      return "Likely Correct";
    }

    if (
      status ===
      "possible_error"
    ) {
      return "Possible Error";
    }

    if (
      status ===
      "needs_review"
    ) {
      return "Needs Review";
    }

    return "Not Reviewed";
  };


  const getAIStatusClass =
    (status) => {

      if (
        status ===
        "likely_correct"
      ) {
        return "status-likely-correct";
      }

      if (
        status ===
        "possible_error"
      ) {
        return "status-possible-error";
      }

      if (
        status ===
        "needs_review"
      ) {
        return "status-needs-review";
      }

      return "status-not-reviewed";
    };


  // -------------------------------------------------------
  // FORMAT PROFESSOR DECISION
  // -------------------------------------------------------

  const formatDecision = (
    decision
  ) => {

    if (
      decision === "accepted"
    ) {
      return "Accepted";
    }

    if (
      decision === "rejected"
    ) {
      return "Rejected";
    }

    if (
      decision === "edited"
    ) {
      return "Edited";
    }

    if (
      decision ===
      "needs_review"
    ) {
      return "Needs Review";
    }

    return "Pending";
  };


  // -------------------------------------------------------
  // FORMAT DATE
  // -------------------------------------------------------

  const formatDate = (
    value
  ) => {

    if (!value) {
      return "—";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return value;
    }

    return date.toLocaleString();
  };


  // -------------------------------------------------------
  // SUMMARY COUNTS
  // -------------------------------------------------------

  const totalClaims =
    claims.length;


  const aiReviewedCount =
    claims.filter(
      (claim) =>
        claim.ai_status &&
        claim.ai_status !==
          "not_reviewed"
    ).length;


  const likelyCorrectCount =
    claims.filter(
      (claim) =>
        claim.ai_status ===
        "likely_correct"
    ).length;


  const possibleErrorCount =
    claims.filter(
      (claim) =>
        claim.ai_status ===
        "possible_error"
    ).length;


  const aiNeedsReviewCount =
    claims.filter(
      (claim) =>
        claim.ai_status ===
        "needs_review"
    ).length;


  const notReviewedCount =
    totalClaims -
    aiReviewedCount;


  const pendingCount =
    claims.filter(
      (claim) =>
        !claim.instructor_decision ||
        claim.instructor_decision ===
          "pending"
    ).length;


  const acceptedCount =
    claims.filter(
      (claim) =>
        claim.instructor_decision ===
        "accepted"
    ).length;


  const rejectedCount =
    claims.filter(
      (claim) =>
        claim.instructor_decision ===
        "rejected"
    ).length;


  const editedCount =
    claims.filter(
      (claim) =>
        claim.instructor_decision ===
        "edited"
    ).length;


  const professorNeedsReviewCount =
    claims.filter(
      (claim) =>
        claim.instructor_decision ===
        "needs_review"
    ).length;


  // -------------------------------------------------------
  // PAGE
  // -------------------------------------------------------

  return (
    <div className="professor-page">

      <header className="professor-header">

        <div>

          <Link
            to="/professor"
            className="review-back-link"
          >
            ← Professor Dashboard
          </Link>

          <h1>
            Lecture Review
          </h1>

          <p>
            Human Anatomy
          </p>

        </div>

      </header>


      <main className="professor-content">

        {/* ============================================= */}
        {/* SAVED DOCUMENTS */}
        {/* ============================================= */}

        <section className="card">

          <h2>
            Saved Lecture Documents
          </h2>

          <p className="description">
            Reopen a previously analyzed lecture,
            continue reviewing it, or delete an
            outdated document.
          </p>


          <div className="actions">

            <button
              onClick={
                loadSavedDocuments
              }

              disabled={
                loadingDocuments
              }
            >
              {loadingDocuments
                ? "Loading..."
                : "Refresh Documents"}
            </button>

          </div>


          {savedDocuments.length ===
          0 ? (

            <p className="description">
              No saved lecture documents were found.
            </p>

          ) : (

            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>

                    <th>
                      Document ID
                    </th>

                    <th>
                      File
                    </th>

                    <th>
                      Type
                    </th>

                    <th>
                      Uploaded
                    </th>

                    <th>
                      Action
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {savedDocuments.map(
                    (document) => (

                      <tr
                        key={
                          document.id
                        }
                      >

                        <td>
                          {document.id}
                        </td>


                        <td className="claim-text">
                          {
                            document.filename
                          }
                        </td>


                        <td>
                          {
                            document.file_type
                          }
                        </td>


                        <td>
                          {
                            formatDate(
                              document.uploaded_at
                            )
                          }
                        </td>


                        <td>

                          <div
                            style={{
                              display:
                                "flex",

                              gap:
                                "8px",

                              flexWrap:
                                "wrap",
                            }}
                          >

                            <button
                              className="review-button"

                              onClick={() =>
                                loadSavedDocument(
                                  document.id
                                )
                              }

                              disabled={
                                loadingDocumentId !==
                                  null ||
                                deletingDocumentId !==
                                  null ||
                                loading
                              }
                            >
                              {loadingDocumentId ===
                              document.id
                                ? "Loading..."
                                : documentId ===
                                    document.id
                                  ? "Reload"
                                  : "Open"}
                            </button>


                            <button
                              onClick={() =>
                                deleteSavedDocument(
                                  document
                                )
                              }

                              disabled={
                                deletingDocumentId !==
                                  null ||
                                loadingDocumentId !==
                                  null
                              }
                            >
                              {deletingDocumentId ===
                              document.id
                                ? "Deleting..."
                                : "Delete"}
                            </button>

                          </div>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {/* ============================================= */}
        {/* UPLOAD NEW LECTURE */}
        {/* ============================================= */}

        <section className="card">

          <h2>
            Upload New Lecture Notes
          </h2>

          <p className="description">
            Upload a DOCX or PDF file to extract lecture
            content and save its anatomy claims for
            factual review.
          </p>


          <input
            type="file"
            accept=".docx,.pdf"
            onChange={
              handleFileChange
            }
          />


          {selectedFile && (

            <div className="file-info">

              <strong>
                Selected:
              </strong>{" "}

              {
                selectedFile.name
              }

            </div>

          )}


          <div className="actions">

            <button
              onClick={
                extractText
              }

              disabled={
                loading ||
                reviewingClaimId !==
                  null
              }
            >
              Extract Document Text
            </button>


            <button
              onClick={
                extractClaimsFromDocument
              }

              disabled={
                loading ||
                reviewingClaimId !==
                  null
              }
            >
              Extract Anatomy Claims
            </button>

          </div>


          {loading && (

            <p className="loading">
              Processing...
            </p>

          )}


          {message && (

            <div className="message">
              {message}
            </div>

          )}

        </section>


        {/* ============================================= */}
        {/* EXTRACTED TEXT */}
        {/* ============================================= */}

        {extractedText && (

          <section className="card">

            <h2>
              Extracted Text
            </h2>

            <textarea
              value={
                extractedText
              }

              readOnly

              rows="15"
            />

          </section>

        )}


        {/* ============================================= */}
        {/* CURRENT LECTURE */}
        {/* ============================================= */}

        {currentDocument && (

          <section className="card">

            <h2>
              Current Lecture
            </h2>

            <p className="description">

              <strong>
                Document ID:
              </strong>{" "}

              {
                currentDocument.id
              }

            </p>

            <p className="description">

              <strong>
                File:
              </strong>{" "}

              {
                currentDocument.filename
              }

            </p>

          </section>

        )}


        {/* ============================================= */}
        {/* AI SUMMARY */}
        {/* ============================================= */}

        {claims.length > 0 && (

          <section className="card">

            <h2>
              AI Review Summary
            </h2>

            <p className="description">
              AI performs an initial factual review and
              retrieves external sources when available.
              These results are suggestions only. The
              instructor remains the final authority.
            </p>


            <div className="review-summary">

              <div className="summary-card">

                <span>
                  Total Claims
                </span>

                <strong>
                  {totalClaims}
                </strong>

              </div>


              <div className="summary-card">

                <span>
                  AI Reviewed
                </span>

                <strong>
                  {aiReviewedCount}
                </strong>

              </div>


              <div className="summary-card">

                <span>
                  Likely Correct
                </span>

                <strong>
                  {likelyCorrectCount}
                </strong>

              </div>


              <div className="summary-card">

                <span>
                  Possible Error
                </span>

                <strong>
                  {possibleErrorCount}
                </strong>

              </div>


              <div className="summary-card">

                <span>
                  Needs Review
                </span>

                <strong>
                  {aiNeedsReviewCount}
                </strong>

              </div>


              <div className="summary-card">

                <span>
                  Not Reviewed
                </span>

                <strong>
                  {notReviewedCount}
                </strong>

              </div>

            </div>


            <p className="description">
              Review claims individually for now.
              Bulk AI review is temporarily disabled
              while the development Gemini API is
              rate-limited.
            </p>

          </section>

        )}


        {/* ============================================= */}
        {/* INSTRUCTOR REVIEW */}
        {/* ============================================= */}

        {claims.length > 0 && (

          <section className="card">

            <h2>
              Instructor Review
            </h2>

            <p className="description">
              Review the AI finding, examine its sources,
              and record the final instructor decision.
            </p>


            <div className="review-summary">

              <div className="summary-card">
                <span>
                  Total
                </span>
                <strong>
                  {totalClaims}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Pending
                </span>
                <strong>
                  {pendingCount}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Accepted
                </span>
                <strong>
                  {acceptedCount}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Rejected
                </span>
                <strong>
                  {rejectedCount}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Edited
                </span>
                <strong>
                  {editedCount}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Needs Review
                </span>
                <strong>
                  {professorNeedsReviewCount}
                </strong>
              </div>

            </div>


            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>

                    <th>
                      DB ID
                    </th>

                    <th>
                      Claim #
                    </th>

                    <th>
                      Page
                    </th>

                    <th>
                      Original Claim
                    </th>

                    <th>
                      AI Review
                    </th>

                    <th>
                      AI Status
                    </th>

                    <th>
                      Reason
                    </th>

                    <th>
                      Suggested Correction
                    </th>

                    <th>
                      Sources
                    </th>

                    <th>
                      Instructor Decision
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {claims.map(
                    (claim) => (

                      <tr
                        key={
                          claim.id
                        }
                      >

                        <td>
                          {claim.id}
                        </td>


                        <td>
                          {
                            claim.claim_number
                          }
                        </td>


                        <td>
                          {
                            claim.page ??
                            "—"
                          }
                        </td>


                        <td className="claim-text">
                          {claim.text}
                        </td>


                        <td>

                          <button
                            className="review-button"

                            onClick={() =>
                              reviewClaimWithAI(
                                claim.id
                              )
                            }

                            disabled={
                              reviewingClaimId !==
                                null ||
                              savingDecisionClaimId !==
                                null
                            }
                          >

                            {reviewingClaimId ===
                            claim.id
                              ? "Reviewing..."
                              : claim.ai_status !==
                                  "not_reviewed"
                                ? "Review Again"
                                : "Review with AI"}

                          </button>

                        </td>


                        <td>

                          <span
                            className={`status-badge ${getAIStatusClass(
                              claim.ai_status
                            )}`}
                          >
                            {
                              formatAIStatus(
                                claim.ai_status
                              )
                            }
                          </span>

                        </td>


                        <td className="reason-text">

                          {
                            claim.reason ||
                            "—"
                          }

                        </td>


                        <td className="correction-text">

                          {
                            claim.suggested_correction ||
                            "—"
                          }


                          {claim.professor_correction && (

                            <div
                              style={{
                                marginTop:
                                  "10px",
                              }}
                            >

                              <strong>
                                Professor version:
                              </strong>

                              <div>
                                {
                                  claim.professor_correction
                                }
                              </div>

                            </div>

                          )}

                        </td>


                        <td>

                          {claim.sources &&
                          claim.sources.length >
                            0 ? (

                            <div>

                              {
                                claim.sources.map(
                                  (
                                    source,
                                    index
                                  ) => (

                                    <div
                                      key={
                                        source.id ||
                                        `${claim.id}-${index}`
                                      }

                                      style={{
                                        marginBottom:
                                          "8px",
                                      }}
                                    >

                                      <a
                                        href={
                                          source.url
                                        }

                                        target="_blank"

                                        rel="noreferrer"
                                      >
                                        {
                                          source.title ||
                                          "View Source"
                                        }
                                      </a>


                                      {source.evidence_text && (

                                        <div
                                          style={{
                                            marginTop:
                                              "4px",
                                          }}
                                        >
                                          {
                                            source.evidence_text
                                          }
                                        </div>

                                      )}

                                    </div>

                                  )
                                )
                              }

                            </div>

                          ) : (
                            "—"
                          )}

                        </td>


                        <td>

                          <div
                            style={{
                              display:
                                "flex",

                              flexDirection:
                                "column",

                              gap:
                                "8px",

                              minWidth:
                                "160px",
                            }}
                          >

                            <strong>
                              {
                                formatDecision(
                                  claim.instructor_decision
                                )
                              }
                            </strong>


                            <button
                              onClick={() =>
                                saveProfessorDecision(
                                  claim.id,
                                  "accepted"
                                )
                              }

                              disabled={
                                savingDecisionClaimId ===
                                  claim.id
                              }
                            >
                              Accept
                            </button>


                            <button
                              onClick={() =>
                                saveProfessorDecision(
                                  claim.id,
                                  "rejected"
                                )
                              }

                              disabled={
                                savingDecisionClaimId ===
                                  claim.id
                              }
                            >
                              Reject
                            </button>


                            <button
                              onClick={() =>
                                startEditingCorrection(
                                  claim
                                )
                              }

                              disabled={
                                savingDecisionClaimId ===
                                  claim.id
                              }
                            >
                              Edit
                            </button>


                            <button
                              onClick={() =>
                                saveProfessorDecision(
                                  claim.id,
                                  "needs_review"
                                )
                              }

                              disabled={
                                savingDecisionClaimId ===
                                  claim.id
                              }
                            >
                              Needs Review
                            </button>


                            {editingClaimId ===
                              claim.id && (

                              <div>

                                <textarea
                                  value={
                                    editCorrectionText
                                  }

                                  onChange={(
                                    event
                                  ) =>
                                    setEditCorrectionText(
                                      event.target.value
                                    )
                                  }

                                  rows="5"

                                  placeholder="Enter the professor-approved correction."
                                />


                                <div
                                  style={{
                                    display:
                                      "flex",

                                    gap:
                                      "6px",

                                    marginTop:
                                      "6px",
                                  }}
                                >

                                  <button
                                    onClick={() =>
                                      saveEditedCorrection(
                                        claim.id
                                      )
                                    }

                                    disabled={
                                      savingDecisionClaimId ===
                                        claim.id
                                    }
                                  >
                                    Save Edit
                                  </button>


                                  <button
                                    onClick={() => {
                                      setEditingClaimId(
                                        null
                                      );

                                      setEditCorrectionText(
                                        ""
                                      );
                                    }}

                                    disabled={
                                      savingDecisionClaimId ===
                                        claim.id
                                    }
                                  >
                                    Cancel
                                  </button>

                                </div>

                              </div>

                            )}


                            {savingDecisionClaimId ===
                              claim.id && (

                              <span>
                                Saving...
                              </span>

                            )}

                          </div>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          </section>

        )}

      </main>

    </div>
  );
}


export default LectureReview;