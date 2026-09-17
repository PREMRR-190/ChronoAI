import { useState } from "react";
import "./login.css";

const API_URL = "http://localhost:5000";

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const submitForm = async (e) => {
    e.preventDefault();

    setMessage("");

    if (!username.trim()) {
      setMessage("Please enter your username.");
      return;
    }

    if (!password) {
      setMessage("Please enter your password.");
      return;
    }

    if (mode === "register" && password !== confirmPassword) {
      setMessage("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const endpoint =
        mode === "login"
          ? "/api/login"
          : "/api/register";

      const response = await fetch(
        `${API_URL}${endpoint}`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          credentials: "include",

          body: JSON.stringify({
            username: username.trim(),
            password: password,
          }),
        }
      );

      const data = await response.json();

      console.log("Server response:", data);

      if (!response.ok || !data.success) {
        setMessage(
          data.message ||
            "Invalid username or password."
        );

        return;
      }

      // ==========================================
      // LOGIN SUCCESS
      // ==========================================

      if (mode === "login") {

        console.log(
          "LOGIN SUCCESS:",
          data.user
        );

        if (!data.user) {
          setMessage(
            "Login successful, but user data was not received."
          );

          return;
        }

        // IMPORTANT:
        // Send the logged-in user to App.jsx
        onLogin(data.user);

        return;
      }

      // ==========================================
      // REGISTER SUCCESS
      // ==========================================

      if (mode === "register") {

        setMessage(
          "Account created successfully. Logging in..."
        );

        // Register already creates the session
        // in our Flask backend.

        if (data.user) {

          console.log(
            "REGISTER SUCCESS:",
            data.user
          );

          onLogin(data.user);

          return;
        }

        // Fallback login if user object wasn't returned

        const loginResponse = await fetch(
          `${API_URL}/api/login`,
          {
            method: "POST",

            headers: {
              "Content-Type": "application/json",
            },

            credentials: "include",

            body: JSON.stringify({
              username: username.trim(),
              password: password,
            }),
          }
        );

        const loginData =
          await loginResponse.json();

        console.log(
          "Automatic login response:",
          loginData
        );

        if (
          !loginResponse.ok ||
          !loginData.success
        ) {
          setMessage(
            "Account created. Please login."
          );

          setMode("login");

          setPassword("");
          setConfirmPassword("");

          return;
        }

        onLogin(loginData.user);
      }

    } catch (error) {

      console.error(
        "LOGIN ERROR:",
        error
      );

      setMessage(
        "Cannot connect to server. Make sure Flask backend is running."
      );

    } finally {

      setLoading(false);
    }
  };


  return (
    <div className="login-page">

      <div className="login-card">

        {/* LOGO */}

        <div className="login-logo">
          <span>✦</span> Chrono<span>AI</span>
        </div>


        {/* TITLE */}

        <h1>
          {mode === "login"
            ? "Welcome back"
            : "Create your account"}
        </h1>


        {/* SUBTITLE */}

        <p className="login-subtitle">

          {mode === "login"
            ? "Sign in to continue to your productivity planner."
            : "Create an account to keep your ChronoAI data private."}

        </p>


        {/* FORM */}

        <form onSubmit={submitForm}>

          {/* USERNAME */}

          <label>
            Username
          </label>

          <input
            type="text"
            placeholder="Enter username"
            value={username}
            onChange={(e) =>
              setUsername(e.target.value)
            }
            autoComplete="username"
          />


          {/* PASSWORD */}

          <label>
            Password
          </label>

          <input
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            autoComplete={
              mode === "login"
                ? "current-password"
                : "new-password"
            }
          />


          {/* CONFIRM PASSWORD */}

          {mode === "register" && (
            <>
              <label>
                Confirm Password
              </label>

              <input
                type="password"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) =>
                  setConfirmPassword(
                    e.target.value
                  )
                }
                autoComplete="new-password"
              />
            </>
          )}


          {/* MESSAGE */}

          {message && (
            <div className="login-message">
              {message}
            </div>
          )}


          {/* BUTTON */}

          <button
            className="login-button"
            type="submit"
            disabled={loading}
          >

            {loading
              ? "Please wait..."
              : mode === "login"
              ? "Login"
              : "Create Account"}

          </button>

        </form>


        {/* SWITCH LOGIN / REGISTER */}

        <div className="login-switch">

          {mode === "login" ? (
            <>
              New user?{" "}

              <button
                type="button"
                onClick={() => {
                  setMode("register");
                  setMessage("");
                }}
              >
                Create an account
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}

              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setMessage("");
                }}
              >
                Login
              </button>
            </>
          )}

        </div>

      </div>

    </div>
  );
}

export default Login;