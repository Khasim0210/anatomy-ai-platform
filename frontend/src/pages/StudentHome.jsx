import { Link } from "react-router-dom";

function StudentHome() {
  return (
    <div className="public-page">
      <header className="public-header">
        <div>
          <h1>Anatomy AI</h1>
          <p>Course-based anatomy learning assistant</p>
        </div>

        <Link
          to="/professor/login"
          className="professor-login-link"
        >
          Professor Login
        </Link>
      </header>

      <main className="student-main">
        <section className="student-hero">
          <p className="eyebrow">Human Anatomy</p>

          <h2>Ask questions about your course</h2>

          <p className="student-intro">
            Ask an anatomy question and receive a concise answer
            based primarily on professor-provided course material.
          </p>

          <div className="student-chat-card">
            <label htmlFor="student-question">
              Your question
            </label>

            <textarea
              id="student-question"
              rows="5"
              placeholder="Example: What is the function of the atlas vertebra?"
              disabled
            />

            <button disabled>
              Ask Question
            </button>

            <p className="coming-soon">
              Student Q&A will be connected after the professor
              document system is complete.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default StudentHome;