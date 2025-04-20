
function confirmDelete(courseName, deleteUrl) {
    if (confirm("Are you sure you want to delete the course: " + courseName + "?")) {
        window.location.href = deleteUrl;
    }
}

function showAlert(message) {
    if (message) {
        alert(message);
    }
}
