(function(){
    'use strict';

    /* Navbar scroll */
    window.addEventListener('scroll', function(){
        var nav = document.getElementById('mainNav');
        if (nav) nav.classList.toggle('scrolled', window.scrollY > 80);
    }, { passive: true });

    /* WhatsApp tooltip */
    var waFloat = document.querySelector('.whatsapp-float');
    if (waFloat) {
        setTimeout(function(){ waFloat.classList.add('wa-show-tip'); setTimeout(function(){ waFloat.classList.remove('wa-show-tip'); }, 4000); }, 5000);
    }

    /* GSAP or fallback reveal */
    var hasGSAP = (typeof gsap !== 'undefined') && (typeof ScrollTrigger !== 'undefined');
    if (hasGSAP) {
        gsap.registerPlugin(ScrollTrigger);
        gsap.utils.toArray('.reveal').forEach(function(el) {
            gsap.fromTo(el,
                { opacity: 0, y: 32, scale: 0.98 },
                { opacity: 1, y: 0, scale: 1, duration: 0.85, ease: 'power3.out',
                  scrollTrigger: { trigger: el, start: 'top 95%', toggleActions: 'play none none none' }
                }
            );
        });
    } else {
        var obs = new IntersectionObserver(function(entries){
            entries.forEach(function(e){ if (e.isIntersecting) e.target.classList.add('visible'); });
        }, { threshold: 0.05 });
        document.querySelectorAll('.reveal').forEach(function(el){ obs.observe(el); });
    }

    /* Auto-close mobile nav on link click */
    var navCollapse = document.getElementById('navbarNav');
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function(link){
        link.addEventListener('click', function(){
            if (navCollapse && navCollapse.classList.contains('show') && typeof bootstrap !== 'undefined') {
                bootstrap.Collapse.getOrCreateInstance(navCollapse, { toggle: false }).hide();
            }
        });
    });

    /* Diseases strip: RAF auto-scroll + drag + pause on interaction */
    (function() {
        var track = document.getElementById('dsTrack');
        if (!track) return;

        var offset    = 0;
        var speed     = 0.45;
        var halfW     = 0;
        var isPaused  = false;
        var isMouseDown = false, isTouchActive = false;
        var didDrag   = false;
        var startX    = 0;
        var resumeTimer = null;

        function getHalfW() {
            if (!halfW) halfW = track.scrollWidth / 2;
            return halfW;
        }

        function wrapOffset() {
            var hw = getHalfW();
            if (!hw) return;
            while (offset > 0)   offset -= hw;
            while (offset < -hw) offset += hw;
        }

        (function tick() {
            if (!isPaused) {
                offset -= speed;
                wrapOffset();
                track.style.transform = 'translateX(' + offset + 'px)';
            }
            requestAnimationFrame(tick);
        })();

        function pause() { isPaused = true; clearTimeout(resumeTimer); }
        function resume() { isPaused = false; }
        function scheduleResume(ms) {
            clearTimeout(resumeTimer);
            resumeTimer = setTimeout(resume, ms || 3000);
        }

        var touchStartY = 0, isHoriz = null;
        track.addEventListener('touchstart', function(e) {
            startX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            isHoriz = null; didDrag = false; isTouchActive = true;
            pause();
        }, { passive: true });

        track.addEventListener('touchmove', function(e) {
            if (!isTouchActive) return;
            var dx = e.touches[0].clientX - startX;
            var dy = e.touches[0].clientY - touchStartY;
            if (isHoriz === null && (Math.abs(dx) > 5 || Math.abs(dy) > 5))
                isHoriz = Math.abs(dx) > Math.abs(dy);
            if (isHoriz) {
                didDrag = true;
                offset += dx;
                wrapOffset();
                track.style.transform = 'translateX(' + offset + 'px)';
                startX = e.touches[0].clientX;
            }
        }, { passive: true });

        track.addEventListener('touchend', function() {
            isTouchActive = false; isHoriz = null;
            scheduleResume(3000);
        }, { passive: true });

        track.addEventListener('mousedown', function(e) {
            startX = e.clientX; didDrag = false; isMouseDown = true;
            pause();
            track.style.cursor = 'grabbing';
            e.preventDefault();
        });

        document.addEventListener('mousemove', function(e) {
            if (!isMouseDown) return;
            var dx = e.clientX - startX;
            if (Math.abs(dx) > 3) didDrag = true;
            offset += dx;
            wrapOffset();
            track.style.transform = 'translateX(' + offset + 'px)';
            startX = e.clientX;
        });

        document.addEventListener('mouseup', function() {
            if (!isMouseDown) return;
            isMouseDown = false;
            track.style.cursor = 'grab';
            scheduleResume(3000);
        });

        track.addEventListener('click', function(e) {
            if (didDrag) { didDrag = false; e.preventDefault(); return; }
            var link = e.target.closest('a[href]');
            if (link && link.getAttribute('tabindex') !== '-1')
                window.location.href = link.getAttribute('href');
        });
    })();

})();
