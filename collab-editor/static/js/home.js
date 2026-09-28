// ======================================
// CodeCollab Pro
// Home Page
// ======================================

// Smooth page animation
window.addEventListener("load", () => {
    document.body.classList.add("loaded");
});

// ---------------------------
// Room Input
// ---------------------------

const roomInput = document.querySelector("input[name='room_id']");

if (roomInput) {

    roomInput.addEventListener("keypress", function(e){

        if(e.key === "Enter"){

            this.form.submit();

        }

    });

}

// ---------------------------
// Button Hover Animation
// ---------------------------

document.querySelectorAll("button").forEach(btn=>{

    btn.addEventListener("mouseenter",()=>{

        btn.style.transform="translateY(-3px)";

    });

    btn.addEventListener("mouseleave",()=>{

        btn.style.transform="translateY(0px)";

    });

});

// ---------------------------
// Random Welcome Messages
// ---------------------------

const messages=[

"Welcome to CodeCollab Pro 🚀",

"Collaborate Faster ⚡",

"Happy Coding 💻",

"Real-Time Collaboration 🌍",

"Powered by Flask + PostgreSQL"

];

let index=0;

const hero=document.querySelector(".hero p");

if(hero){

    setInterval(()=>{

        hero.innerHTML=messages[index];

        index++;

        if(index>=messages.length){

            index=0;

        }

    },3500);

}