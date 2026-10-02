
document.addEventListener('DOMContentLoaded', () => {
  // ---------- small UI helpers ----------
  const toast = document.getElementById('toast');
  if (toast) {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-8px)';
      toast.style.transition = '.35s ease';
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  document.querySelectorAll('[data-toggle-password]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      if (!input) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.textContent = input.type === 'password' ? 'Show' : 'Hide';
    });
  });

  document.querySelectorAll('input[type="tel"]').forEach(input => {
    input.addEventListener('input', () => {
      input.value = input.value.replace(/\D/g, '').slice(0, 10);
    });
  });

  // ---------- scroll progress + back-to-top ----------
  const progress = document.getElementById('scrollProgress');
  const backTop = document.getElementById('backTop');
  const updateScrollUI = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
    if (progress) progress.style.width = pct + '%';
    if (backTop) backTop.classList.toggle('show', window.scrollY > 500);
  };
  window.addEventListener('scroll', updateScrollUI, {passive:true});
  updateScrollUI();
  backTop?.addEventListener('click', () => window.scrollTo({top:0, behavior:'smooth'}));

  // ---------- mobile learner navigation ----------
  const sidebar = document.querySelector('.side-nav');
  if (sidebar) {
    const menu = document.createElement('button');
    menu.className = 'mobile-menu-btn';
    menu.type = 'button';
    menu.setAttribute('aria-label', 'Open navigation');
    menu.textContent = '☰';
    const backdrop = document.createElement('div');
    backdrop.className = 'mobile-backdrop';
    document.body.appendChild(backdrop);
    document.body.appendChild(menu);

    const closeMenu = () => {
      sidebar.classList.remove('mobile-open');
      backdrop.classList.remove('open');
      menu.textContent = '☰';
    };
    menu.addEventListener('click', () => {
      const open = sidebar.classList.toggle('mobile-open');
      backdrop.classList.toggle('open', open);
      menu.textContent = open ? '×' : '☰';
    });
    backdrop.addEventListener('click', closeMenu);
    sidebar.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMenu));
  }

  // ---------- reveal animation ----------
  const revealItems = document.querySelectorAll(
    '.course-card,.stat-cards>div,.mission-grid article,.feature-grid article,.contact-cards article,.settings-panel,.certificate-card,.progress-item,.admin-panel,.security-card'
  );
  revealItems.forEach(el => el.classList.add('reveal-on-scroll'));
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, {threshold:.08});
    revealItems.forEach(el => observer.observe(el));
  } else {
    revealItems.forEach(el => el.classList.add('is-visible'));
  }

  // ---------- Discover: search + category + sorting + favourites ----------
  const search = document.getElementById('courseSearch');
  const cards = [...document.querySelectorAll('.discover-card')];
  const chips = [...document.querySelectorAll('.chip')];
  const grid = document.getElementById('courseGrid');
  const empty = document.getElementById('noResults');

  if (search && grid && cards.length) {
    const resultBar = document.createElement('div');
    resultBar.className = 'course-result-bar';
    resultBar.innerHTML = '<span id="courseResultText"></span><select class="course-sort" aria-label="Sort courses"><option value="featured">Featured first</option><option value="rating">Highest rated</option><option value="title">A–Z</option></select>';
    search.closest('.search-bar')?.after(resultBar);
    const resultText = resultBar.querySelector('#courseResultText');
    const sort = resultBar.querySelector('.course-sort');

    const favorites = new Set(JSON.parse(localStorage.getItem('skillshare_favorites') || '[]').map(String));

    cards.forEach(card => {
      const id = card.querySelector('a[href*="/course/"], form[action*="/enroll/"]')?.getAttribute('href')?.match(/(\d+)/)?.[1]
        || card.querySelector('form')?.action?.match(/(\d+)/)?.[1]
        || card.querySelector('h3')?.textContent.trim();
      const visual = card.querySelector('.course-visual');
      if (visual && !visual.querySelector('.favorite-btn')) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'favorite-btn' + (favorites.has(String(id)) ? ' is-fav' : '');
        btn.textContent = favorites.has(String(id)) ? '♥' : '♡';
        btn.title = 'Save course';
        btn.setAttribute('aria-label', 'Save course');
        visual.appendChild(btn);
        btn.addEventListener('click', e => {
          e.preventDefault();
          e.stopPropagation();
          const key = String(id);
          if (favorites.has(key)) {
            favorites.delete(key);
            btn.classList.remove('is-fav');
            btn.textContent = '♡';
          } else {
            favorites.add(key);
            btn.classList.add('is-fav');
            btn.textContent = '♥';
          }
          localStorage.setItem('skillshare_favorites', JSON.stringify([...favorites]));
        });
      }
    });

    const getActive = () => document.querySelector('.chip.active')?.dataset.filter || 'all';
    const filter = () => {
      const q = (search.value || '').trim().toLowerCase();
      const active = getActive();
      let visible = [];
      cards.forEach(card => {
        const category = card.dataset.category || '';
        const hay = (card.dataset.search || '').toLowerCase();
        const ok = (active === 'all' || category === active) && hay.includes(q);
        card.style.display = ok ? '' : 'none';
        if (ok) visible.push(card);
      });

      const mode = sort?.value || 'featured';
      visible.sort((a,b) => {
        if (mode === 'title') return (a.querySelector('h3')?.textContent || '').localeCompare(b.querySelector('h3')?.textContent || '');
        if (mode === 'rating') return parseFloat((b.querySelector('.course-meta span')?.textContent || '0').replace(/[^\d.]/g,'')) - parseFloat((a.querySelector('.course-meta span')?.textContent || '0').replace(/[^\d.]/g,''));
        return (b.querySelector('.featured') ? 1 : 0) - (a.querySelector('.featured') ? 1 : 0);
      });
      visible.forEach(c => grid.appendChild(c));
      if (resultText) resultText.textContent = `${visible.length} course${visible.length === 1 ? '' : 's'} available`;
      if (empty) empty.style.display = visible.length ? 'none' : '';
    };
    search.addEventListener('input', filter);
    chips.forEach(ch => ch.addEventListener('click', () => {
      chips.forEach(x => x.classList.remove('active'));
      ch.classList.add('active');
      filter();
    }));
    sort?.addEventListener('change', filter);
    filter();
  }

  // ---------- password strength feedback ----------
  document.querySelectorAll('input[name="new_password"]').forEach(input => {
    const hint = document.createElement('small');
    hint.className = 'password-strength';
    hint.style.cssText = 'display:block;margin-top:4px;color:#718096;font-size:11px';
    input.parentElement?.appendChild(hint);
    input.addEventListener('input', () => {
      const n = input.value.length;
      hint.textContent = n === 0 ? '' : n < 6 ? 'Use at least 6 characters' : n < 9 ? 'Password strength: good' : 'Password strength: strong';
      hint.style.color = n >= 9 ? '#58e0a5' : n >= 6 ? '#70a5ff' : '#ff9aab';
    });
  });

  // ---------- dynamic lesson completion ----------
  document.querySelectorAll('[data-lesson-form]').forEach(form => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const card = form.closest('[data-course-lessons]');
      if (!btn || !card || btn.disabled) return;
      const progressValue = document.getElementById('courseProgressValue');
      const progressBar = document.getElementById('courseProgressBar');
      const progressLabel = document.getElementById('courseProgressLabel');
      const lessons = Math.max(1, Number(card.dataset.courseLessons || 10));
      const oldHTML = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = 'Completing lesson <span>✓</span>';
      try {
        const response = await fetch(form.action, {method:'POST', headers:{'X-Requested-With':'XMLHttpRequest','Accept':'application/json'}});
        if (!response.ok) throw new Error('Unable to save progress');
        const data = await response.json();
        const pct = Math.max(0, Math.min(100, Number(data.progress || 0)));
        if (progressValue) progressValue.textContent = pct + '%';
        if (progressBar) progressBar.style.width = pct + '%';
        if (progressLabel) progressLabel.textContent = data.completed ? 'Course complete' : 'Progress updated successfully';

        const completedCount = Math.min(lessons, Math.ceil((pct / 100) * lessons));
        document.querySelectorAll('[data-lesson]').forEach((lesson, index) => {
          const done = index < completedCount;
          lesson.classList.toggle('done', done);
          const marker = lesson.querySelector('span');
          if (marker) marker.textContent = done ? '✓' : String(index + 1).padStart(2, '0');
        });

        if (data.completed) {
          const banner = document.createElement('div');
          banner.className = 'completion-banner';
          banner.id = 'completionBanner';
          banner.innerHTML = '<span>✓</span><div><b>Congratulations! Course completed.</b><small>Your certificate is ready to download.</small></div><a class="gold-btn" href="/certificate/' + encodeURIComponent(card.dataset.courseId) + '/download">Get certificate ↓</a>';
          form.replaceWith(banner);
        } else {
          btn.disabled = false;
          btn.innerHTML = 'Complete next lesson <span>→</span>';
        }
      } catch (error) {
        btn.disabled = false;
        btn.innerHTML = oldHTML;
        if (progressLabel) progressLabel.textContent = 'Could not update progress. Please try again.';
      }
    });
  });

  // ---------- small dynamic polish ----------
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = Number(el.dataset.count || el.textContent.replace(/[^0-9.]/g,''));
    if (!Number.isFinite(target)) return;
    const duration = 700, start = performance.now();
    const tick = now => {
      const p = Math.min(1, (now - start) / duration);
      const value = Math.round(target * (1 - Math.pow(1 - p, 3)));
      el.textContent = value.toLocaleString();
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  document.querySelectorAll('.course-card').forEach(card => {
    card.addEventListener('pointermove', e => {
      if (window.innerWidth < 900) return;
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - .5;
      const y = (e.clientY - r.top) / r.height - .5;
      card.style.transform = `perspective(900px) rotateX(${(-y * 2).toFixed(2)}deg) rotateY(${(x * 2).toFixed(2)}deg) translateY(-3px)`;
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
  });

  // ---------- prevent accidental double submits ----------
  document.querySelectorAll('form').forEach(form => {
    if (form.matches('[data-no-lock]')) return;
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"]');
      if (button && !button.disabled && !form.action.includes('/lesson')) {
        setTimeout(() => {
          button.disabled = true;
          button.style.opacity = '.7';
        }, 10);
      }
    });
  });
});
