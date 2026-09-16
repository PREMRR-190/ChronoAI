import { useState } from "react";

function Tasks() {
  const [tasks, setTasks] = useState([]);

  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("Medium");
  const [time, setTime] = useState("1");

  const addTask = () => {
    if (title.trim() === "") {
      alert("Please enter a task");
      return;
    }

    const newTask = {
      id: Date.now(),
      title: title,
      priority: priority,
      time: time,
      completed: false,
    };

    setTasks([...tasks, newTask]);

    // Clear form after adding
    setTitle("");
    setPriority("Medium");
    setTime("1");
  };

  const completeTask = (id) => {
    setTasks(
      tasks.map((task) =>
        task.id === id
          ? { ...task, completed: !task.completed }
          : task
      )
    );
  };

  const deleteTask = (id) => {
    setTasks(
      tasks.filter((task) => task.id !== id)
    );
  };

  return (
    <div className="tasks-page">

      <h1>My Tasks</h1>

      <p className="task-subtitle">
        Add and manage your daily tasks.
      </p>

      {/* ADD TASK FORM */}
      <div className="task-form">

        <input
          type="text"
          placeholder="Enter task name"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        <input
          type="number"
          min="0.5"
          step="0.5"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />

        <button onClick={addTask}>
          + Add Task
        </button>

      </div>

      {/* TASK LIST */}
      <div className="task-list">

        {tasks.length === 0 ? (
          <div className="empty-task">
            <h3>No tasks yet</h3>
            <p>Add your first task above.</p>
          </div>
        ) : (

          tasks.map((task) => (

            <div className="task-item" key={task.id}>

              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => completeTask(task.id)}
              />

              <div className="task-details">

                <h3
                  className={
                    task.completed ? "done" : ""
                  }
                >
                  {task.title}
                </h3>

                <p>
                  {task.priority} Priority • {task.time} hours
                </p>

              </div>

              <button
                className="delete-task"
                onClick={() => deleteTask(task.id)}
              >
                Delete
              </button>

            </div>

          ))

        )}

      </div>

    </div>
  );
}

export default Tasks;