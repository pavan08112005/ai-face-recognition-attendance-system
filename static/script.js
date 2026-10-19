
 // ==============================
 // PAGE NAVIGATION
 // ==============================

function showPage(pageId, button) {
    const pages = document.querySelectorAll(".page");

    pages.forEach(page => {
        page.classList.remove("active-page");
    });

    const selectedPage = document.getElementById(pageId);

    if (selectedPage) {
        selectedPage.classList.add("active-page");
    }

    const buttons = document.querySelectorAll(".nav-item");

    buttons.forEach(btn => {
        btn.classList.remove("active");
    });

    if (button) {
        button.classList.add("active");
    }

    if (pageId === "dashboard") {
        loadDashboard();
    }

    if (pageId === "students") {
        loadStudents();
    }

    if (pageId === "records") {
        loadAttendance();
    }
}


// ==============================
// ATTENDANCE RECORDS DATA
// ==============================

let allAttendanceRecords = [];


// ==============================
// DATE
// ==============================

function updateDate() {
    const dateElement = document.getElementById("currentDate");

    if (!dateElement) return;

    const now = new Date();

    dateElement.textContent = now.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}


// ==============================
// DASHBOARD
// ==============================

async function loadDashboard() {
    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Failed to load dashboard");
        }

        const data = await response.json();

        const totalStudents = document.getElementById("totalStudents");
        const presentToday = document.getElementById("presentToday");
        const absentToday = document.getElementById("absentToday");
        const attendancePercentage = document.getElementById(
            "attendancePercentage"
        );

        if (totalStudents) {
            totalStudents.textContent = data.total_students;
        }

        if (presentToday) {
            presentToday.textContent = data.present_today;
        }

        if (absentToday) {
            absentToday.textContent = data.absent_today;
        }

        if (attendancePercentage) {
            attendancePercentage.textContent =
                data.attendance_percentage + "%";
        }

        await loadTodayAttendance();
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}


// ==============================
// TODAY ATTENDANCE
// ==============================

async function loadTodayAttendance() {
    try {
        const response = await fetch("/api/attendance");

        if (!response.ok) {
            throw new Error("Failed to load today's attendance");
        }

        const records = await response.json();

        // Get today's date using local time.
        const now = new Date();

        const today =
            now.getFullYear() +
            "-" +
            String(now.getMonth() + 1).padStart(2, "0") +
            "-" +
            String(now.getDate()).padStart(2, "0");

        const todayRecords = records.filter(
            record => record.date === today
        );

        const table = document.getElementById("todayTable");

        if (!table) return;

        table.innerHTML = "";

        if (todayRecords.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align:center;">
                        No attendance recorded today.
                    </td>
                </tr>
            `;
            return;
        }

        todayRecords.forEach(record => {
            const row = document.createElement("tr");

            [
                record.student_id,
                record.name,
                record.date,
                record.time,
                record.session
            ].forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value ?? "";
                row.appendChild(cell);
            });

            const statusCell = document.createElement("td");
            const status = document.createElement("span");

            status.className = "status";
            status.textContent = "Present";

            statusCell.appendChild(status);
            row.appendChild(statusCell);

            table.appendChild(row);
        });
    } catch (error) {
        console.error("Attendance error:", error);
    }
}


// ==============================
// STUDENTS
// ==============================

async function loadStudents() {
    try {
        const response = await fetch("/api/students");

        if (!response.ok) {
            throw new Error("Failed to load students");
        }

        const students = await response.json();

        const table = document.getElementById("studentsTable");
        const studentCount = document.getElementById("studentCount");

        if (!table) return;

        table.innerHTML = "";

        if (students.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="3" style="text-align:center;">
                        No registered students.
                    </td>
                </tr>
            `;

            if (studentCount) {
                studentCount.textContent = "0 Students";
            }

            return;
        }

        students.forEach(student => {
            const row = document.createElement("tr");

            const values = [
                student.student_id,
                student.name,
                formatDateTime(student.created_at)
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value ?? "";
                row.appendChild(cell);
            });

            table.appendChild(row);
        });

        if (studentCount) {
            studentCount.textContent =
                `${students.length} Student(s)`;
        }
    } catch (error) {
        console.error("Students error:", error);
    }
}


// ==============================
// ATTENDANCE RECORDS
// ==============================

async function loadAttendance() {
    try {
        const response = await fetch("/api/attendance");

        if (!response.ok) {
            throw new Error("Failed to load attendance records");
        }

        const records = await response.json();

        allAttendanceRecords = Array.isArray(records)
            ? records
            : [];

        filterAttendanceByDate();
    } catch (error) {
        console.error("Records error:", error);

        const table = document.getElementById("recordsTable");

        if (table) {
            table.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align:center;">
                        Unable to load attendance records.
                    </td>
                </tr>
            `;
        }
    }
}


// ==============================
// FILTER ATTENDANCE BY DATE
// ==============================

function filterAttendanceByDate() {
    const dateInput = document.getElementById(
        "attendanceDateFilter"
    );

    const selectedDate = dateInput ? dateInput.value : "";

    const filteredRecords = selectedDate
        ? allAttendanceRecords.filter(
              record => record.date === selectedDate
          )
        : allAttendanceRecords;

    const table = document.getElementById("recordsTable");

    if (!table) return;

    table.innerHTML = "";

    if (filteredRecords.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 5;
        cell.style.textAlign = "center";
        cell.textContent = selectedDate
            ? "No attendance records for this date."
            : "No attendance records.";

        row.appendChild(cell);
        table.appendChild(row);

        return;
    }

    filteredRecords.forEach(record => {
        const row = document.createElement("tr");

        [
            record.student_id,
            record.name,
            record.date,
            record.time,
            record.session
        ].forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "";
            row.appendChild(cell);
        });

        table.appendChild(row);
    });
}


// ==============================
// CLEAR DATE FILTER
// ==============================

function clearAttendanceDateFilter() {
    const dateInput = document.getElementById(
        "attendanceDateFilter"
    );

    if (dateInput) {
        dateInput.value = "";
    }

    filterAttendanceByDate();
}


// ==============================
// REGISTER STUDENT
// ==============================

async function registerStudent() {
    const studentId = document
        .getElementById("studentId")
        .value.trim();

    const studentName = document
        .getElementById("studentName")
        .value.trim();

    const message = document.getElementById("registerMessage");

    if (!studentId || !studentName) {
        message.textContent =
            "Please enter Student ID and Name.";
        return;
    }

    // Ask for the admin password.
    const password = prompt(
        "Enter admin password to register this student:"
    );

    if (password === null || !password.trim()) {
        message.textContent =
            "Registration cancelled. Admin password is required.";
        return;
    }

    message.textContent = "Starting face registration...";

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Admin-Password": password
            },
            body: JSON.stringify({
                student_id: studentId,
                name: studentName
            })
        });

        const data = await response.json();

        message.textContent =
            data.message || "Registration request completed.";

        if (response.ok) {
            loadStudents();
        }
    } catch (error) {
        message.textContent = "Unable to start registration.";

        console.error("Registration error:", error);
    }
}


// ==============================
// LIVE ATTENDANCE
// ==============================

async function startAttendance() {
    const message = document.getElementById("attendanceMessage");

    message.textContent = "Starting attendance camera...";

    try {
        const response = await fetch("/api/start-attendance", {
            method: "POST"
        });

        const data = await response.json();

        message.textContent =
            data.message || "Attendance request completed.";

    } catch (error) {
        message.textContent = "Unable to start attendance.";

        console.error("Attendance start error:", error);
    }
}


// ==============================
// CSV DOWNLOAD
// ==============================

function downloadCSV() {
    window.location.href = "/api/export";
}


// ==============================
// FORMAT DATE
// ==============================

function formatDateTime(value) {
    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}


// ==============================
// INITIAL LOAD
// ==============================

document.addEventListener("DOMContentLoaded", function () {
    updateDate();
    loadDashboard();
});
