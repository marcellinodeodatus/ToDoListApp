document.addEventListener("DOMContentLoaded", () => {
    const taskList = document.getElementById("task-list");
    let draggedTaskIndex = null;

    // Function to add tasks to the DOM
    function addTaskToDOM(task, index) {
        const li = document.createElement("li");
        li.setAttribute("draggable", "true");
        li.setAttribute("data-id", task.id); // Use task ID instead of index
        li.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");

        // Create checkbox for task completion
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = task.completed;

        // Create text node for task description
        const text = document.createElement("span");
        text.textContent = task.text;

        // Apply a 'completed' class if the task is already completed
        if (task.completed) {
            text.classList.add("completed");
        }

        // Create delete button for task
        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "Delete";
        deleteBtn.classList.add("btn", "btn-danger", "btn-sm", "delete-btn");

        // Add event listener for the delete button
        deleteBtn.addEventListener("click", () => {
            deleteTask(task.id);
        });

        // Add event listener for the checkbox
        checkbox.addEventListener("change", () => {
            toggleTask(task.id); // Use the task ID
            text.classList.toggle("completed", checkbox.checked); // Toggle completed class
        });

        // Append checkbox, text, and delete button to the list item
        li.appendChild(checkbox);
        li.appendChild(text);
        li.appendChild(deleteBtn);

        // Append the list item to the task list
        taskList.appendChild(li);

        // Event listeners for drag-and-drop
        li.addEventListener("dragstart", (e) => {
            draggedTaskIndex = task.id;  // Use task ID directly
            e.dataTransfer.effectAllowed = "move";
        });

        li.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "move";
        });

        li.addEventListener("drop", (e) => {
            e.preventDefault();
            const droppedTaskId = parseInt(e.target.closest('li').getAttribute('data-id'));  // Use task ID for drop
            if (draggedTaskIndex !== null && draggedTaskIndex !== droppedTaskId) {
                reorderTasks(draggedTaskIndex, droppedTaskId);  // Send task IDs to backend
            }
        });
    }

    // Function to delete task from the server
    function deleteTask(index) {
        fetch(`/delete/${index}`, {
            method: 'DELETE',
        })
        .then(response => response.json())
        .then(tasks => {
            taskList.innerHTML = '';
            tasks.forEach((task, i) => addTaskToDOM(task, i));
        })
        .catch(error => console.error('Error deleting task:', error));
    }

    // Function to toggle task completion status
    function toggleTask(index) {
        fetch(`/toggle/${index}`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(tasks => {
            taskList.innerHTML = '';
            tasks.forEach((task, i) => addTaskToDOM(task, i));
        })
        .catch(error => console.error('Error toggling task:', error));
    }

    // Function to reorder tasks
    function reorderTasks(fromTaskId, toTaskId) {
        fetch('/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ fromIndex: fromTaskId, toIndex: toTaskId })
        })
        .then(response => response.json())
        .then(tasks => {
            taskList.innerHTML = '';
            tasks.forEach(task => addTaskToDOM(task));  // Re-render tasks in new order
        })
        .catch(error => console.error('Error reordering tasks:', error));
    }


    // Load tasks when the page loads
    function loadTasks() {
        fetch('/tasks')
            .then(response => response.json())
            .then(tasks => {
                taskList.innerHTML = '';
                tasks.forEach(task => addTaskToDOM(task));
            })
            .catch(error => console.error('Error loading tasks:', error));
    }

    loadTasks();

    // Handle form submission and dynamically add new tasks
    const form = document.getElementById("todo-form");
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        const taskInput = document.getElementById("todo-input");
        const taskText = taskInput.value.trim();

        if (taskText !== '') {
            fetch('/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `task=${encodeURIComponent(taskText)}`
            })
            .then(response => response.json())
            .then(tasks => {
                taskList.innerHTML = '';
                tasks.forEach((task, i) => addTaskToDOM(task, i));
            });

            taskInput.value = '';
        }
    });
});
