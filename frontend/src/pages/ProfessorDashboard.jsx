import { useNavigate } from "react-router-dom";


function ProfessorDashboard() {
  const navigate = useNavigate();

  const professorEmail =
    localStorage.getItem(
      "professor_email"
    );


  const handleLogout = () => {
    localStorage.removeItem(
      "professor_token"
    );

    localStorage.removeItem(
      "professor_email"
    );

    navigate(
      "/",
      {
        replace: true,
      }
    );
  };


  const openLectureReview = () => {
    navigate(
      "/professor/review"
    );
  };


  return (
    <div className="professor-page">

      <header className="professor-header">

        <div>
          <h1>
            Professor Dashboard
          </h1>

          <p>
            Human Anatomy
          </p>
        </div>


        <div className="professor-header-actions">

          <span>
            {professorEmail}
          </span>

          <button
            onClick={handleLogout}
          >
            Logout
          </button>

        </div>

      </header>


      <main className="professor-content">

        <section className="dashboard-welcome">

          <p className="dashboard-eyebrow">
            HUMAN ANATOMY
          </p>

          <h2>
            Course Management
          </h2>

          <p>
            Manage lecture materials,
            review AI findings, and
            understand common student
            questions.
          </p>

        </section>


        <section className="dashboard-grid">

          <div className="dashboard-tile">

            <div className="dashboard-tile-top">
              <span className="dashboard-icon">
                PDF
              </span>

              <span className="feature-status">
                Coming next
              </span>
            </div>

            <h3>
              Documents
            </h3>

            <p>
              Upload, replace, and manage
              private course PDFs.
            </p>

          </div>


          <div className="dashboard-tile dashboard-tile-active">

            <div className="dashboard-tile-top">

              <span className="dashboard-icon">
                AI
              </span>

              <span className="feature-status feature-active">
                Available
              </span>

            </div>

            <h3>
              Lecture Review
            </h3>

            <p>
              Extract lecture claims and
              review possible factual issues
              using AI.
            </p>

            <button
              type="button"
              className="dashboard-action-button"
              onClick={openLectureReview}
            >
              Open Lecture Review →
            </button>

          </div>


          <div className="dashboard-tile">

            <div className="dashboard-tile-top">
              <span className="dashboard-icon">
                Q
              </span>

              <span className="feature-status">
                Planned
              </span>
            </div>

            <h3>
              Student Questions
            </h3>

            <p>
              Review frequently asked and
              unanswered anatomy questions.
            </p>

          </div>


          <div className="dashboard-tile">

            <div className="dashboard-tile-top">
              <span className="dashboard-icon">
                %
              </span>

              <span className="feature-status">
                Planned
              </span>
            </div>

            <h3>
              Analytics
            </h3>

            <p>
              Identify repeated topics and
              areas of student confusion.
            </p>

          </div>

        </section>

      </main>

    </div>
  );
}


export default ProfessorDashboard;