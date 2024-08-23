document.addEventListener('DOMContentLoaded', function() {
    const featuresGrid = document.querySelector('.features-grid');
    const featuresCarousel = document.querySelector('.features-carousel');
    const featureItems = document.querySelectorAll('.feature-link');

    let isDragging = false;
    let startPos = 0;
    let currentTranslate = 0;
    let prevTranslate = 0;
    let animationID = null;

    // Configuración del carrusel
    function setupCarousel() {
        const totalWidth = Array.from(featureItems).reduce((width, item) => width + item.offsetWidth + 20, 0);
        console.log(totalWidth);
        featuresCarousel.style.width = `${totalWidth * 2}px`;

        // Duplicar elementos para efecto infinito
        featureItems.forEach(item => {
            const clone = item.cloneNode(true);
            featuresCarousel.appendChild(clone);
        });
    }

    setupCarousel();

    // Funciones de arrastre
    function startDrag(e) {
        if (e.type === 'touchstart') {
            startPos = e.touches[0].clientX;
        } else {
            startPos = e.clientX;
            e.preventDefault();
        }
        isDragging = true;
        animationID = requestAnimationFrame(animation);
        featuresCarousel.style.transition = 'none';
    }

    function drag(e) {
        if (isDragging) {
            const currentPosition = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
            currentTranslate = prevTranslate + currentPosition - startPos;
        }
    }

    function endDrag() {
        isDragging = false;
        cancelAnimationFrame(animationID);
        featuresCarousel.style.transition = 'transform 0.3s ease';
        
        const carouselWidth = featuresCarousel.offsetWidth / 2;
        if (Math.abs(currentTranslate) >= carouselWidth) {
            currentTranslate = currentTranslate % carouselWidth;
        }
        
        prevTranslate = currentTranslate;
        setTransform();
    }

    function animation() {
        setTransform();
        if (isDragging) requestAnimationFrame(animation);
    }

    function setTransform() {
        featuresCarousel.style.transform = `translateX(${currentTranslate}px)`;
    }

    // Event Listeners
    featuresGrid.addEventListener('mousedown', startDrag);
    featuresGrid.addEventListener('touchstart', startDrag);
    featuresGrid.addEventListener('mousemove', drag);
    featuresGrid.addEventListener('touchmove', drag);
    featuresGrid.addEventListener('mouseup', endDrag);
    featuresGrid.addEventListener('touchend', endDrag);
    featuresGrid.addEventListener('mouseleave', endDrag);

    // Prevenir clic durante el arrastre
    featuresGrid.addEventListener('click', function(e) {
        if (Math.abs(currentTranslate - prevTranslate) > 5) {
            e.preventDefault();
        }
    });

    // Animación automática
    let autoScrollInterval;

    function startAutoScroll() {
        autoScrollInterval = setInterval(() => {
            if (!isDragging) {
                currentTranslate -= 1;
                if (Math.abs(currentTranslate) >= featuresCarousel.offsetWidth / 2) {
                    currentTranslate = 0;
                }
                setTransform();
            }
        }, 20);
    }

    function stopAutoScroll() {
        clearInterval(autoScrollInterval);
    }

    featuresGrid.addEventListener('mouseenter', stopAutoScroll);
    featuresGrid.addEventListener('mouseleave', startAutoScroll);

    startAutoScroll();
});