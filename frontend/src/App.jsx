import { useEffect, useState } from "react";
import "./App.css";

const API = "https://chronoai-7.onrender.com";

// =========================================================
// BACKEND REQUEST HELPER
// =========================================================
// This automatically sends the Flask session cookie.

const apiFetch = (url, options = {}) => {
  return window.fetch(url, {
    ...options,
    credentials: "include",
  });
};

function App() {
  // =========================================================
  // LOGIN / AUTHENTICATION
  // =========================================================

  const [user, setUser] = useState(null);
  const [checkingLogin, setCheckingLogin] = useState(true);

  const [authMode, setAuthMode] = useState("login");
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authConfirmPassword, setAuthConfirmPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  // =========================================================
  // TASKS
  // =========================================================

  const [tasks, setTasks] = useState([]);

  const [taskName, setTaskName] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [hours, setHours] = useState("1");

  // =========================================================
  // SCHEDULE
  // =========================================================

  const [schedule, setSchedule] = useState([]);

  const [scheduleTime, setScheduleTime] = useState("");
  const [scheduleActivity, setScheduleActivity] = useState("");

  // =========================================================
  // DAILY HABITS
  // =========================================================

  const [sleepTime, setSleepTime] = useState("");
  const [wakeTime, setWakeTime] = useState("");
  const [screenTime, setScreenTime] = useState("");
  const [studyTime, setStudyTime] = useState("");

  const [habitsSaved, setHabitsSaved] = useState(false);

  // =========================================================
  // CHECK LOGIN SESSION
  // =========================================================

  useEffect(() => {
    checkLogin();
  }, []);

  const checkLogin = async () => {
    try {
      const response = await apiFetch(`${API}/api/me`);
      const data = await response.json();

      if (data.success && data.user) {
        setUser(data.user);
      }
    } catch (error) {
      console.log("Could not check login:", error);
    } finally {
      setCheckingLogin(false);
    }
  };

  // =========================================================
  // LOGIN / REGISTER
  // =========================================================

  const handleAuthSubmit = async (event) => {
    event.preventDefault();

    const username = authUsername.trim();

    if (!username || !authPassword) {
      alert("Please enter username and password.");
      return;
    }

    if (authMode === "register") {
      if (username.length < 3) {
        alert("Username must be at least 3 characters.");
        return;
      }

      if (authPassword.length < 6) {
        alert("Password must be at least 6 characters.");
        return;
      }

      if (authPassword !== authConfirmPassword) {
        alert("Passwords do not match.");
        return;
      }
    }

    setAuthLoading(true);

    try {
      const endpoint =
        authMode === "login"
          ? "/api/login"
          : "/api/register";

      const response = await apiFetch(
        `${API}${endpoint}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            password: authPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        alert(
          data.message ||
            (
              authMode === "login"
                ? "Invalid username or password."
                : "Registration failed."
            )
        );
        return;
      }

      setUser(data.user);

      setAuthUsername("");
      setAuthPassword("");
      setAuthConfirmPassword("");
    } catch (error) {
      console.log("Authentication error:", error);

      alert(
        "Cannot connect to the backend. Please try again."
      );
    } finally {
      setAuthLoading(false);
    }
  };

  // =========================================================
  // LOGOUT
  // =========================================================

  const handleLogout = async () => {
    try {
      await apiFetch(`${API}/api/logout`, {
        method: "POST",
      });
    } catch (error) {
      console.log("Logout error:", error);
    }

    setUser(null);

    setTasks([]);
    setSchedule([]);

    setSleepTime("");
    setWakeTime("");
    setScreenTime("");
    setStudyTime("");

    setHabitsSaved(false);
  };

  // =========================================================
  // LOAD USER DATA AFTER LOGIN
  // =========================================================

  useEffect(() => {
    if (!user) {
      return;
    }

    loadTasks();
    loadSchedule();
    loadHabits();
  }, [user]);

  // =========================================================
  // LOAD TASKS
  // =========================================================

  const loadTasks = async () => {
    try {
      const response = await apiFetch(
        `${API}/api/tasks`
      );

      const data = await response.json();

      if (data.success) {
        setTasks(data.tasks);
      }
    } catch (error) {
      console.log(
        "Could not load tasks:",
        error
      );
    }
  };

  // =========================================================
  // ADD TASK
  // =========================================================

  const addTask = async () => {
    if (!taskName.trim()) {
      alert("Please enter a task");
      return;
    }

    try {
      const response = await apiFetch(
        `${API}/api/tasks`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            title: taskName,
            priority: priority,
            hours: Number(hours),
          }),
        }
      );

      const data = await response.json();

      if (data.success) {
        setTasks((previousTasks) => [
          ...previousTasks,
          data.task,
        ]);

        setTaskName("");
        setPriority("Medium");
        setHours("1");
      } else {
        alert(
          data.message ||
            "Could not add task"
        );
      }
    } catch (error) {
      console.log(error);

      alert(
        "Cannot connect to the backend."
      );
    }
  };

  // =========================================================
  // COMPLETE / UNCOMPLETE TASK
  // =========================================================

  const toggleTask = async (id) => {
    const task = tasks.find(
      (item) => item.id === id
    );

    if (!task) return;

    try {
      const response = await apiFetch(
        `${API}/api/tasks/${id}`,
        {
          method: "PUT",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            completed:
              !task.completed,
          }),
        }
      );

      const data =
        await response.json();

      if (data.success) {
        setTasks((previousTasks) =>
          previousTasks.map(
            (item) =>
              item.id === id
                ? {
                    ...item,
                    completed:
                      !item.completed,
                  }
                : item
          )
        );
      } else {
        alert(
          data.message ||
            "Could not update task"
        );
      }
    } catch (error) {
      console.log(error);
    }
  };

  // =========================================================
  // DELETE TASK
  // =========================================================

  const deleteTask = async (id) => {
    try {
      const response = await apiFetch(
        `${API}/api/tasks/${id}`,
        {
          method: "DELETE",
        }
      );

      const data =
        await response.json();

      if (data.success) {
        setTasks((previousTasks) =>
          previousTasks.filter(
            (task) =>
              task.id !== id
          )
        );
      } else {
        alert(
          data.message ||
            "Could not delete task"
        );
      }
    } catch (error) {
      console.log(error);
    }
  };

  // =========================================================
  // SORT TASKS
  // HIGH → MEDIUM → LOW
  // =========================================================

  const priorityValue = {
    High: 1,
    Medium: 2,
    Low: 3,
  };

  const sortedTasks = [...tasks].sort(
    (a, b) =>
      (priorityValue[a.priority] || 2) -
      (priorityValue[b.priority] || 2)
  );

  const activeTasks = sortedTasks.filter(
    (task) => !task.completed
  );

  const completedTasks =
    sortedTasks.filter(
      (task) => task.completed
    );

  // =========================================================
  // TASK COMPLETION
  // =========================================================

  const taskCompletion =
    tasks.length === 0
      ? 0
      : Math.round(
          (completedTasks.length /
            tasks.length) *
            100
        );

  // =========================================================
  // PLANNED HOURS
  // =========================================================

  const plannedHours =
    tasks.reduce(
      (sum, task) =>
        sum +
        Number(task.hours || 0),
      0
    );

  // =========================================================
  // SLEEP DURATION
  // =========================================================

  const calculateSleepHours = () => {
    if (!sleepTime || !wakeTime) {
      return 0;
    }

    const [
      sleepHour,
      sleepMinute,
    ] =
      sleepTime
        .split(":")
        .map(Number);

    const [
      wakeHour,
      wakeMinute,
    ] =
      wakeTime
        .split(":")
        .map(Number);

    let sleepMinutes =
      sleepHour * 60 +
      sleepMinute;

    let wakeMinutes =
      wakeHour * 60 +
      wakeMinute;

    if (wakeMinutes <= sleepMinutes) {
      wakeMinutes +=
        24 * 60;
    }

    const duration =
      (wakeMinutes -
        sleepMinutes) /
      60;

    return Number(
      duration.toFixed(1)
    );
  };

  const sleepHours =
    calculateSleepHours();

  // =========================================================
  // SLEEP SCORE
  // =========================================================

  const calculateSleepScore = () => {
    if (!sleepTime || !wakeTime) {
      return 0;
    }

    if (
      sleepHours >= 7 &&
      sleepHours <= 9
    ) {
      return 100;
    }

    if (
      sleepHours >= 6 &&
      sleepHours < 7
    ) {
      return 80;
    }

    if (
      sleepHours > 9 &&
      sleepHours <= 10
    ) {
      return 85;
    }

    if (sleepHours >= 5) {
      return 60;
    }

    return 40;
  };

  const sleepScore =
    calculateSleepScore();

  // =========================================================
  // SCREEN SCORE
  // =========================================================

  const calculateScreenScore = () => {
    const screen =
      Number(screenTime);

    if (
      screenTime === "" ||
      isNaN(screen)
    ) {
      return 0;
    }

    if (screen <= 2) {
      return 100;
    }

    if (screen <= 4) {
      return 90;
    }

    if (screen <= 6) {
      return 75;
    }

    if (screen <= 8) {
      return 55;
    }

    return 35;
  };

  const screenScore =
    calculateScreenScore();

  // =========================================================
  // STUDY / WORK SCORE
  // =========================================================

  const calculateStudyScore = () => {
    const study =
      Number(studyTime);

    if (
      studyTime === "" ||
      isNaN(study)
    ) {
      return 0;
    }

    if (study >= 5) {
      return 100;
    }

    if (study >= 4) {
      return 90;
    }

    if (study >= 3) {
      return 80;
    }

    if (study >= 2) {
      return 65;
    }

    if (study >= 1) {
      return 50;
    }

    return 30;
  };

  const studyScore =
    calculateStudyScore();

  // =========================================================
  // PRODUCTIVITY SCORE
  // =========================================================

  let productivity = 0;

  if (habitsSaved) {
    productivity = Math.round(
      taskCompletion * 0.40 +
        sleepScore * 0.20 +
        screenScore * 0.20 +
        studyScore * 0.20
    );
  }

  // =========================================================
  // PRODUCTIVITY MESSAGE
  // =========================================================

  const getProductivityMessage = () => {
    if (!habitsSaved) {
      return "Enter your daily habits to calculate your ChronoAI score.";
    }

    if (productivity >= 85) {
      return "Excellent! Your daily routine is highly productive.";
    }

    if (productivity >= 70) {
      return "Good productivity. A few improvements can make your day better.";
    }

    if (productivity >= 50) {
      return "Your productivity can improve. Check your screen time and study time.";
    }

    return "Your productivity is low today. ChronoAI recommends improving your daily routine.";
  };

  // =========================================================
  // RECOMMENDATION
  // =========================================================

  const getRecommendation = () => {
    if (!habitsSaved) {
      return "Add your sleep, screen time and study/work data.";
    }

    if (screenScore < 60) {
      return "Try reducing screen time by 30 minutes tomorrow.";
    }

    if (sleepScore < 70) {
      return "Try maintaining 7–9 hours of sleep.";
    }

    if (studyScore < 60) {
      return "Try increasing focused study/work time.";
    }

    if (taskCompletion < 60) {
      return "Focus on your highest-priority tasks first.";
    }

    return "Your routine looks balanced. Keep maintaining your consistency.";
  };

  // =========================================================
  // LOAD SCHEDULE
  // =========================================================

  const loadSchedule = async () => {
    try {
      const response = await apiFetch(
        `${API}/api/schedule`
      );

      const data =
        await response.json();

      if (data.success) {
        setSchedule(
          data.schedule
        );
      }
    } catch (error) {
      console.log(
        "Could not load schedule:",
        error
      );
    }
  };

  // =========================================================
  // ADD SCHEDULE
  // =========================================================

  const addSchedule = async () => {
    if (
      !scheduleTime ||
      !scheduleActivity.trim()
    ) {
      alert(
        "Enter both time and activity"
      );
      return;
    }

    try {
      const response = await apiFetch(
        `${API}/api/schedule`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            time: scheduleTime,
            activity:
              scheduleActivity,
          }),
        }
      );

      const data =
        await response.json();

      if (data.success) {
        setSchedule(
          (previous) => [
            ...previous,
            data.schedule,
          ]
        );

        setScheduleTime("");
        setScheduleActivity("");
      } else {
        alert(
          data.message ||
            "Could not add schedule"
        );
      }
    } catch (error) {
      console.log(error);

      alert(
        "Cannot connect to the backend."
      );
    }
  };

  // =========================================================
  // DELETE SCHEDULE
  // =========================================================

  const deleteSchedule = async (id) => {
    try {
      const response = await apiFetch(
        `${API}/api/schedule/${id}`,
        {
          method: "DELETE",
        }
      );

      const data =
        await response.json();

      if (data.success) {
        setSchedule(
          (previous) =>
            previous.filter(
              (item) =>
                item.id !== id
            )
        );
      } else {
        alert(
          data.message ||
            "Could not delete schedule"
        );
      }
    } catch (error) {
      console.log(error);
    }
  };

  // =========================================================
  // LOAD HABITS
  // =========================================================

  const loadHabits = async () => {
    try {
      const response = await apiFetch(
        `${API}/api/habits`
      );

      const data =
        await response.json();

      if (
        data.success &&
        data.habit
      ) {
        setSleepTime(
          data.habit.sleep_time ||
            ""
        );

        setWakeTime(
          data.habit.wake_time ||
            ""
        );

        setScreenTime(
          data.habit.screen_time ??
            ""
        );

        setStudyTime(
          data.habit.study_time ??
            ""
        );

        setHabitsSaved(true);
      }
    } catch (error) {
      console.log(
        "Could not load habits:",
        error
      );
    }
  };

  // =========================================================
  // SAVE HABITS
  // =========================================================

  const saveHabits = async () => {
    if (!sleepTime || !wakeTime) {
      alert(
        "Please enter sleep time and wake-up time"
      );
      return;
    }

    if (
      screenTime === "" ||
      studyTime === ""
    ) {
      alert(
        "Please enter screen time and study/work time"
      );
      return;
    }

    try {
      const response = await apiFetch(
        `${API}/api/habits`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            sleep_time:
              sleepTime,

            wake_time:
              wakeTime,

            screen_time:
              Number(screenTime),

            study_time:
              Number(studyTime),
          }),
        }
      );

      const data =
        await response.json();

      if (data.success) {
        setHabitsSaved(true);

        alert(
          "Daily habits saved successfully!"
        );
      } else {
        alert(
          data.message ||
            "Could not save habits"
        );
      }
    } catch (error) {
      console.log(error);

      alert(
        "Cannot connect to the backend."
      );
    }
  };

  // =========================================================
  // TIME FORMAT
  // =========================================================

  const formatTime = (time) => {
    if (!time) {
      return "";
    }

    const [hour, minute] =
      time.split(":");

    let h = Number(hour);

    const suffix =
      h >= 12 ? "PM" : "AM";

    h = h % 12;

    if (h === 0) {
      h = 12;
    }

    return `${String(h).padStart(
      2,
      "0"
    )}:${minute} ${suffix}`;
  };

  // =========================================================
  // LOADING SCREEN
  // =========================================================

  if (checkingLogin) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f7f4ff",
          fontSize: "20px",
          fontWeight: "700",
          color: "#4f3c8d",
        }}
      >
        Loading ChronoAI...
      </div>
    );
  }

  // =========================================================
  // LOGIN / REGISTER SCREEN
  // =========================================================

  if (!user) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "30px",
          boxSizing: "border-box",
          background:
            "linear-gradient(135deg, #f7f4ff 0%, #f9fbff 100%)",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: "430px",
            background: "#ffffff",
            borderRadius: "24px",
            padding: "38px",
            boxSizing: "border-box",
            boxShadow:
              "0 20px 60px rgba(30, 20, 70, 0.12)",
          }}
        >
          <div
            style={{
              textAlign: "center",
              fontSize: "31px",
              fontWeight: "800",
              marginBottom: "24px",
            }}
          >
            <span
              style={{
                color: "#6d3df5",
              }}
            >
              ✦
            </span>{" "}
            Chrono
            <span
              style={{
                color: "#6d3df5",
              }}
            >
              AI
            </span>
          </div>

          <h1
            style={{
              textAlign: "center",
              margin: "0",
              fontSize: "30px",
            }}
          >
            {authMode === "login"
              ? "Welcome back"
              : "Create your account"}
          </h1>

          <p
            style={{
              textAlign: "center",
              color: "#777",
              lineHeight: "1.5",
              margin:
                "10px 0 28px",
            }}
          >
            {authMode === "login"
              ? "Sign in to continue to your productivity planner."
              : "Create an account to keep your ChronoAI data private."}
          </p>

          <form
            onSubmit={
              handleAuthSubmit
            }
          >
            <label
              style={{
                display: "block",
                fontWeight: "600",
                marginBottom: "8px",
              }}
            >
              Username
            </label>

            <input
              type="text"
              placeholder="Enter username"
              value={authUsername}
              onChange={(e) =>
                setAuthUsername(
                  e.target.value
                )
              }
              autoComplete="username"
              style={{
                width: "100%",
                boxSizing:
                  "border-box",
                padding:
                  "14px 15px",
                marginBottom:
                  "18px",
                border:
                  "1px solid #ddd",
                borderRadius:
                  "12px",
                outline: "none",
                fontSize: "15px",
              }}
            />

            <label
              style={{
                display: "block",
                fontWeight: "600",
                marginBottom: "8px",
              }}
            >
              Password
            </label>

            <input
              type="password"
              placeholder="Enter password"
              value={authPassword}
              onChange={(e) =>
                setAuthPassword(
                  e.target.value
                )
              }
              autoComplete={
                authMode === "login"
                  ? "current-password"
                  : "new-password"
              }
              style={{
                width: "100%",
                boxSizing:
                  "border-box",
                padding:
                  "14px 15px",
                marginBottom:
                  authMode === "register"
                    ? "18px"
                    : "22px",
                border:
                  "1px solid #ddd",
                borderRadius:
                  "12px",
                outline: "none",
                fontSize: "15px",
              }}
            />

            {authMode ===
              "register" && (
              <>
                <label
                  style={{
                    display: "block",
                    fontWeight: "600",
                    marginBottom:
                      "8px",
                  }}
                >
                  Confirm Password
                </label>

                <input
                  type="password"
                  placeholder="Re-enter password"
                  value={
                    authConfirmPassword
                  }
                  onChange={(e) =>
                    setAuthConfirmPassword(
                      e.target.value
                    )
                  }
                  autoComplete="new-password"
                  style={{
                    width: "100%",
                    boxSizing:
                      "border-box",
                    padding:
                      "14px 15px",
                    marginBottom:
                      "22px",
                    border:
                      "1px solid #ddd",
                    borderRadius:
                      "12px",
                    outline: "none",
                    fontSize: "15px",
                  }}
                />
              </>
            )}

            <button
              type="submit"
              disabled={authLoading}
              style={{
                width: "100%",
                border: "none",
                borderRadius: "13px",
                padding: "14px",
                background:
                  "linear-gradient(135deg, #6d3df5, #8b5cf6)",
                color: "#fff",
                fontSize: "16px",
                fontWeight: "700",
                cursor: authLoading
                  ? "not-allowed"
                  : "pointer",
                opacity: authLoading
                  ? 0.65
                  : 1,
              }}
            >
              {authLoading
                ? "Please wait..."
                : authMode === "login"
                  ? "Login"
                  : "Create Account"}
            </button>
          </form>

          <div
            style={{
              textAlign: "center",
              marginTop: "22px",
              color: "#777",
              fontSize: "14px",
            }}
          >
            {authMode === "login"
              ? "New user? "
              : "Already have an account? "}

            <button
              type="button"
              onClick={() => {
                setAuthMode(
                  authMode === "login"
                    ? "register"
                    : "login"
                );

                setAuthPassword("");

                setAuthConfirmPassword("");
              }}
              style={{
                border: "none",
                background: "none",
                color: "#6d3df5",
                fontWeight: "700",
                cursor: "pointer",
                padding: "0",
              }}
            >
              {authMode === "login"
                ? "Create an account"
                : "Login"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // =========================================================
  // MAIN DASHBOARD
  // =========================================================

  return (
    <div className="app">

      {/* ================================================= */}
      {/* NAVBAR */}
      {/* ================================================= */}

      <header className="navbar">

        <div className="logo">
          <span>✦</span> Chrono
          <span>AI</span>
        </div>

        <nav>

          <a
            className="nav-active"
            href="#dashboard"
          >
            ⌂ Dashboard
          </a>

          <a href="#tasks">
            ☑ Tasks
          </a>

          <a href="#schedule">
            ▣ Schedule
          </a>

          <a href="#habits">
            ◷ Habits
          </a>

          <a href="#analytics">
            ▥ Analytics
          </a>

        </nav>

        <div
          className="nav-profile"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >

          <div className="bell">
            ♧
          </div>

          <div
            className="profile"
            title={
              user?.username ||
              "User"
            }
          >
            {(user?.username ||
              "U")
              .charAt(0)
              .toUpperCase()}
          </div>

          <span
            style={{
              fontWeight: "600",
              fontSize: "14px",
              color: "#333",
            }}
          >
            {user?.username}
          </span>

          <button
            onClick={
              handleLogout
            }
            style={{
              border: "none",
              borderRadius: "9px",
              padding:
                "8px 12px",
              background:
                "#f1eff8",
              cursor:
                "pointer",
              fontWeight: "600",
              color: "#333",
            }}
          >
            Logout
          </button>

        </div>

      </header>

      {/* ================================================= */}
      {/* MAIN */}
      {/* ================================================= */}

      <main
        className="main-container"
        id="dashboard"
      >

        {/* ================================================= */}
        {/* HERO */}
        {/* ================================================= */}

        <section className="hero">

          <div className="hero-left">

            <div className="ai-label">
              ✦ AI POWERED PRODUCTIVITY
            </div>

            <h1>
              Your time.
              <br />
              <span>
                Optimized by AI.
              </span>
            </h1>

            <p>
              ChronoAI intelligently
              organizes your tasks,
              schedule and habits to
              help you focus on what
              matters most.
            </p>

            <button
              className="plan-btn"
              onClick={() =>
                document
                  .getElementById(
                    "task-input"
                  )
                  ?.focus()
              }
            >
              Plan My Day <b>→</b>
            </button>

          </div>

          <div className="hero-art">

            <div className="art-glow"></div>

            <div className="ai-box">

              <div className="ai-symbol">
                AI
              </div>

              <div className="mini-line">
                <span>✓</span>
                <i></i>
              </div>

              <div className="mini-line">
                <span>✓</span>
                <i></i>
              </div>

              <div className="mini-line">
                <span>✓</span>
                <i></i>
              </div>

              <div className="mini-line">
                <span>✓</span>
                <i></i>
              </div>

            </div>

            <div className="big-star">
              ✦
            </div>

          </div>

        </section>

        {/* ================================================= */}
        {/* OVERVIEW */}
        {/* ================================================= */}

        <section className="overview">

          <div className="overview-title">

            <h4>
              OVERVIEW
            </h4>

            <p>
              Your productivity at a glance.
            </p>

          </div>

          <div className="stats">

            {/* PRODUCTIVITY */}

            <div className="stat-card">

              <div className="stat-icon purple-icon">
                ✦
              </div>

              <small>
                CHRONOAI PRODUCTIVITY
              </small>

              <h2>
                {habitsSaved
                  ? `${productivity}%`
                  : "--"}
              </h2>

              <p>
                AI productivity score
              </p>

              <strong>
                {habitsSaved
                  ? productivity >=
                    70
                    ? "↑ Good"
                    : "↓ Needs improvement"
                  : "Enter habits"}
              </strong>

            </div>

            {/* PLANNED TIME */}

            <div className="stat-card">

              <div className="stat-icon blue-icon">
                ◷
              </div>

              <small>
                PLANNED TIME
              </small>

              <h2>
                {plannedHours}h
              </h2>

              <p>
                Today's workload
              </p>

              <strong>
                ↑ Planned
              </strong>

            </div>

            {/* COMPLETED */}

            <div className="stat-card">

              <div className="stat-icon green-icon">
                ✓
              </div>

              <small>
                COMPLETED
              </small>

              <h2>
                {completedTasks.length}
              </h2>

              <p>
                Tasks finished
              </p>

              <strong>
                {taskCompletion}%
              </strong>

            </div>

          </div>

        </section>

        {/* ================================================= */}
        {/* MAIN GRID */}
        {/* ================================================= */}

        <div className="dashboard-grid">

          {/* ================================================= */}
          {/* TASKS */}
          {/* ================================================= */}

          <section
            className="tasks-card"
            id="tasks"
          >

            <div className="tasks-heading">

              <div>

                <small>
                  ✦ PRODUCTIVITY PLANNER
                </small>

                <h2>
                  Today's Tasks
                </h2>

                <p>
                  Organize your priorities
                  and accomplish more.
                </p>

              </div>

              <div className="active-pill">
                <span></span>
                {activeTasks.length}
                {" "}
                Active
              </div>

            </div>

            {/* ADD TASK */}

            <div className="task-input">

              <div className="input-star">
                ✦
              </div>

              <input
                id="task-input"
                type="text"
                placeholder="What needs to be done?"
                value={taskName}
                onChange={(e) =>
                  setTaskName(
                    e.target.value
                  )
                }
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter"
                  ) {
                    addTask();
                  }
                }}
              />

              <select
                value={priority}
                onChange={(e) =>
                  setPriority(
                    e.target.value
                  )
                }
              >
                <option value="High">
                  High
                </option>

                <option value="Medium">
                  Medium
                </option>

                <option value="Low">
                  Low
                </option>
              </select>

              <select
                value={hours}
                onChange={(e) =>
                  setHours(
                    e.target.value
                  )
                }
              >
                <option value="0.5">
                  0.5 hrs
                </option>

                <option value="1">
                  1 hr
                </option>

                <option value="1.5">
                  1.5 hrs
                </option>

                <option value="2">
                  2 hrs
                </option>

                <option value="3">
                  3 hrs
                </option>
              </select>

              <button
                onClick={addTask}
              >
                Add Task <b>＋</b>
              </button>

            </div>

            {/* ACTIVE TASKS */}

            <div className="task-label">
              ACTIVE TASKS
            </div>

            <div className="task-list">

              {activeTasks.length ===
                0 && (
                <div className="empty">
                  🎉 All tasks completed!
                </div>
              )}

              {activeTasks.map(
                (task) => (
                  <div
                    className="task-row"
                    key={task.id}
                  >

                    <button
                      className="check-button"
                      onClick={() =>
                        toggleTask(
                          task.id
                        )
                      }
                    >
                      <span></span>
                    </button>

                    <div className="task-name">
                      {task.title}
                    </div>

                    <div
                      className={`priority ${String(
                        task.priority
                      ).toLowerCase()}`}
                    >
                      {task.priority}
                    </div>

                    <div className="task-hours">
                      ◷ {task.hours}{" "}
                      {Number(
                        task.hours
                      ) === 1
                        ? "hour"
                        : "hours"}
                    </div>

                    <button
                      className="delete"
                      onClick={() =>
                        deleteTask(
                          task.id
                        )
                      }
                    >
                      🗑
                    </button>

                  </div>
                )
              )}

            </div>

            {/* COMPLETED */}

            <div className="completed-heading">

              <span>
                COMPLETED TASKS
              </span>

              <b>
                {completedTasks.length}
              </b>

              {completedTasks.length >
                0 && (
                <button
                  onClick={() =>
                    completedTasks.forEach(
                      (task) =>
                        deleteTask(
                          task.id
                        )
                    )
                  }
                >
                  Clear All
                </button>
              )}

            </div>

            <div className="completed-list">

              {completedTasks.map(
                (task) => (
                  <div
                    className="task-row completed-row"
                    key={task.id}
                  >

                    <button
                      className="check-button checked"
                      onClick={() =>
                        toggleTask(
                          task.id
                        )
                      }
                    >
                      ✓
                    </button>

                    <div className="task-name">
                      {task.title}
                    </div>

                    <div
                      className={`priority ${String(
                        task.priority
                      ).toLowerCase()}`}
                    >
                      {task.priority}
                    </div>

                    <div className="task-hours">
                      ◷ {task.hours}{" "}
                      {Number(
                        task.hours
                      ) === 1
                        ? "hour"
                        : "hours"}
                    </div>

                    <button
                      className="delete"
                      onClick={() =>
                        deleteTask(
                          task.id
                        )
                      }
                    >
                      🗑
                    </button>

                  </div>
                )
              )}

            </div>

          </section>

          {/* ================================================= */}
          {/* RIGHT COLUMN */}
          {/* ================================================= */}

          <div className="right-column">

            {/* ================================================= */}
            {/* SCHEDULE */}
            {/* ================================================= */}

            <section
              className="side-card"
              id="schedule"
            >

              <div className="side-title">

                <small>
                  ▣ YOUR DAY
                </small>

                <h2>
                  Today's Schedule
                </h2>

              </div>

              {/* SCHEDULE INPUT */}

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  marginBottom:
                    "18px",
                }}
              >

                <input
                  type="time"
                  value={scheduleTime}
                  onChange={(e) =>
                    setScheduleTime(
                      e.target.value
                    )
                  }
                  style={{
                    width: "120px",
                    padding: "14px",
                    borderRadius:
                      "14px",
                    border:
                      "1px solid #ddd",
                    fontSize: "16px",
                  }}
                />

                <input
                  type="text"
                  placeholder="Activity"
                  value={
                    scheduleActivity
                  }
                  onChange={(e) =>
                    setScheduleActivity(
                      e.target.value
                    )
                  }
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter"
                    ) {
                      addSchedule();
                    }
                  }}
                  style={{
                    flex: 1,
                    padding: "14px",
                    borderRadius:
                      "14px",
                    border:
                      "1px solid #ddd",
                    fontSize: "16px",
                  }}
                />

                <button
                  onClick={
                    addSchedule
                  }
                  style={{
                    width: "55px",
                    border: "none",
                    borderRadius:
                      "14px",
                    background:
                      "#f0f0f5",
                    fontSize: "22px",
                    cursor:
                      "pointer",
                  }}
                >
                  +
                </button>

              </div>

              <div className="schedule-list">

                {[...schedule]
                  .sort(
                    (a, b) =>
                      a.time.localeCompare(
                        b.time
                      )
                  )
                  .map(
                    (item, index) => (
                      <div
                        className="schedule-item"
                        key={item.id}
                      >

                        <time>
                          {formatTime(
                            item.time
                          )}
                        </time>

                        <span
                          className={`dot ${
                            index % 3 ===
                            0
                              ? "purple-dot"
                              : index % 3 ===
                                  1
                                ? "blue-dot"
                                : "green-dot"
                          }`}
                        ></span>

                        <b>
                          {item.activity}
                        </b>

                        <button
                          onClick={() =>
                            deleteSchedule(
                              item.id
                            )
                          }
                          style={{
                            border: "none",
                            background:
                              "transparent",
                            cursor:
                              "pointer",
                            fontSize:
                              "15px",
                          }}
                        >
                          🗑
                        </button>

                      </div>
                    )
                  )}

                {schedule.length ===
                  0 && (
                  <div className="empty">
                    Add today's schedule.
                  </div>
                )}

              </div>

            </section>

            {/* ================================================= */}
            {/* DAILY HABITS */}
            {/* ================================================= */}

            <section
              className="side-card"
              id="habits"
              style={{
                marginTop: "24px",
              }}
            >

              <div className="side-title">

                <small>
                  ✦ DAILY HABITS
                </small>

                <h2>
                  Track Your Day
                </h2>

              </div>

              <p
                style={{
                  color: "#777",
                  marginBottom:
                    "20px",
                  lineHeight: "1.5",
                }}
              >
                Enter your daily routine.
                ChronoAI uses this data
                to calculate your
                productivity score.
              </p>

              {/* SLEEP / WAKE */}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "1fr 1fr",
                  gap: "14px",
                }}
              >

                <div>

                  <label
                    style={{
                      display:
                        "block",
                      fontWeight:
                        "600",
                      marginBottom:
                        "8px",
                    }}
                  >
                    😴 Sleep Time
                  </label>

                  <input
                    type="time"
                    value={sleepTime}
                    onChange={(e) =>
                      setSleepTime(
                        e.target.value
                      )
                    }
                    style={{
                      width: "100%",
                      boxSizing:
                        "border-box",
                      padding:
                        "13px",
                      borderRadius:
                        "12px",
                      border:
                        "1px solid #ddd",
                      fontSize:
                        "15px",
                    }}
                  />

                </div>

                <div>

                  <label
                    style={{
                      display:
                        "block",
                      fontWeight:
                        "600",
                      marginBottom:
                        "8px",
                    }}
                  >
                    🌅 Wake-up Time
                  </label>

                  <input
                    type="time"
                    value={wakeTime}
                    onChange={(e) =>
                      setWakeTime(
                        e.target.value
                      )
                    }
                    style={{
                      width: "100%",
                      boxSizing:
                        "border-box",
                      padding:
                        "13px",
                      borderRadius:
                        "12px",
                      border:
                        "1px solid #ddd",
                      fontSize:
                        "15px",
                    }}
                  />

                </div>

              </div>

              {/* SCREEN / STUDY */}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "1fr 1fr",
                  gap: "14px",
                  marginTop:
                    "16px",
                }}
              >

                <div>

                  <label
                    style={{
                      display:
                        "block",
                      fontWeight:
                        "600",
                      marginBottom:
                        "8px",
                    }}
                  >
                    📱 Screen Time
                  </label>

                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    placeholder="e.g. 5.5"
                    value={screenTime}
                    onChange={(e) =>
                      setScreenTime(
                        e.target.value
                      )
                    }
                    style={{
                      width: "100%",
                      boxSizing:
                        "border-box",
                      padding:
                        "13px",
                      borderRadius:
                        "12px",
                      border:
                        "1px solid #ddd",
                      fontSize:
                        "15px",
                    }}
                  />

                  <small>
                    hours
                  </small>

                </div>

                <div>

                  <label
                    style={{
                      display:
                        "block",
                      fontWeight:
                        "600",
                      marginBottom:
                        "8px",
                    }}
                  >
                    📚 Study / Work
                  </label>

                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    placeholder="e.g. 3"
                    value={studyTime}
                    onChange={(e) =>
                      setStudyTime(
                        e.target.value
                      )
                    }
                    style={{
                      width: "100%",
                      boxSizing:
                        "border-box",
                      padding:
                        "13px",
                      borderRadius:
                        "12px",
                      border:
                        "1px solid #ddd",
                      fontSize:
                        "15px",
                    }}
                  />

                  <small>
                    hours
                  </small>

                </div>

              </div>

              {/* SLEEP DURATION */}

              {sleepTime &&
                wakeTime && (
                  <div
                    style={{
                      marginTop:
                        "18px",
                      padding:
                        "14px",
                      borderRadius:
                        "14px",
                      background:
                        "#f6f3ff",
                      textAlign:
                        "center",
                    }}
                  >
                    😴 Sleep Duration:{" "}
                    <strong>
                      {sleepHours} hours
                    </strong>
                  </div>
                )}

              {/* SAVE */}

              <button
                onClick={
                  saveHabits
                }
                style={{
                  width: "100%",
                  marginTop:
                    "20px",
                  padding:
                    "14px",
                  border: "none",
                  borderRadius:
                    "14px",
                  background:
                    "linear-gradient(135deg, #6d3df5, #8b5cf6)",
                  color: "white",
                  fontSize:
                    "16px",
                  fontWeight:
                    "700",
                  cursor:
                    "pointer",
                  boxShadow:
                    "0 8px 20px rgba(109,61,245,0.2)",
                }}
              >
                💾 Save Today's Data
              </button>

              {/* HABIT SCORES */}

              {habitsSaved && (
                <div
                  style={{
                    marginTop:
                      "20px",
                    display: "grid",
                    gap: "8px",
                  }}
                >

                  <div>
                    Task Completion:{" "}
                    <strong>
                      {taskCompletion}%
                    </strong>
                  </div>

                  <div>
                    Sleep Score:{" "}
                    <strong>
                      {sleepScore}%
                    </strong>
                  </div>

                  <div>
                    Screen Efficiency:{" "}
                    <strong>
                      {screenScore}%
                    </strong>
                  </div>

                  <div>
                    Study / Work:{" "}
                    <strong>
                      {studyScore}%
                    </strong>
                  </div>

                </div>
              )}

            </section>

            {/* ================================================= */}
            {/* ANALYTICS */}
            {/* ================================================= */}

            <section
              className="side-card analytics"
              id="analytics"
              style={{
                marginTop: "24px",
              }}
            >

              <div className="side-title">

                <small>
                  ▣ INSIGHTS
                </small>

                <h2>
                  Productivity Analytics
                </h2>

              </div>

              {/* CHRONOAI SCORE */}

              <div
                style={{
                  textAlign:
                    "center",
                  margin:
                    "20px 0",
                }}
              >

                <small>
                  CHRONOAI PRODUCTIVITY SCORE
                </small>

                <div
                  style={{
                    fontSize:
                      "52px",
                    fontWeight:
                      "800",
                    marginTop:
                      "8px",
                  }}
                >
                  {habitsSaved
                    ? `${productivity}%`
                    : "--"}
                </div>

              </div>

              {/* PROGRESS */}

              <div className="progress-title">

                <span>
                  Task completion
                </span>

                <strong>
                  {taskCompletion}%
                </strong>

              </div>

              <div className="progress">

                <div
                  style={{
                    width: `${taskCompletion}%`,
                  }}
                ></div>

              </div>

              {/* BOXES */}

              <div className="analytics-boxes">

                <div>

                  <b>
                    {completedTasks.length}/
                    {tasks.length}
                  </b>

                  <span>
                    Completed tasks
                  </span>

                </div>

                <div>

                  <b>
                    {plannedHours}h
                  </b>

                  <span>
                    Planned time
                  </span>

                </div>

              </div>

              {/* AI INSIGHT */}

              <div
                style={{
                  marginTop:
                    "20px",
                  padding:
                    "18px",
                  borderRadius:
                    "16px",
                  background:
                    "#f7f4ff",
                }}
              >

                <strong>
                  ✦ ChronoAI Insight
                </strong>

                <p
                  style={{
                    lineHeight:
                      "1.5",
                    marginBottom:
                      "8px",
                  }}
                >
                  {getProductivityMessage()}
                </p>

                <p
                  style={{
                    margin:
                      "0",
                    fontWeight:
                      "600",
                  }}
                >
                  💡{" "}
                  {getRecommendation()}
                </p>

              </div>

            </section>

            {/* ================================================= */}
            {/* AI CARD */}
            {/* ================================================= */}

            <section className="ai-card">

              <small>
                ✦ CHRONOAI INTELLIGENCE
              </small>

              <h2>
                Your productivity,
                <br />
                intelligently planned.
              </h2>

              <p>
                ChronoAI analyzes your
                tasks, schedule, sleep,
                screen time and study/work
                patterns to understand your
                productivity.
              </p>

              <div className="ai-decoration">
                ∿
              </div>

            </section>

          </div>

        </div>

      </main>

      {/* ================================================= */}
      {/* FLOATING BUTTON */}
      {/* ================================================= */}

      <button
        className="floating-button"
        onClick={() =>
          document
            .getElementById(
              "task-input"
            )
            ?.focus()
        }
      >
        +
      </button>

      {/* ================================================= */}
      {/* FOOTER */}
      {/* ================================================= */}

      <footer>

        <div>

          <b>
            ChronoAI
          </b>

          <span>
            Adaptive Productivity Planner
          </span>

        </div>

        <div className="footer-links">

          <span>
            About
          </span>

          <span>
            Privacy
          </span>

          <span>
            Terms
          </span>

        </div>

      </footer>

    </div>
  );
}

export default App;