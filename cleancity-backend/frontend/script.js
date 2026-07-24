function checkBackend() {

    document.getElementById("backendStatus").innerText =
        " Checking...";

    fetch("/api/health")
        .then(response => response.json())
        .then(data => {

            document.getElementById("backendStatus").innerText =
                " " + data.message;

        })
        .catch(error => {

            document.getElementById("backendStatus").innerText =
                " Backend connection failed";

            console.error(error);

        });
}
