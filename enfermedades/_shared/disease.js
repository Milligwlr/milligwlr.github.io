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


    /* Reading progress bar (auto-inject if page lacks one) */
    (function(){
        if (document.querySelector('.read-progress')) return;
        var wrap = document.createElement('div');
        wrap.className = 'read-progress'; wrap.setAttribute('aria-hidden','true');
        var bar = document.createElement('div'); bar.className = 'read-progress__bar';
        wrap.appendChild(bar); document.body.appendChild(wrap);
        var doc = document.documentElement, ticking = false;
        function onScroll(){
            if (ticking) return; ticking = true;
            requestAnimationFrame(function(){
                var max = doc.scrollHeight - doc.clientHeight;
                bar.style.width = Math.max(0, Math.min(100, max>0 ? (doc.scrollTop/max)*100 : 0)) + '%';
                ticking = false;
            });
        }
        window.addEventListener('scroll', onScroll, {passive:true});
        window.addEventListener('resize', onScroll, {passive:true});
        onScroll();
    })();


    /* Shared CTA particle generator — fills empty .cta-band__particles (default landing blue). */
    (function(){
        var nodes = document.querySelectorAll('.cta-band__particles');
        if(!nodes.length) return;
        var anims=['p-drift-1','p-drift-2','p-drift-3','p-drift-4','p-drift-5','p-drift-6','p-drift-7','p-drift-8'];
        var r=Math.random;
        nodes.forEach(function(c){
            if(c.children.length) return; /* page already populated it */
            var attr=c.getAttribute('data-colors');
            var cols = attr ? attr.split('|') : ['rgba(9,132,227,','rgba(116,185,255,','rgba(0,206,201,','rgba(9,132,227,','rgba(116,185,255,'];
            var n=window.innerWidth<768?35:75;
            for(var i=0;i<n;i++){
                var s=document.createElement('span');
                var sz=(r()*5+2).toFixed(1)+'px';
                var col=cols[Math.floor(r()*cols.length)];
                var op=(r()*.55+.45).toFixed(2);
                s.className='cta-band__p';
                s.style.cssText='width:'+sz+';height:'+sz+';background:'+col+op+');top:'+Math.floor(r()*100)+'%;left:'+Math.floor(r()*100)+'%;animation:'+anims[Math.floor(r()*anims.length)]+' '+(r()*9+5).toFixed(1)+'s '+(r()*7).toFixed(1)+'s linear infinite;';
                c.appendChild(s);
            }
        });
    })();

})();
