// SkillShare JavaScript
// ===============================

// Navbar Shadow
window.addEventListener("scroll", () => {

    const navbar = document.querySelector(".navbar");

    if (navbar) {
        if (window.scrollY > 50) {
            navbar.classList.add("active");
        } else {
            navbar.classList.remove("active");
        }
    }

});

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(link => {

    link.addEventListener("click", function (e) {

        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if (target) {
            target.scrollIntoView({
                behavior: "smooth"
            });
        }

    });

});

// Fade Animation
const cards = document.querySelectorAll(".step-card, .skill-card, .learner-card");

const observer = new IntersectionObserver(entries => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {
            entry.target.classList.add("show");
        }

    });

});

cards.forEach(card => observer.observe(card));
// Scroll Reveal

const reveals = document.querySelectorAll(".reveal");

function revealSections(){

    reveals.forEach(section=>{

        const windowHeight = window.innerHeight;

        const top = section.getBoundingClientRect().top;

        if(top < windowHeight - 120){

            section.classList.add("active");

        }

    });

}

window.addEventListener("scroll", revealSections);

revealSections();