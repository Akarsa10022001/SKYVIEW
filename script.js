/* ============================================================
   Sky View Real Estate — interactions
   ============================================================ */
(function () {
  'use strict';

  var body = document.body;
  var FORM_ENDPOINT = body.getAttribute('data-form-endpoint') || '';
  var WA_NUMBER = body.getAttribute('data-wa') || '';
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }

  /* ---------- Scroll reveal ---------- */
  var reveals = $$('.reveal');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Stat counters ----------
     The true figure is already in the HTML, so if JS or rAF never runs the
     page still shows the correct number rather than a stranded zero. */
  function runCount(el) {
    var target = parseInt(el.dataset.to, 10);
    if (reduceMotion || isNaN(target)) { return; }

    var dur = 1400, start = null, done = false;
    function finish() { if (!done) { done = true; el.textContent = target; } }
    var guard = setTimeout(finish, dur + 900);

    function step(ts) {
      if (done) return;
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      el.textContent = Math.round(eased * target);
      if (p < 1) { requestAnimationFrame(step); }
      else { clearTimeout(guard); done = true; }
    }
    el.textContent = '0';
    requestAnimationFrame(step);
  }
  var counters = $$('.count');
  if ('IntersectionObserver' in window && counters.length) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- Home: featured listing filter pills ---------- */
  var pills = $$('.filters button');
  if (pills.length) {
    pills.forEach(function (btn) {
      btn.addEventListener('click', function () {
        pills.forEach(function (b) { b.setAttribute('aria-selected', 'false'); });
        btn.setAttribute('aria-selected', 'true');
        var f = btn.dataset.filter;
        $$('#cardGrid .card').forEach(function (c) {
          c.hidden = !(f === 'all' || c.dataset.type === f);
        });
      });
    });
  }

  /* ---------- Listings page: search, filter, sort ---------- */
  var searchBar = $('#searchBar');
  if (searchBar) {
    var grid = $('#cardGrid');
    var cards = $$('.card', grid);
    var countEl = $('#resultCount');
    var emptyEl = $('#emptyState');
    var sortEl = $('#s-sort');

    function priceOf(card) {
      var t = $('.price', card).textContent.replace(/[^\d]/g, '');
      return parseInt(t, 10) || 0;
    }
    function areaOf(card) {
      var t = $('.specs span', card).textContent.replace(/[^\d]/g, '');
      return parseInt(t, 10) || 0;
    }

    function apply() {
      var purpose = $('#s-purpose').value;
      var kind = $('#s-kind').value;
      var beds = $('#s-beds').value;
      var q = $('#s-q').value.trim().toLowerCase();
      var shown = 0;

      cards.forEach(function (c) {
        var ok = true;
        if (purpose && c.dataset.type !== purpose) ok = false;
        if (kind && c.dataset.kind !== kind) ok = false;
        if (beds) {
          var b = parseInt($$('.specs span', c)[1].textContent.replace(/\D/g, ''), 10) || 0;
          ok = ok && (beds === '5' ? b >= 5 : b === parseInt(beds, 10));
        }
        if (q && c.textContent.toLowerCase().indexOf(q) === -1) ok = false;
        c.hidden = !ok;
        if (ok) shown++;
      });

      if (countEl) countEl.textContent = shown + (shown === 1 ? ' property' : ' properties');
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    function sortCards() {
      var mode = sortEl ? sortEl.value : 'new';
      var arr = cards.slice();
      if (mode === 'low') arr.sort(function (a, b) { return priceOf(a) - priceOf(b); });
      else if (mode === 'high') arr.sort(function (a, b) { return priceOf(b) - priceOf(a); });
      else if (mode === 'area') arr.sort(function (a, b) { return areaOf(b) - areaOf(a); });
      arr.forEach(function (c) { grid.appendChild(c); });
    }

    searchBar.addEventListener('submit', function (e) { e.preventDefault(); apply(); });
    ['#s-purpose', '#s-kind', '#s-beds'].forEach(function (sel) {
      $(sel).addEventListener('change', apply);
    });
    $('#s-q').addEventListener('input', apply);
    if (sortEl) sortEl.addEventListener('change', function () { sortCards(); apply(); });

    var clearBtn = $('#clearFilters');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        searchBar.reset();
        apply();
      });
    }

    // Honour ?purpose= / ?kind= / ?beds= from nav and footer links
    var params = new URLSearchParams(location.search);
    ['purpose', 'kind', 'beds'].forEach(function (k) {
      var v = params.get(k);
      var el = $('#s-' + k);
      if (v && el) el.value = v;
    });
    apply();
  }

  /* ---------- Reviews: rendered from data/reviews.json ----------
     Kept out of the markup on purpose so the client can swap in real reviews
     without touching HTML. If the file is missing or the array is empty the
     whole section removes itself rather than showing invented testimonials. */
  var revSection = $('[data-reviews]');
  if (revSection) {
    var track = $('#revTrack');
    var dotWrap = $('#revDots');
    var base = location.pathname.indexOf('/property/') > -1 ||
               location.pathname.indexOf('/blog/') > -1 ? '../' : '';

    fetch(base + 'data/reviews.json')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        var list = (data && data.reviews) || [];
        if (!list.length) { revSection.remove(); return; }

        list.forEach(function (rv) {
          var initials = (rv.author || '?').split(' ')
            .map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase();
          var el = document.createElement('article');
          el.className = 'rev';
          el.innerHTML =
            '<div class="rev__top">' +
              '<h3></h3>' +
              '<span class="rev__mono" aria-hidden="true"></span>' +
            '</div>' +
            '<p></p>' +
            '<div class="rev__foot">' +
              '<span class="who"></span>' +
              '<span class="where"></span>' +
            '</div>';
          $('h3', el).textContent = rv.heading || '';
          $('.rev__mono', el).textContent = initials;
          $('p', el).textContent = rv.quote || '';
          $('.who', el).textContent = rv.author || '';
          $('.where', el).textContent = rv.location || '';
          track.appendChild(el);
        });

        if (data._status === 'placeholder') {
          console.info('[Sky View] reviews.json is still placeholder content — ' +
                       'replace with real reviews before launch.');
        }

        // dots
        var slides = $$('.rev', track);
        slides.forEach(function (_, idx) {
          var d = document.createElement('button');
          d.type = 'button';
          d.setAttribute('aria-label', 'Go to review ' + (idx + 1));
          d.setAttribute('aria-selected', idx === 0 ? 'true' : 'false');
          d.addEventListener('click', function () {
            slides[idx].scrollIntoView({
              behavior: reduceMotion ? 'auto' : 'smooth',
              inline: 'center', block: 'nearest'
            });
          });
          dotWrap.appendChild(d);
        });

        var t;
        track.addEventListener('scroll', function () {
          clearTimeout(t);
          t = setTimeout(function () {
            var mid = track.scrollLeft + track.clientWidth / 2;
            var best = 0, bestDist = Infinity;
            slides.forEach(function (s, j) {
              var c = s.offsetLeft + s.offsetWidth / 2;
              var dist = Math.abs(c - mid);
              if (dist < bestDist) { bestDist = dist; best = j; }
            });
            $$('button', dotWrap).forEach(function (d, k) {
              d.setAttribute('aria-selected', k === best ? 'true' : 'false');
            });
          }, 90);
        }, { passive: true });
      })
      .catch(function () { revSection.remove(); });
  }

  /* ---------- Showreel: click-to-load YouTube facade ----------
     No YouTube script or cookie until the visitor actually presses play. */
  var reel = $('#reel');
  if (reel) {
    var playBtn = $('.reel__play', reel);
    playBtn.addEventListener('click', function () {
      var id = reel.dataset.video;
      if (!id) return;
      var frame = document.createElement('iframe');
      frame.src = 'https://www.youtube-nocookie.com/embed/' + id +
                  '?autoplay=1&rel=0&modestbranding=1';
      frame.title = reel.dataset.title || 'Showreel';
      frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture';
      frame.allowFullscreen = true;
      frame.className = 'reel__frame';
      reel.innerHTML = '';
      reel.appendChild(frame);
    });
  }

  /* ---------- FAQ accordion (one open at a time) ---------- */
  var faqs = $$('.faq-item');
  faqs.forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (!d.open) return;
      faqs.forEach(function (o) { if (o !== d) o.open = false; });
    });
  });

  /* ---------- Mobile menu ---------- */
  var burger = $('.nav__burger');
  var links = $('.nav__links');
  if (burger && links) {
    burger.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        links.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        links.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }

  /* ---------- Nav background on scroll ---------- */
  var nav = $('.nav');
  if (nav && !nav.classList.contains('nav--solid')) {
    var last = null;
    var onScroll = function () {
      var scrolled = window.scrollY > 40;
      if (scrolled === last) return;
      last = scrolled;
      nav.classList.toggle('is-stuck', scrolled);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Forms ----------
     Posts to FORM_ENDPOINT when one is configured in build.py. With no
     endpoint set the submission falls back to opening a pre-filled WhatsApp
     message, so the form is genuinely usable rather than a dead end. */
  function waFallback(fields) {
    // Build the plain message first, then encode once — mixing raw text with
    // pre-encoded fragments leaves literal spaces in the URL.
    var text = 'New enquiry from the website\n\n' +
      'Name: ' + (fields.name || '') + '\n' +
      'Email: ' + (fields.email || '') + '\n' +
      'Phone: ' + (fields.phone || '—') + '\n' +
      'Message: ' + (fields.message || '—');
    return 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(text);
  }

  var lead = $('#leadForm');
  if (lead) {
    var note = $('#formNote');
    var submitBtn = $('button[type=submit]', lead);

    lead.addEventListener('submit', function (e) {
      e.preventDefault();
      var fields = {
        name: $('#f-name').value.trim(),
        email: $('#f-email').value.trim(),
        phone: $('#f-phone').value.trim(),
        message: $('#f-msg').value.trim()
      };

      function fail(msg) {
        note.hidden = false;
        note.className = 'form-note is-error';
        note.textContent = msg;
      }

      if (!fields.name || !fields.email) {
        return fail('Please add your name and email so we can reach you.');
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(fields.email)) {
        return fail('That email address doesn\'t look right — please check it.');
      }

      if (!FORM_ENDPOINT) {
        // No backend wired up yet: hand the enquiry to WhatsApp.
        note.hidden = false;
        note.className = 'form-note';
        note.textContent = 'Opening WhatsApp to send your enquiry…';
        window.open(waFallback(fields), '_blank', 'noopener');
        lead.reset();
        return;
      }

      submitBtn.disabled = true;
      var original = submitBtn.textContent;
      submitBtn.textContent = 'Sending…';
      note.hidden = true;

      fetch(FORM_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(fields)
      })
        .then(function (res) {
          if (!res.ok) throw new Error('Bad response ' + res.status);
          window.location.href = 'thank-you.html';
        })
        .catch(function () {
          submitBtn.disabled = false;
          submitBtn.textContent = original;
          note.hidden = false;
          note.className = 'form-note is-error';
          note.innerHTML = 'We couldn\'t send that just now. ' +
            '<a href="' + waFallback(fields) + '" target="_blank" rel="noopener">Send via WhatsApp</a> ' +
            'or email <a href="mailto:info@skyviewdubai.com">info@skyviewdubai.com</a>.';
        });
    });
  }

  var news = $('#newsForm');
  if (news) {
    news.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = $('input', news);
      var email = input.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      input.removeAttribute('aria-invalid');

      function done() {
        input.value = '';
        input.placeholder = 'Subscribed — thank you!';
      }
      if (!FORM_ENDPOINT) { done(); return; }
      fetch(FORM_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ type: 'newsletter', email: email })
      }).then(done).catch(done);
    });
  }
})();
