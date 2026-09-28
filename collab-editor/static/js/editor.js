// ===========================================
// CodeCollab Pro
// editor.js
// ===========================================

const socket = io();

// -------------------------------------------
// USERNAME
// -------------------------------------------

let username = prompt("Enter your name");

if (!username || username.trim() === "") {
    username = "Guest";
}

// -------------------------------------------
// EDITOR
// -------------------------------------------

const editor = CodeMirror.fromTextArea(
    document.getElementById("editor"),
    {
        mode: LANGUAGE,
        theme: "material-darker",
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        lineWrapping: true,
        autofocus: true
    }
);

// -------------------------------------------
// JOIN ROOM
// -------------------------------------------

socket.emit("join", {
    room: ROOM_ID,
    username: username
});

// -------------------------------------------
// RECEIVE EXISTING CODE
// -------------------------------------------

socket.on("load_code", function (data) {

    editor.setValue(data.code);

    updateCharacterCount();

});

// -------------------------------------------
// SEND CODE CHANGES
// -------------------------------------------

let typingTimer = null;

editor.on("change", function (cm, change) {

    if (change.origin === "setValue") return;

    const code = editor.getValue();

    socket.emit("code_change", {

        room: ROOM_ID,

        code: code

    });

    updateCharacterCount();

    clearTimeout(typingTimer);

    document.getElementById("saveStatus").innerText =
        "Saving...";

    typingTimer = setTimeout(function () {

        socket.emit("save_document", {

            room: ROOM_ID

        });

    }, 1500);

});

// -------------------------------------------
// RECEIVE LIVE UPDATE
// -------------------------------------------

socket.on("code_update", function (data) {

    const cursor = editor.getCursor();

    editor.setValue(data.code);

    editor.setCursor(cursor);

    updateCharacterCount();

});

// -------------------------------------------
// SAVE STATUS
// -------------------------------------------

socket.on("saved", function () {

    document.getElementById("saveStatus").innerText =
        "Saved";

});

// -------------------------------------------
// LANGUAGE
// -------------------------------------------

const languageSelect =
document.getElementById("language");

languageSelect.value = LANGUAGE;

languageSelect.addEventListener("change", function () {

    const language = this.value;

    socket.emit("language_change", {

        room: ROOM_ID,

        language: language

    });

    changeMode(language);

});

socket.on("language_update", function (data) {

    languageSelect.value = data.language;

    changeMode(data.language);

});

// -------------------------------------------
// CHANGE EDITOR MODE
// -------------------------------------------

function changeMode(language){

    switch(language){

        case "python":

            editor.setOption("mode","python");

            break;

        case "javascript":

            editor.setOption("mode","javascript");

            break;

        case "java":

            editor.setOption("mode","text/x-java");

            break;

        case "cpp":

            editor.setOption("mode","text/x-c++src");

            break;

        case "c":

            editor.setOption("mode","text/x-csrc");

            break;

    }

}

// -------------------------------------------
// USER JOIN
// -------------------------------------------

socket.on("user_joined", function(data){

    document.getElementById("onlineCount")
        .innerText = data.users;

});

// -------------------------------------------
// USER LEFT
// -------------------------------------------

socket.on("user_left", function(data){

    document.getElementById("onlineCount")
        .innerText = data.users;

});

// -------------------------------------------
// COPY ROOM
// -------------------------------------------

document
.getElementById("copyRoom")
.addEventListener("click", function () {

    const link = window.location.href; // full invite link, not just the room ID
    const btn = this;
    const originalText = btn.textContent;

    function showCopied() {
        btn.textContent = "Copied!";
        btn.classList.add("copied");
        setTimeout(function () {
            btn.textContent = originalText;
            btn.classList.remove("copied");
        }, 1500);
    }

    function fallbackCopy() {
        const tempInput = document.createElement("textarea");
        tempInput.value = link;
        tempInput.style.position = "fixed";
        tempInput.style.opacity = "0";
        document.body.appendChild(tempInput);
        tempInput.focus();
        tempInput.select();
        try {
            document.execCommand("copy");
            showCopied();
        } catch (err) {
            console.error("Copy failed:", err);
            btn.textContent = "Copy failed";
            setTimeout(function () { btn.textContent = originalText; }, 1500);
        }
        document.body.removeChild(tempInput);
    }

    // Clipboard API only works on https:// or localhost — fall back otherwise
    // (e.g. testing over a LAN IP like http://192.168.x.x:5000)
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(link).then(showCopied).catch(fallbackCopy);
    } else {
        fallbackCopy();
    }

});

// -------------------------------------------
// CHARACTER COUNT
// -------------------------------------------

function updateCharacterCount(){

    const count = editor
        .getValue()
        .length;

    document
        .getElementById("characterCount")
        .innerText =
        "Characters : " + count;

}

updateCharacterCount();

// -------------------------------------------
// LEAVE ROOM
// -------------------------------------------

document
.getElementById("leaveRoom")
.addEventListener("click",function(){

    socket.emit("leave",{

        room:ROOM_ID,

        username:username

    });

    window.location="/";

});

// -------------------------------------------
// DISCONNECT
// -------------------------------------------

window.addEventListener("beforeunload",function(){

    socket.emit("leave",{

        room:ROOM_ID,

        username:username

    });

});

// -------------------------------------------
// CONNECTION STATUS
// -------------------------------------------

socket.on("connect",function(){

    document
        .getElementById("saveStatus")
        .innerText="Connected";

});

socket.on("disconnect",function(){

    document
        .getElementById("saveStatus")
        .innerText="Disconnected";

});