
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



let attendanceCameraStream = null;
let attendanceRecognitionTimer = null;
let attendanceRequestInProgress = false;

async function startAttendance() {
    const message = document.getElementById("attendanceMessage");
    const video = document.getElementById("attendanceVideo");
    const placeholder = document.getElementById("cameraPlaceholder");
    const startButton = document.getElementById("startAttendanceBtn");
    const stopButton = document.getElementById("stopAttendanceBtn");
    
    if (attendanceCameraStream) return;

    if (!navigator.mediaDevices?.getUserMedia) {
        message.textContent = "Camera access requires HTTPS or localhost.";
        attendanceAdminPassword = "";
        return;
    }

    message.textContent = "Requesting camera permission...";

    try {
        attendanceCameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user",
                width: { ideal: 640 },
                height: { ideal: 480 }
            },
            audio: false
        });

        video.srcObject = attendanceCameraStream;
        video.style.display = "block";
        placeholder.style.display = "none";
        startButton.style.display = "none";
        stopButton.style.display = "inline-block";

        await video.play();

        message.textContent = "Camera ready. Starting recognition...";

        // Wait for the video to produce usable frames.
        await new Promise(resolve => {
            if (video.videoWidth > 0) {
                resolve();
            } else {
                video.addEventListener("loadedmetadata", resolve, { once: true });
            }
        });

        attendanceRecognitionTimer = setInterval(
            recognizeAttendanceFrame,
            1500
        );
    } catch (error) {
        console.error("Camera startup error:", error);

        if (attendanceCameraStream) {
            attendanceCameraStream.getTracks().forEach(track => track.stop());
        }

        attendanceCameraStream = null;
        
        message.textContent = "Unable to start the camera. Check camera permission.";
    }
}

async function recognizeAttendanceFrame() {
    if (attendanceRequestInProgress || !attendanceCameraStream) return;

    const video = document.getElementById("attendanceVideo");
    const message = document.getElementById("attendanceMessage");

    if (!video.videoWidth || !video.videoHeight) return;

    attendanceRequestInProgress = true;

    try {
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve =>
            canvas.toBlob(resolve, "image/jpeg", 0.8)
        );

        if (!blob) {
            message.textContent = "Could not capture a camera frame.";
            return;
        }

        const formData = new FormData();
        formData.append("frame", blob, "frame.jpg");

        const response = await fetch("/api/recognize-frame", {
    method: "POST",
    body: formData
});

        const result = await response.json();

        

        if (result.recognized && result.success) {
            message.textContent = result.attendance_marked
                ? `Attendance marked: ${result.name} (${result.student_id})`
                : `${result.name}: attendance already marked.`;
        } else {
            message.textContent = result.message || "Face not recognized.";
        }
    } catch (error) {
        console.error("Recognition request failed:", error);
        message.textContent = "Could not contact the recognition server.";
    } finally {
        attendanceRequestInProgress = false;
    }
}

function stopAttendance() {
    const message = document.getElementById("attendanceMessage");
    const video = document.getElementById("attendanceVideo");
    const placeholder = document.getElementById("cameraPlaceholder");
    const startButton = document.getElementById("startAttendanceBtn");
    const stopButton = document.getElementById("stopAttendanceBtn");


    if (attendanceRecognitionTimer !== null) {
        clearInterval(attendanceRecognitionTimer);
        attendanceRecognitionTimer = null;
    }

    if (attendanceCameraStream) {
        attendanceCameraStream.getTracks().forEach(track => track.stop());
        attendanceCameraStream = null;
    }

    video.srcObject = null;
    video.style.display = "none";
    placeholder.style.display = "block";
    startButton.style.display = "inline-block";
    stopButton.style.display = "none";

    
    message.textContent = "Camera stopped.";
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
