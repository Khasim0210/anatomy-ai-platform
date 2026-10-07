import { useState } from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";


const BACKEND_URL =
  "http://127.0.0.1:8000";


function ProfessorLogin() {
  const navigate = useNavigate();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [message, setMessage] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!email.trim() || !password) {
      setMessage(
        "Email and password are required."
      );

      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch(
        `${BACKEND_URL}/professor/login`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        }
      );

      const result =
        await response.json();

      if (!response.ok) {
        throw new Error(
          result.detail ||
            "Login failed."
        );
      }

      localStorage.setItem(
        "professor_token",
        result.access_token
      );

      localStorage.setItem(
        "professor_email",
        result.professor.email
      );

      navigate(
        "/professor",
        {
          replace: true,
        }
      );

    } catch (error) {
      setMessage(
        error.message
      );

    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="login-page">

      <div className="login-card">

        <Link
          to="/"
          className="back-link"
        >
          ← Back to student site
        </Link>

        <h1>
          Professor Login
        </h1>

        <p>
          Sign in to manage course materials
          and review AI findings.
        </p>


        <form onSubmit={handleSubmit}>

          <label htmlFor="professor-email">
            Email
          </label>

          <input
            id="professor-email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
            placeholder="professor@buffalo.edu"
            autoComplete="email"
          />


          <label htmlFor="professor-password">
            Password
          </label>

          <input
            id="professor-password"
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value
              )
            }
            placeholder="Enter password"
            autoComplete="current-password"
          />


          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Sign In"}
          </button>

        </form>


        {message && (
          <div className="login-message">
            {message}
          </div>
        )}

      </div>

    </div>
  );
}


export default ProfessorLogin;