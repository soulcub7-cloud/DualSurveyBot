const state = {
  role: 'admin',
  session: null,
  page: 'dashboard',
  data: null,
  mentorId: 1,
  studentId: 1,
  module: 'Все модули',
  draftProgress: {},
  showArchivedStudents: false,
  showArchivedMentors: false,
  showArchivedCourses: false,
  attendanceDate: new Date().toISOString().slice(0, 10),
  attendanceStream: '',
  profileStudentId: 1,
  evaluations: [],
  evaluationView: 'journal',
  evaluationStream: '',
  evaluationCourse: '',
  evaluationMonth: '',
  evaluationType: '',
  journalColumns: [],
  dashboardScheduleStream: '3',
  profileSkillType: 'all',
  matrixRows: [],
  matrixStream: '',
  matrixStudentId: 0,
  matrixSkillType: 'all',
  demoExamStream: '',
  demoExamStudentId: 0,
  quizCourseId: 0,
  quizQuestions: [],
  accounts: [],
};

const el = (selector, root = document) => root.querySelector(selector);
const els = (selector, root = document) => [...root.querySelectorAll(selector)];
const content = el('#content');

const NAV = {
  admin: [
    ['dashboard', 'Обзор', '⌂'],
    ['students', 'Студенты', 'С'],
    ['attendance', 'Посещаемость', 'П'],
    ['evaluations', 'Оценивание', 'О'],
    ['demo_exam', 'Демоэкзамен', 'Д'],
    ['mentors', 'Наставники', 'Н'],
    ['courses', 'Учебные курсы', '▤'],
    ['rotations', 'Ротации', '↔'],
    ['matrix', 'Матрица навыков', '✓'],
    ['reports', 'Аналитика', '↗'],
    ['accounts', 'Учётные записи', '◎'],
  ],
  mentor: [
    ['checklist', 'Чек-лист навыков', '✓'],
    ['attendance', 'Посещаемость', 'П'],
    ['evaluations', 'Оценивание', 'О'],
    ['demo_exam', 'Демоэкзамен', 'Д'],
    ['mentor_students', 'Мои студенты', 'С'],
    ['matrix', 'Матрица навыков', '▦'],
  ],
  student: [
    ['trajectory', 'Моя траектория', '↗'],
    ['courses', 'Мои курсы', '▤'],
    ['student_skills', 'Мои навыки', '✓'],
    ['demo_exam', 'Демоэкзамен', 'Д'],
  ],
};

const roleDefaults = { admin: 'dashboard', mentor: 'checklist', student: 'trajectory' };
const pageNames = {
  dashboard: 'Обзор', students: 'Студенты', attendance: 'Посещаемость', evaluations: 'Оценивание', demo_exam: 'Демоэкзамен', student_profile: 'Карточка студента', mentors: 'Наставники', courses: 'Учебные курсы', rotations: 'Ротации', matrix: 'Матрица навыков',
  reports: 'Аналитика', checklist: 'Чек-лист навыков', mentor_students: 'Мои студенты',
  trajectory: 'Моя траектория', student_skills: 'Мои навыки',
  accounts: 'Учётные записи',
};

function escapeHTML(value = '') {
  return String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

function canDeleteRecords() {
  return state.session?.can_delete !== false;
}

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase();
}

function formatDate(value, withYear = false) {
  if (!value) return '—';
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', ...(withYear ? { year: 'numeric' } : {}) }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value) {
  if (!value) return '';
  const normalized = value.includes('T') ? value : value.replace(' ', 'T') + 'Z';
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(normalized));
}

function statusClass(status) {
  const map = {
    'На практике': 'active', 'Активна': 'active', 'Подтверждено': 'confirmed', confirmed: 'confirmed',
    'Ожидает допуска': 'pending', 'Ожидает начала практики': 'planned', 'В процессе': 'in_progress', in_progress: 'in_progress',
    'Запланирована': 'planned', 'Завершена': 'finished', 'Завершил ротацию': 'finished', not_started: 'not_started', completed: 'confirmed',
  };
  return map[status] || 'finished';
}

function progressPct(student) {
  return Math.round(((student.skills_confirmed || 0) / Math.max(student.skills_total || 1, 1)) * 100);
}

function progressLabel(status) {
  return { not_started: 'Не начат', in_progress: 'В процессе', confirmed: 'Подтверждён' }[status] || status;
}

const attendanceLabels = {
  present: 'Присутствовал', late: 'Опоздал', excused: 'Уважительная причина', absent: 'Отсутствовал',
};
const evaluationLabels = { section: 'Итоги раздела', practical: 'Практическая работа (ЛПЗ)', rotation: 'Итоги ротации', practice: 'Итоги практики', demo_exam: 'Демоэкзамен' };
const gradeLabels = { 5: 'Отлично', 4: 'Хорошо', 3: 'Удовлетворительно', 2: 'Неудовлетворительно' };

const ACADEMIC_MONTHS = [
  ['Сентябрь', 5, '1–5'], ['Октябрь', 5, '5–9'], ['Ноябрь', 5, '10–14'], ['Декабрь', 5, '14–18'],
  ['Январь', 4, '19–22'], ['Февраль', 4, '23–26'], ['Март', 5, '27–31'], ['Апрель', 5, '31–35'],
  ['Май', 5, '36–40'], ['Июнь', 5, '40–44'], ['Июль', 4, 'каникулы'], ['Август', 4, 'каникулы'],
];

const ACADEMIC_SCHEDULES = {
  3: {
    course: 2,
    stream: 3,
    years: '2025–2028',
    specialty: 'Механизация сельского хозяйства',
    phases: [
      { span: 10, weeks: '1–9', type: 'theory', short: 'Теория', title: 'Теоретическое обучение' },
      { span: 9, weeks: '10–17', type: 'assembly', short: 'CT Assembly', title: 'Обработка деталей (252 часа)' },
      { span: 2, weeks: '18–19', type: 'holiday', short: 'К', title: 'Каникулы' },
      { span: 9, weeks: '20–28', type: 'assembly', short: 'CT Assembly', title: 'Монтаж узлов и механизмов сельскохозяйственных машин (324 часа)' },
      { span: 5, weeks: '29–32', type: 'reimann', short: 'Reimann', title: 'Восстановление деталей сельскохозяйственных машин (144 часа)' },
      { span: 5, weeks: '33–37', type: 'theory', short: 'Теория', title: 'Теоретическое обучение' },
      { span: 5, weeks: '38–41', type: 'assembly', short: 'CT Assembly', title: 'Обкатка, регулировка и испытание сельскохозяйственных машин (144 часа)' },
      { span: 2, weeks: '42–43', type: 'exam', short: 'ПА', title: 'Промежуточная аттестация' },
      { span: 1, weeks: '44', type: 'reserve', short: 'Р', title: 'Резервная неделя' },
      { span: 8, weeks: 'июль–август', type: 'holiday summer', short: 'К', title: 'Летние каникулы' },
    ],
  },
  2: {
    course: 3,
    stream: 2,
    years: '2024–2028',
    specialty: 'Профессиональное обучение',
    phases: [
      { span: 9, weeks: '1–8', type: 'assembly', short: 'CT Assembly', title: 'Основные части тракторов (288 часов)' },
      { span: 10, weeks: '9–17', type: 'theory', short: 'Теория', title: 'Теоретическое обучение' },
      { span: 2, weeks: '18–19', type: 'holiday', short: 'К', title: 'Каникулы' },
      { span: 7, weeks: '20–26', type: 'theory', short: 'Теория', title: 'Теоретическое обучение' },
      { span: 10, weeks: '27–35', type: 'agro', short: 'CT Agro', title: 'Неисправности и ремонтные работы систем, механизмов тракторов и сельскохозяйственных машин (324 часа)' },
      { span: 7, weeks: '36–41', type: 'agro', short: 'CT Agro', title: 'Выполнение сельскохозяйственных работ (252 часа)' },
      { span: 2, weeks: '42–43', type: 'exam', short: 'ПА', title: 'Промежуточная аттестация' },
      { span: 1, weeks: '44', type: 'reserve', short: 'Р', title: 'Резервная неделя' },
      { span: 8, weeks: 'июль–август', type: 'holiday summer', short: 'К', title: 'Летние каникулы' },
    ],
  },
  1: {
    course: 4,
    stream: 1,
    years: '2023–2027',
    specialty: 'Механизация сельского хозяйства',
    phases: [
      { span: 9, weeks: '1–8', type: 'agro', short: 'CT Agro', title: 'Эксплуатация и техническое обслуживание сельскохозяйственной техники (288 часов)' },
      { span: 10, weeks: '9–17', type: 'theory', short: 'Теория', title: 'Теоретическое обучение' },
      { span: 2, weeks: '18–19', type: 'holiday', short: 'К', title: 'Каникулы' },
      { span: 3, weeks: '20–22', type: 'theory', short: 'Т', title: 'Теоретическое обучение' },
      { span: 21, weeks: '23–41', type: 'assembly', short: 'CT Assembly', title: 'Организация работ по подготовке и эксплуатации сельскохозяйственной техники (696 часов)' },
      { span: 2, weeks: '42–43', type: 'exam', short: 'ИА', title: 'Итоговая аттестация' },
      { span: 1, weeks: '44', type: 'reserve', short: 'Р', title: 'Резервная неделя' },
      { span: 8, weeks: 'июль–август', type: 'holiday summer', short: 'К', title: 'Летние каникулы' },
    ],
  },
};

function plural(number, one, few, many) {
  const n10 = number % 10, n100 = number % 100;
  return n10 === 1 && n100 !== 11 ? one : (n10 >= 2 && n10 <= 4 && !(n100 >= 12 && n100 <= 14) ? few : many);
}

function sortedStreams(students) {
  return [...new Set(students.map(student => student.stream).filter(Boolean))].sort((a, b) => {
    const aNumber = Number(String(a).match(/\d+/)?.[0] || Number.MAX_SAFE_INTEGER);
    const bNumber = Number(String(b).match(/\d+/)?.[0] || Number.MAX_SAFE_INTEGER);
    return aNumber - bNumber || String(a).localeCompare(String(b), 'ru', { numeric: true });
  });
}

function nextRotationCaption(stats) {
  if (!stats.next_rotation_date) return 'Новых ротаций не запланировано';
  const days = Number(stats.next_rotation_days);
  const students = Number(stats.next_rotation_students || 0);
  const who = `${students} ${plural(students, 'студент', 'студента', 'студентов')}`;
  if (days <= 0) return `Следующая ротация сегодня · ${who}`;
  return `Ближайшая: ${formatDate(stats.next_rotation_date, true)} · через ${days} ${plural(days, 'день', 'дня', 'дней')} · ${who}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (response.status === 401 && !path.startsWith('/api/auth/')) showLogin();
  if (!response.ok) throw new Error(body.error || 'Не удалось выполнить запрос');
  return body;
}

async function loadData(silent = false) {
  if (!silent) content?.classList.add('content-loading');
  state.data = await api('/api/bootstrap');
  state.matrixRows = [];
  state.session = state.data.session;
  state.role = state.session.role;
  if (!NAV[state.role].some(([page]) => page === state.page)) state.page = roleDefaults[state.role];
  const sessionMentorId = Number(state.session.mentor_id || 0);
  if (sessionMentorId) state.mentorId = sessionMentorId;
  if (state.session.student_id) state.studentId = Number(state.session.student_id);
  const productionMentors = state.data.mentors.filter(mentor => Boolean(mentor.can_mentor));
  if (!sessionMentorId && !productionMentors.some(mentor => mentor.id === state.mentorId)) state.mentorId = productionMentors[0]?.id || 0;
  if (!state.data.dashboard.students.some(student => student.id === state.studentId)) state.studentId = state.data.dashboard.students[0]?.id || 0;
  content?.classList.remove('content-loading');
  renderChrome();
  await renderPage();
}

function renderChrome() {
  const unread = state.data.dashboard.notifications.filter(n => !n.is_read).length;
  const nav = NAV[state.role];
  el('#main-nav').innerHTML = `
    <div class="nav-label">Рабочее пространство</div>
    ${nav.map(([id, title, icon]) => `
      <button class="nav-item ${state.page === id || (state.page === 'student_profile' && (id === 'students' || id === 'mentor_students')) ? 'active' : ''}" data-page="${id}">
        <span class="nav-icon">${icon}</span><span>${title}</span>
        ${id === 'students' ? `<span class="nav-badge">${state.data.dashboard.stats.students}</span>` : ''}
      </button>`).join('')}
  `;
  el('#breadcrumbs').textContent = `CT Assembly Learning Hub  /  ${pageNames[state.page] || 'Обзор'}`;
  el('#notification-count').textContent = unread || '';
  el('#notification-count').style.display = unread ? 'grid' : 'none';
  const selected = state.session;
  const roleTitles = { admin: selected?.account_title || 'Учебный центр', mentor: 'Наставник', student: 'Студент' };
  el('#session-role').textContent = roleTitles[state.role] || state.role;
  el('#user-title').textContent = selected?.full_name || 'Учебный центр';
  el('#user-subtitle').textContent = state.role === 'mentor' ? 'Наставник' : state.role === 'student' ? 'Студент' : (selected?.account_title || 'Администратор');
  const avatar = el('.user-chip .avatar');
  if (avatar) avatar.textContent = initials(selected?.full_name || 'Учебный центр');
  renderNotifications();
}

function pageHead(eyebrow, title, description, actions = '') {
  return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div>${actions ? `<div class="page-actions">${actions}</div>` : ''}</div>`;
}

function statCard(label, value, foot, symbol, accent = 'orange') {
  const colors = {
    orange: ['#d71920', '#fdecee'], green: ['#6f8f38', '#eef4e7'], blue: ['#59636b', '#eef1f3'], purple: ['#3f474d', '#eceff1'],
  };
  const [color, soft] = colors[accent];
  return `<article class="stat-card" style="--accent:${color};--accent-soft:${soft}"><div class="stat-top"><span class="stat-label">${label}</span><span class="stat-symbol">${symbol}</span></div><div class="stat-value">${value}</div><div class="stat-foot">${foot}</div></article>`;
}

function personCell(student) {
  return `<div class="person"><div class="avatar" style="background:${student.avatar_color}">${initials(student.full_name)}</div><div><strong>${escapeHTML(student.full_name)}</strong><small>${escapeHTML(student.specialty || student.stream || '')}</small></div></div>`;
}

function dashboardAcademicSchedule() {
  const schedule = ACADEMIC_SCHEDULES[state.dashboardScheduleStream] || ACADEMIC_SCHEDULES[3];
  const practicePhases = schedule.phases.filter(phase => ['assembly', 'reimann', 'agro'].includes(phase.type));
  return `
    <div class="schedule-toolbar">
      <div class="schedule-stream-switch" role="group" aria-label="Выбор потока">
        ${[3, 2, 1].map(stream => {
          const item = ACADEMIC_SCHEDULES[stream];
          return `<button type="button" class="${Number(state.dashboardScheduleStream) === stream ? 'active' : ''}" data-dashboard-schedule-stream="${stream}"><strong>${stream} поток</strong><span>${item.course} курс</span></button>`;
        }).join('')}
      </div>
      <div class="schedule-selected-meta"><span>Выбран</span><strong>${schedule.course} курс · ${schedule.stream} поток</strong><small>${schedule.years} · ${escapeHTML(schedule.specialty)}</small></div>
    </div>
    <div class="academic-schedule-scroll" tabindex="0" aria-label="График учебного процесса: ${schedule.course} курс, ${schedule.stream} поток">
      <div class="academic-schedule-chart">
        <div class="academic-months">${ACADEMIC_MONTHS.map(([month, span, weeks]) => `<div style="grid-column:span ${span}"><strong>${month}</strong><span>${weeks} нед.</span></div>`).join('')}</div>
        <div class="academic-timeline">${schedule.phases.map(phase => `<div class="academic-phase ${phase.type}" style="grid-column:span ${phase.span}" title="${escapeHTML(`${phase.title} · недели ${phase.weeks}`)}"><strong>${escapeHTML(phase.short)}</strong><span>${escapeHTML(phase.weeks)}</span></div>`).join('')}</div>
        <div class="academic-week-ruler"><span>1</span><span>5</span><span>10</span><span>15</span><span>20</span><span>25</span><span>30</span><span>35</span><span>40</span><span>44 неделя</span><span>Июль</span><span>Август</span></div>
      </div>
    </div>
    <div class="schedule-practice-list">
      ${practicePhases.map(phase => `<article class="${phase.type}"><span></span><div><strong>${escapeHTML(phase.title)}</strong><small>Недели ${escapeHTML(phase.weeks)}</small></div></article>`).join('')}
    </div>
    <div class="schedule-legend">
      <span><i class="theory"></i>Теория</span><span><i class="assembly"></i>Практика в CT Assembly</span><span><i class="reimann"></i>Практика в ТОО Reimann</span><span><i class="agro"></i>Практика в CT Agro</span><span><i class="holiday"></i>Каникулы</span><span><i class="exam"></i>Аттестация</span>
    </div>`;
}

function dashboardCompetencyGroup(title, items, typeClass) {
  return `<div class="competency-group"><div class="competency-group-head"><strong>${title}</strong><span>${items.length}</span></div><div class="competency-chip-list">${items.map(item => `<span class="competency-chip ${typeClass}" title="${escapeHTML(item.description)}"><b>${escapeHTML(item.code)}</b>${escapeHTML(item.title)}</span>`).join('')}</div></div>`;
}

function renderDashboard() {
  const { stats, notifications } = state.data.dashboard;
  const hardSkills = state.data.skills.filter(skill => skill.category === 'Hard skill');
  const softSkills = state.data.skills.filter(skill => skill.category === 'Soft skill');
  content.innerHTML = `
    <div class="dashboard-page">
    <section class="dashboard-hero">
      ${pageHead('Учебный центр', 'Обзор программы', 'Контроль обучения, допусков и производственных ротаций в одном рабочем окне.', `<button class="button secondary" data-action="open-safety">Оформить допуск ТБ</button><button class="button primary" data-action="add-student"><span class="plus">+</span> Добавить студента</button>`)}
    </section>
    <div class="stats-grid">
      ${statCard('Всего студентов', stats.students, `<b>${stats.active_students}</b> сейчас на практике`, 'С', 'orange')}
      ${statCard('Наставники', stats.mentors, `${stats.supervisors || 0} ${plural(stats.supervisors || 0, 'руководитель', 'руководителя', 'руководителей')} практики`, 'Н', 'blue')}
      ${statCard('Учебные модули', state.data.courses.length, 'В действующей программе', '▤', 'purple')}
      ${statCard('Средний прогресс', `${stats.avg_progress}%`, 'По обязательным компетенциям', '✓', 'green')}
    </div>
    <section class="card dashboard-schedule">
      <div class="card-head"><div><h2>График учебного процесса 2026–2027</h2><p>Учебные недели, теория, практика, каникулы и аттестация</p></div><span class="schedule-source">Утверждённый график · 44 недели</span></div>
      ${dashboardAcademicSchedule()}
    </section>
    <section class="card dashboard-competencies">
      <div class="card-head"><div><h2>Компетенции к освоению</h2><p>Единый перечень результатов практической подготовки студентов</p></div><button class="text-link" data-page="matrix">Открыть матрицу →</button></div>
      <div class="competency-overview">${dashboardCompetencyGroup('Hard skills', hardSkills, 'hard')}${dashboardCompetencyGroup('Soft skills', softSkills, 'soft')}</div>
    </section>
    <section class="card dashboard-attention">
        <div class="card-head"><div><h2>Требует внимания</h2><p>${notifications.filter(n => !n.is_read).length} новых событий</p></div><button class="text-link" data-action="notifications">Открыть →</button></div>
        <div class="card-body stack">
          ${notifications.slice(0, 4).map(n => `<article class="alert-card ${n.kind}"><strong>${escapeHTML(n.title)}</strong><p>${escapeHTML(n.message)}</p><span class="alert-time">${formatDateTime(n.created_at)}</span></article>`).join('') || `<div class="empty"><strong>Всё спокойно</strong>Новых событий нет.</div>`}
        </div>
    </section></div>`;
}

function renderStudents(mentorOnly = false) {
  const mentor = state.data.mentors.find(m => m.id === state.mentorId);
  const archiveMode = !mentorOnly && state.showArchivedStudents;
  const base = mentorOnly
    ? state.data.dashboard.students.filter(s => s.mentor_id === state.mentorId)
    : archiveMode ? state.data.archived_students : state.data.dashboard.students;
  const adminActions = `<button class="button secondary" data-action="toggle-student-archive">${archiveMode ? '← Активные студенты' : `Архив (${state.data.archived_students.length})`}</button>${archiveMode ? '' : '<button class="button primary" data-action="add-student"><span class="plus">+</span> Добавить студента</button>'}`;
  content.innerHTML = `
    ${pageHead(mentorOnly ? 'Кабинет наставника' : archiveMode ? 'Архив контингента' : 'Контингент', mentorOnly ? 'Мои студенты' : archiveMode ? 'Архив студентов' : 'Студенты', mentorOnly ? `Закреплённые студенты · ${escapeHTML(mentor?.workshop || '')}` : archiveMode ? 'Архивные записи скрыты из активной работы, но вся история обучения сохранена.' : 'Карточки студентов, статусы допуска, наставники и освоение компетенций.', mentorOnly ? '' : adminActions)}
    ${mentorOnly ? `<div class="mentor-toolbar"><label><span class="label">Наставник</span><select class="select" data-select="mentor">${mentorOptions()}</select></label><div></div><button class="button secondary" data-page="checklist">Открыть чек-лист</button></div>` : ''}
    <div class="filters"><div class="search-box"><input class="input" id="student-search" placeholder="Поиск по ФИО или специальности"></div><select class="select filter-select" id="status-filter"><option value="">Все статусы</option><option>На практике</option><option>Ожидает начала практики</option><option>Ожидает допуска</option><option>Завершил ротацию</option></select><select class="select filter-select" id="stream-filter"><option value="">Все потоки</option>${sortedStreams(base).map(x => `<option>${escapeHTML(x)}</option>`).join('')}</select></div>
    <div class="students-grid" id="students-grid">${base.length ? base.map(student => studentCard(student, !mentorOnly)).join('') : `<div class="empty empty-card"><strong>${archiveMode ? 'Архив пуст' : 'Студенты не найдены'}</strong>${archiveMode ? 'Архивированные студенты появятся здесь.' : 'Добавьте первую запись.'}</div>`}</div>`;
}

function studentCard(student, adminControls = false) {
  const pct = progressPct(student);
  const actions = adminControls
    ? student.is_archived
      ? `<button class="button secondary small" data-action="restore-student" data-student-id="${student.id}">Восстановить</button>`
      : `<button class="button secondary small" data-student-profile="${student.id}">Карточка</button><button class="button secondary small" data-action="edit-student" data-student-id="${student.id}">Изменить</button>${canDeleteRecords() ? `<button class="button ghost small danger" data-action="archive-student" data-student-id="${student.id}">В архив</button>` : ''}`
    : `<button class="button secondary small" data-student-profile="${student.id}">Карточка</button>`;
  return `<article class="student-card" data-search="${escapeHTML(`${student.full_name} ${student.specialty}`.toLowerCase())}" data-status="${escapeHTML(student.status)}" data-stream="${escapeHTML(student.stream)}">
    <div class="student-card-top"><div class="avatar" style="background:${student.avatar_color}">${initials(student.full_name)}</div><span class="status ${statusClass(student.status)}">${escapeHTML(student.status)}</span></div>
    <h3>${escapeHTML(student.full_name)}</h3><p class="specialty">${escapeHTML(student.specialty)} · ${student.course} курс</p>
    <div class="info-grid"><div class="info-cell"><span>Поток / курс</span><strong>${escapeHTML(student.stream)} · ${student.course} курс</strong></div><div class="info-cell"><span>Наставник</span><strong>${escapeHTML(student.mentor_name || 'Не назначен')}</strong></div></div>
    <div class="card-footer"><div class="progress-line"><div class="progress-meta"><span>Компетенции</span><b>${pct}%</b></div><div class="bar"><span style="width:${pct}%"></span></div></div><div class="card-actions">${actions}</div></div>
  </article>`;
}

function mentorRegistryRows(people, archiveMode = false) {
  return people.map(mentor => {
    const isSupervisor = mentor.role_type === 'supervisor';
    const load = Math.round(Number(mentor.students_count || 0) / Math.max(Number(mentor.student_limit), 1) * 100);
    const rowActions = archiveMode
      ? `<button class="button secondary small" data-action="restore-mentor" data-mentor-id="${mentor.id}">Восстановить</button>`
      : `<div class="row-actions"><button class="button secondary small" data-action="edit-mentor" data-mentor-id="${mentor.id}">Изменить</button>${canDeleteRecords() ? `<button class="button ghost small danger" data-action="archive-mentor" data-mentor-id="${mentor.id}">В архив</button>` : ''}</div>`;
    const workload = isSupervisor
      ? '<span class="muted">Управление программой</span>'
      : `<div class="progress-line"><div class="progress-meta"><span>${mentor.students_count || 0} из ${mentor.student_limit}</span><b>${load}%</b></div><div class="bar"><span style="width:${load}%;background:${load >= 100 ? 'var(--red)' : 'var(--blue)'}"></span></div></div>`;
    return `<tr><td><div class="person"><div class="avatar avatar-navy">${initials(mentor.full_name)}</div><div><strong>${escapeHTML(mentor.full_name)}</strong><small>${archiveMode ? 'В архиве' : isSupervisor ? 'Руководитель практики' : 'Производственный наставник'}</small></div></div></td><td><strong>${escapeHTML(mentor.enterprise || 'Не указано')}</strong><br><small>${escapeHTML(mentor.city || 'Город не указан')}</small></td><td>${escapeHTML(mentor.workshop)}</td><td>${escapeHTML(mentor.qualification)}</td><td>${workload}</td><td>${escapeHTML(mentor.phone || '—')}</td><td>${rowActions}</td></tr>`;
  }).join('');
}

function mentorRegistrySection(title, subtitle, people, archiveMode = false) {
  return `<section class="card mentor-registry"><div class="card-head"><div><h2>${title}</h2><p>${subtitle}</p></div><span class="journal-count">${people.length}</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>ФИО / роль</th><th>Предприятие / город</th><th>Цех / отдел</th><th>Квалификация / должность</th><th>Нагрузка</th><th>Контакт</th><th></th></tr></thead><tbody>${mentorRegistryRows(people, archiveMode) || `<tr><td colspan="7"><div class="empty">Записей пока нет</div></td></tr>`}</tbody></table></div></section>`;
}

function renderMentors() {
  const archiveMode = state.showArchivedMentors;
  const activePeople = state.data.mentors;
  const people = archiveMode ? state.data.archived_mentors : activePeople;
  const productionMentors = activePeople.filter(person => Boolean(person.can_mentor));
  const supervisors = activePeople.filter(person => person.role_type === 'supervisor');
  const occupied = productionMentors.reduce((sum, mentor) => sum + Number(mentor.students_count || 0), 0);
  const capacity = productionMentors.reduce((sum, mentor) => sum + Number(mentor.student_limit || 0), 0);
  const actions = `<button class="button secondary" data-action="toggle-mentor-archive">${archiveMode ? '← Действующая команда' : `Архив (${state.data.archived_mentors.length})`}</button>${archiveMode ? '' : '<button class="button primary" data-action="add-mentor"><span class="plus">+</span> Добавить сотрудника</button>'}`;
  content.innerHTML = `
    ${pageHead(archiveMode ? 'Архив команды' : 'Команда практической подготовки', archiveMode ? 'Архив наставников и руководителей' : 'Наставники и руководители', archiveMode ? 'История сохраняется; любую запись можно вернуть в активный реестр.' : 'Ответственные сотрудники распределены по роли, предприятию и городу.', actions)}
    <div class="stats-grid">
      ${statCard('Наставники', productionMentors.length, 'Производственные наставники', 'Н', 'blue')}
      ${statCard('Руководители', supervisors.length, 'Координируют практику', 'Р', 'purple')}
      ${statCard('Закреплено студентов', occupied, `из ${capacity} доступных мест`, 'С', 'orange')}
      ${statCard('Предприятия', new Set(activePeople.map(person => person.enterprise).filter(Boolean)).size, 'Участвуют в программе', '▦', 'green')}
    </div>
    ${archiveMode
      ? mentorRegistrySection('Архивные записи', 'Доступно восстановление', people, true)
      : `${mentorRegistrySection('Руководители практики', 'Координация программы и взаимодействие с предприятиями', supervisors)}${mentorRegistrySection('Производственные наставники', 'Сотрудники, закрепляемые за студентами', productionMentors)}`}`;
}

function roleStudents() {
  const students = state.data.dashboard.students;
  return state.role === 'mentor' ? students.filter(student => student.mentor_id === state.mentorId) : students;
}

async function renderAttendance() {
  const records = await api(`/api/attendance?date=${state.attendanceDate}`);
  const allStudents = roleStudents();
  const streams = sortedStreams(allStudents);
  const students = state.attendanceStream ? allStudents.filter(student => student.stream === state.attendanceStream) : allStudents;
  const recordMap = new Map(records.map(record => [record.student_id, record]));
  const visibleRecords = students.map(student => recordMap.get(student.id)).filter(Boolean);
  const counts = Object.fromEntries(Object.keys(attendanceLabels).map(status => [status, visibleRecords.filter(record => record.status === status).length]));
  const exportUrl = `/api/export/attendance.xlsx${state.attendanceStream ? `?stream=${encodeURIComponent(state.attendanceStream)}` : ''}`;
  content.innerHTML = `
    ${pageHead('Ежедневный журнал', 'Посещаемость', 'Отметьте присутствие студентов за выбранную дату. Повторное сохранение обновляет существующие отметки.', `<a class="button secondary" href="${exportUrl}" download>⇩ Выгрузить Excel</a><button class="button secondary" data-action="mark-all-present">✓ Все присутствуют</button><button class="button primary" data-action="save-attendance">Сохранить журнал</button>`)}
    <div class="attendance-toolbar"><label><span class="label">Дата</span><input class="input" id="attendance-date" type="date" value="${state.attendanceDate}"></label><label><span class="label">Поток</span><select class="select" id="attendance-stream"><option value="">Все потоки</option>${streams.map(stream => `<option ${selected(stream, state.attendanceStream)}>${escapeHTML(stream)}</option>`).join('')}</select></label><div class="attendance-summary"><span class="att-summary present">${counts.present || 0} присутствуют</span><span class="att-summary late">${counts.late || 0} опоздали</span><span class="att-summary excused">${counts.excused || 0} уважит.</span><span class="att-summary absent">${counts.absent || 0} отсутствуют</span></div></div>
    <section class="card attendance-card"><div class="attendance-head"><span>Студент</span><span>Отметка за день</span><span>Часы</span><span>Комментарий</span></div><div class="attendance-list">${students.length ? students.map(student => attendanceRow(student, recordMap.get(student.id))).join('') : '<div class="empty"><strong>Студенты не найдены</strong>Измените фильтр потока.</div>'}</div></section>`;
}

function attendanceRow(student, record) {
  const status = record?.status || '';
  const buttons = [
    ['present', '✓', 'Был'], ['late', 'О', 'Опоздал'], ['excused', 'У', 'Уважительная'], ['absent', 'Н', 'Не был'],
  ];
  return `<div class="attendance-row" data-att-student="${student.id}" data-status="${status}"><div class="person"><div class="avatar" style="background:${student.avatar_color}">${initials(student.full_name)}</div><div><strong>${escapeHTML(student.full_name)}</strong><small>${escapeHTML(student.stream)} · ${escapeHTML(student.specialty)}</small></div></div><div class="attendance-statuses">${buttons.map(([value, mark, title]) => `<button type="button" data-att-status="${value}" class="${status === value ? `selected ${value}` : ''}" title="${title}"><b>${mark}</b><span>${title}</span></button>`).join('')}</div><input class="input attendance-hours" type="number" min="0" max="12" step="0.5" value="${record?.hours ?? 8}" aria-label="Количество часов"><input class="input attendance-note" value="${escapeHTML(record?.note || '')}" placeholder="При необходимости" aria-label="Комментарий"></div>`;
}

async function saveAttendance() {
  const rows = els('.attendance-row');
  const items = rows.filter(row => row.dataset.status).map(row => ({
    student_id: Number(row.dataset.attStudent),
    status: row.dataset.status,
    hours: Number(el('.attendance-hours', row).value),
    note: el('.attendance-note', row).value.trim(),
  }));
  if (items.length !== rows.length) {
    toast('Поставьте отметку каждому студенту в списке', 'error');
    return;
  }
  try {
    const result = await api('/api/attendance', { method: 'POST', body: JSON.stringify({ attendance_date: state.attendanceDate, mentor_id: state.role === 'mentor' ? state.mentorId : null, items }) });
    toast(`Журнал сохранён: ${result.saved} ${plural(result.saved, 'студент', 'студента', 'студентов')}`);
    await renderAttendance();
  } catch (error) { toast(error.message, 'error'); }
}

async function renderEvaluations() {
  const allEvaluations = await api('/api/evaluations');
  state.evaluations = allEvaluations;
  renderEvaluationWorkspace();
}

async function renderDemoExam() {
  const allEvaluations = await api('/api/evaluations');
  state.evaluations = allEvaluations;
  const students = [...roleStudents()];
  const streams = sortedStreams(students);
  students.sort((a, b) => streams.indexOf(a.stream) - streams.indexOf(b.stream) || a.full_name.localeCompare(b.full_name, 'ru'));
  if (state.demoExamStream && !streams.includes(state.demoExamStream)) state.demoExamStream = '';
  const streamStudents = students.filter(student => !state.demoExamStream || student.stream === state.demoExamStream);
  if (state.demoExamStudentId && !streamStudents.some(student => student.id === Number(state.demoExamStudentId))) state.demoExamStudentId = 0;
  const visibleStudents = streamStudents.filter(student => !state.demoExamStudentId || student.id === Number(state.demoExamStudentId));
  const examResults = allEvaluations.filter(item => item.evaluation_type === 'demo_exam');
  const latestByStudent = new Map();
  examResults.forEach(item => {
    if (!latestByStudent.has(item.student_id)) latestByStudent.set(item.student_id, item);
  });
  const evaluated = visibleStudents.map(student => latestByStudent.get(student.id)).filter(Boolean);
  const average = evaluated.length ? Math.round(evaluated.reduce((sum, item) => sum + Number(item.score), 0) / evaluated.length) : 0;
  const canEdit = state.role !== 'student';
  const pageActions = canEdit ? '<button class="button primary" data-action="add-demo-exam"><span class="plus">+</span> Добавить результат</button>' : '';
  content.innerHTML = `
    ${pageHead('Итоговая аттестация', 'Демонстрационный экзамен', 'Результаты экзамена вынесены в отдельный раздел и доступны учебному центру, наставнику и студенту.', pageActions)}
    <div class="stats-grid">
      ${statCard('Участники', visibleStudents.length, 'В выбранной группе', 'С', 'blue')}
      ${statCard('Оценено', evaluated.length, `из ${visibleStudents.length} студентов`, '✓', 'green')}
      ${statCard('Средний результат', evaluated.length ? average : '—', evaluated.length ? 'По 100-балльной шкале' : 'Результатов пока нет', 'О', 'orange')}
      ${statCard('Оценки 4 и 5', evaluated.filter(item => Number(item.grade) >= 4).length, 'Последние результаты', '5', 'purple')}
    </div>
    <section class="card demo-exam-card"><div class="card-head"><div><h2>Ведомость демонстрационного экзамена</h2><p>Для каждого студента показан последний результат</p></div><span class="journal-count">${evaluated.length} ${plural(evaluated.length, 'результат', 'результата', 'результатов')}</span></div>
      <div class="matrix-toolbar demo-exam-toolbar">
        <label><span>Поток</span><select class="filter-select" data-demo-filter="stream"><option value="">Все потоки</option>${streams.map(stream => `<option value="${escapeHTML(stream)}" ${selected(stream, state.demoExamStream)}>${escapeHTML(stream)}</option>`).join('')}</select></label>
        <label><span>Студент</span><select class="filter-select" data-demo-filter="student"><option value="0">Все студенты</option>${streamStudents.map(student => `<option value="${student.id}" ${selected(student.id, state.demoExamStudentId)}>${escapeHTML(student.full_name)}</option>`).join('')}</select></label>
      </div>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Студент</th><th>Поток</th><th>Экзамен / дата</th><th>Результат</th><th>Оценка</th><th>Оценил</th>${canEdit ? '<th></th>' : ''}</tr></thead><tbody>${visibleStudents.length ? visibleStudents.map(student => {
        const result = latestByStudent.get(student.id);
        return `<tr><td>${personCell(student)}</td><td><span class="stream-label">${escapeHTML(student.stream)}</span></td><td>${result ? `<strong>${escapeHTML(result.section_title)}</strong><br><small>${formatDate(result.evaluated_at, true)}</small>` : '<span class="muted">Не проводился</span>'}</td><td>${result ? `<strong class="matrix-score">${result.score}/100</strong>` : '<span class="muted">Не оценён</span>'}</td><td>${result ? `<span class="grade-display"><span class="grade grade-${result.grade}">${result.grade}</span><small>${gradeLabels[result.grade]}</small></span>` : '—'}</td><td>${result ? escapeHTML(result.evaluator_name || 'Учебный центр') : '—'}</td>${canEdit ? `<td>${result ? evaluationActions(result) : `<button class="button secondary small" data-action="add-demo-exam" data-student-id="${student.id}">Добавить</button>`}</td>` : ''}</tr>`;
      }).join('') : `<tr><td colspan="${canEdit ? 7 : 6}"><div class="empty"><strong>Студенты не найдены</strong>Измените выбранные фильтры.</div></td></tr>`}</tbody></table></div>
    </section>`;
}

function evaluationEventKey(item) {
  return [item.course_id || '', item.evaluated_at, item.evaluation_type, String(item.section_title || '').trim().toLocaleLowerCase('ru')].join('|');
}

function scoreGrade(score) {
  return score >= 90 ? 5 : score >= 70 ? 4 : score >= 50 ? 3 : 2;
}

function evaluationMonthLabel(value) {
  if (!value) return '';
  return new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' }).format(new Date(`${value}-01T00:00:00`));
}

function journalDateMarkup(value) {
  if (!value) return '<div class="journal-date"><b>—</b></div>';
  const date = new Date(`${value}T00:00:00`);
  const day = new Intl.DateTimeFormat('ru-RU', { day: '2-digit' }).format(date);
  const monthYear = new Intl.DateTimeFormat('ru-RU', { month: 'short', year: 'numeric' }).format(date).replace(/\s*г\.$/, '');
  return `<div class="journal-date"><b>${escapeHTML(day)}</b><span>${escapeHTML(monthYear)}</span></div>`;
}

function evaluationCourseOptions(evaluations) {
  const courses = [...state.data.courses].sort((a, b) => a.title.localeCompare(b.title, 'ru'));
  const hasUnassigned = evaluations.some(item => !item.course_id);
  return `<option value="">Все курсы и модули</option>${hasUnassigned ? `<option value="unassigned" ${selected('unassigned', state.evaluationCourse)}>Без привязки к курсу</option>` : ''}${courses.map(course => `<option value="${course.id}" ${selected(course.id, state.evaluationCourse)}>${escapeHTML(course.title)}</option>`).join('')}`;
}

function evaluationFilters(evaluations, students) {
  const streams = sortedStreams(students);
  const months = [...new Set(evaluations.map(item => item.evaluated_at?.slice(0, 7)).filter(Boolean))].sort().reverse();
  return `<div class="journal-toolbar">
    <div class="journal-filters">
      <label><span>Поток</span><select class="filter-select" data-evaluation-filter="stream"><option value="">Все потоки</option>${streams.map(stream => `<option value="${escapeHTML(stream)}" ${selected(stream, state.evaluationStream)}>${escapeHTML(stream)}</option>`).join('')}</select></label>
      <label><span>Учебный курс</span><select class="filter-select" data-evaluation-filter="course">${evaluationCourseOptions(evaluations)}</select></label>
      <label><span>Месяц</span><select class="filter-select" data-evaluation-filter="month"><option value="">Все месяцы</option>${months.map(month => `<option value="${month}" ${selected(month, state.evaluationMonth)}>${escapeHTML(evaluationMonthLabel(month))}</option>`).join('')}</select></label>
      <label><span>Вид контроля</span><select class="filter-select" data-evaluation-filter="type"><option value="">Все виды</option>${Object.entries(evaluationLabels).map(([value, label]) => `<option value="${value}" ${selected(value, state.evaluationType)}>${escapeHTML(label)}</option>`).join('')}</select></label>
    </div>
    <div class="journal-view-switch" aria-label="Формат отображения"><button type="button" class="${state.evaluationView === 'journal' ? 'active' : ''}" data-evaluation-view="journal">Электронный журнал</button><button type="button" class="${state.evaluationView === 'list' ? 'active' : ''}" data-evaluation-view="list">Список записей</button></div>
  </div>`;
}

function filteredEvaluationData(evaluations, students) {
  const streamOrder = sortedStreams(students);
  const visibleStudents = students.filter(student => !state.evaluationStream || student.stream === state.evaluationStream).sort((a, b) => {
    const streamCompare = streamOrder.indexOf(a.stream) - streamOrder.indexOf(b.stream);
    return streamCompare || a.full_name.localeCompare(b.full_name, 'ru');
  });
  const visibleIds = new Set(visibleStudents.map(student => student.id));
  const visibleEvaluations = evaluations.filter(item => visibleIds.has(item.student_id)
    && (!state.evaluationCourse || (state.evaluationCourse === 'unassigned' ? !item.course_id : String(item.course_id) === String(state.evaluationCourse)))
    && (!state.evaluationMonth || item.evaluated_at?.startsWith(state.evaluationMonth))
    && (!state.evaluationType || item.evaluation_type === state.evaluationType));
  return { visibleStudents, visibleEvaluations };
}

function journalCourseSummary() {
  if (!state.evaluationCourse || state.evaluationCourse === 'unassigned') return '';
  const course = state.data.courses.find(item => String(item.id) === String(state.evaluationCourse));
  if (!course) return '';
  return `<div class="journal-course-summary"><div><span>Выбранный курс / модуль</span><strong>${escapeHTML(course.title)}</strong><small>${escapeHTML(course.category)} · ${course.duration_hours} ч.</small></div><div><span>Проходной результат</span><strong>${course.pass_score}%</strong><small>${escapeHTML(course.description || 'Описание не заполнено')}</small></div></div>`;
}

function renderElectronicJournal(evaluations, students) {
  const columnsMap = new Map();
  evaluations.forEach(item => {
    const key = evaluationEventKey(item);
    if (!columnsMap.has(key)) columnsMap.set(key, { ...item, key });
  });
  const columns = [...columnsMap.values()].sort((a, b) => a.evaluated_at.localeCompare(b.evaluated_at) || a.section_title.localeCompare(b.section_title, 'ru'));
  state.journalColumns = columns;
  const recordMap = new Map();
  evaluations.forEach(item => {
    const key = `${item.student_id}:${evaluationEventKey(item)}`;
    if (!recordMap.has(key)) recordMap.set(key, item);
  });
  if (!columns.length) {
    return `${journalCourseSummary()}<div class="journal-empty"><strong>Для выбранных фильтров оценок пока нет</strong><span>Добавьте первую оценку — работа появится отдельным столбцом, после чего можно заполнять результаты остальных студентов.</span><button class="button primary" data-action="add-evaluation"><span class="plus">+</span> Добавить первую оценку</button></div>`;
  }
  const bodyRows = students.map((student, studentIndex) => {
    const studentRecords = [];
    const cells = columns.map((column, columnIndex) => {
      const record = recordMap.get(`${student.id}:${column.key}`);
      if (record) studentRecords.push(record);
      return record
        ? `<td class="journal-score-cell"><button type="button" class="journal-score grade-${record.grade}" data-action="edit-evaluation" data-evaluation-id="${record.id}" title="Изменить результат">${record.score}</button></td>`
        : `<td class="journal-score-cell"><button type="button" class="journal-score empty-score" data-action="add-journal-score" data-student-id="${student.id}" data-column-index="${columnIndex}" title="Поставить оценку">+</button></td>`;
    }).join('');
    const average = studentRecords.length ? Math.round(studentRecords.reduce((sum, item) => sum + item.score, 0) / studentRecords.length) : null;
    const grade = average === null ? null : scoreGrade(average);
    return `<tr><td class="journal-number">${studentIndex + 1}</td><td class="journal-student">${personCell(student)}<small>${escapeHTML(student.stream)} · ${escapeHTML(student.specialty)}</small></td>${cells}<td class="journal-result">${average === null ? '<span>—</span>' : `<strong>${average}</strong><small class="grade-text grade-${grade}">${gradeLabels[grade]}</small>`}</td></tr>`;
  }).join('');
  return `${journalCourseSummary()}<div class="electronic-journal-wrap"><table class="electronic-journal"><thead><tr><th class="journal-number">№</th><th class="journal-student">ФИО студента</th>${columns.map(column => `<th class="journal-work">${journalDateMarkup(column.evaluated_at)}<strong title="${escapeHTML(column.section_title)}">${escapeHTML(column.section_title)}</strong><small>${escapeHTML(evaluationLabels[column.evaluation_type] || column.evaluation_type)}${column.course_title ? ` · ${escapeHTML(column.course_title)}` : ''}</small></th>`).join('')}<th class="journal-result">Средний<br>результат</th></tr></thead><tbody>${bodyRows}</tbody></table></div><div class="journal-legend"><span><i class="legend-dot excellent"></i>90–100 Отлично</span><span><i class="legend-dot good"></i>70–89 Хорошо</span><span><i class="legend-dot satisfactory"></i>50–69 Удовлетворительно</span><span><i class="legend-dot poor"></i>0–49 Неудовлетворительно</span><small>Нажмите на балл для изменения или на «+» для добавления.</small></div>`;
}

function renderEvaluationList(evaluations) {
  return `<div class="table-wrap"><table class="data-table"><thead><tr><th>Студент</th><th>Курс / модуль</th><th>Вид контроля</th><th>Работа / раздел / этап</th><th>Дата</th><th>Балл</th><th>Оценка</th><th>Наставник</th><th></th></tr></thead><tbody>${evaluations.length ? evaluations.map(evaluationRow).join('') : '<tr><td colspan="9"><div class="empty"><strong>Оценок пока нет</strong>Добавьте первый результат.</div></td></tr>'}</tbody></table></div>`;
}

function renderEvaluationWorkspace() {
  const students = roleStudents();
  const allowedIds = new Set(students.map(student => student.id));
  const evaluations = state.evaluations.filter(item => allowedIds.has(item.student_id));
  const average = evaluations.length ? Math.round(evaluations.reduce((sum, item) => sum + item.score, 0) / evaluations.length) : 0;
  const { visibleStudents, visibleEvaluations } = filteredEvaluationData(evaluations, students);
  const exportParams = new URLSearchParams();
  if (state.evaluationStream) exportParams.set('stream', state.evaluationStream);
  if (state.evaluationCourse) exportParams.set('course', state.evaluationCourse);
  if (state.evaluationMonth) exportParams.set('month', state.evaluationMonth);
  if (state.evaluationType) exportParams.set('type', state.evaluationType);
  const exportQuery = exportParams.size ? `?${exportParams}` : '';
  content.innerHTML = `
    ${pageHead('Контроль результатов', 'Электронный журнал успеваемости', 'Студенты расположены по строкам, а даты и контрольные работы — по столбцам.', `<a class="button secondary" href="/api/export/evaluations.xlsx${exportQuery}" download>⇩ Выгрузить Excel</a><button class="button primary" data-action="add-evaluation"><span class="plus">+</span> Добавить оценку</button>`)}
    <div class="stats-grid">
      ${statCard('Всего оценок', evaluations.length, 'Сохранено в журнале', 'О', 'orange')}
      ${statCard('Средний балл', average, 'По 100-балльной шкале', '↗', 'green')}
      ${statCard('Практические работы', evaluations.filter(item => item.evaluation_type === 'practical').length, 'ЛПЗ', 'Л', 'blue')}
      ${statCard('Итоговых', evaluations.filter(item => ['rotation', 'practice', 'demo_exam'].includes(item.evaluation_type)).length, 'Ротации, практика и демоэкзамен', 'И', 'purple')}
    </div>
    <section class="card journal-card"><div class="card-head"><div><h2>Электронный журнал</h2><p>Студенты по строкам, контрольные работы по столбцам</p></div><span class="journal-count">${visibleStudents.length} ${plural(visibleStudents.length, 'студент', 'студента', 'студентов')} · ${visibleEvaluations.length} ${plural(visibleEvaluations.length, 'оценка', 'оценки', 'оценок')}</span></div>${evaluationFilters(evaluations, students)}<div class="journal-content">${state.evaluationView === 'journal' ? renderElectronicJournal(visibleEvaluations, visibleStudents) : renderEvaluationList(visibleEvaluations)}</div></section>`;
}

function evaluationActions(item) {
  return `<div class="row-actions evaluation-actions"><button class="button secondary small" data-action="edit-evaluation" data-evaluation-id="${item.id}">Изменить</button>${canDeleteRecords() ? `<button class="button ghost small danger" data-action="delete-evaluation" data-evaluation-id="${item.id}">Удалить</button>` : ''}</div>`;
}

function evaluationRow(item) {
  const student = state.data.dashboard.students.find(student => student.id === item.student_id) || item;
  return `<tr><td>${personCell(student)}</td><td>${item.course_title ? `<strong>${escapeHTML(item.course_title)}</strong>` : '<span class="muted">Без привязки</span>'}</td><td><span class="evaluation-type ${item.evaluation_type}">${evaluationLabels[item.evaluation_type] || escapeHTML(item.evaluation_type)}</span></td><td><strong>${escapeHTML(item.section_title)}</strong>${item.comment ? `<br><small>${escapeHTML(item.comment)}</small>` : ''}</td><td>${formatDate(item.evaluated_at, true)}</td><td><strong>${item.score}</strong>/100</td><td><span class="grade-display"><span class="grade grade-${item.grade}">${item.grade}</span><small>${gradeLabels[item.grade]}</small></span></td><td>${escapeHTML(item.evaluator_name || 'Учебный центр')}</td><td>${evaluationActions(item)}</td></tr>`;
}

function quizAttemptRows(attempts) {
  return attempts.map(attempt => {
    const answerResult = attempt.correct_answers == null || attempt.total_questions == null
      ? '—'
      : `${attempt.correct_answers} из ${attempt.total_questions}`;
    const legacyNote = attempt.is_legacy
      ? '<br><small>Результат зафиксирован до включения истории попыток</small>'
      : '';
    return `<tr><td><strong>${escapeHTML(attempt.course_title)}</strong>${legacyNote}</td><td>№ ${attempt.attempt_number}</td><td>${formatDateTime(attempt.attempted_at)}</td><td>${answerResult}</td><td><strong>${attempt.score}%</strong></td><td><span class="account-state ${attempt.passed ? 'active' : 'inactive'}">${attempt.passed ? 'Пройден' : 'Нужна пересдача'}</span><br><small>Порог ${attempt.pass_score}%</small></td></tr>`;
  }).join('');
}

function skillLevelLabel(score) {
  return ({
    1: 'Требуется обучение',
    2: 'С постоянной помощью',
    3: 'С периодической помощью',
    4: 'Самостоятельно',
    5: 'Уверенно / может объяснить',
  })[Number(score)] || 'Ещё не оценён';
}

function skillProgressRows(progress) {
  return progress.map(item => `<tr><td><span class="skill-code">${escapeHTML(item.code)}</span></td><td><strong>${escapeHTML(item.title)}</strong><br><small>${escapeHTML(item.module)}</small></td><td><span class="type-pill ${item.category === 'Soft skill' ? 'soft' : 'practice'}">${escapeHTML(item.category)}</span></td><td>${item.score ? `<strong class="matrix-score grade-${Math.round(Number(item.score))}">${item.score}/5</strong><br><small>${skillLevelLabel(item.score)}</small>` : '<span class="muted">Не оценён</span>'}</td><td><span class="status ${statusClass(item.status)}">${progressLabel(item.status)}</span></td><td>${item.score ? formatDateTime(item.updated_at) : '—'}</td></tr>`).join('');
}

function skillBatchRows(batches) {
  return batches.map(batch => `<tr><td>${formatDateTime(batch.assessed_at)}</td><td><strong>${escapeHTML(batch.mentor_name)}</strong><br><small>${escapeHTML(batch.enterprise || 'Предприятие не указано')}</small></td><td><strong>${Number(batch.average_score).toFixed(2)}/5</strong><br><small>${batch.skills_count} ${plural(batch.skills_count, 'навык', 'навыка', 'навыков')}</small></td><td><strong>Успехи:</strong> ${escapeHTML(batch.best || '—')}<br><strong>Улучшить:</strong> ${escapeHTML(batch.improve || '—')}<br><strong>Рекомендации:</strong> ${escapeHTML(batch.recommendation || '—')}</td><td><span class="account-state active">Telegram-бот</span></td></tr>`).join('');
}

async function renderStudentProfile() {
  const profile = await api(`/api/student-profile?student_id=${state.profileStudentId}`);
  state.evaluations = profile.evaluations;
  const student = profile.student;
  const records = profile.attendance;
  const attended = records.filter(record => ['present', 'late'].includes(record.status)).length;
  const excused = records.filter(record => record.status === 'excused').length;
  const attendanceRate = records.length ? Math.round(attended / Math.max(records.length - excused, 1) * 100) : 0;
  const average = profile.evaluations.length ? Math.round(profile.evaluations.reduce((sum, item) => sum + item.score, 0) / profile.evaluations.length) : 0;
  const pct = progressPct(student);
  const quizAttempts = profile.quiz_attempts || [];
  const skillProgress = [...(profile.progress || [])].sort((a, b) => {
    const typeOrder = (a.category === 'Hard skill' ? 0 : 1) - (b.category === 'Hard skill' ? 0 : 1);
    return typeOrder || Number(a.display_order || 0) - Number(b.display_order || 0);
  });
  const filteredSkillProgress = state.profileSkillType === 'all'
    ? skillProgress
    : skillProgress.filter(item => item.category === state.profileSkillType);
  const skillBatches = profile.skill_assessment_batches || [];
  const currentRotation = profile.rotations.find(rotation => rotation.status === 'Активна')
    || profile.rotations.filter(rotation => rotation.status === 'Запланирована').sort((a, b) => a.start_date.localeCompare(b.start_date))[0]
    || profile.rotations[0];
  const backPage = state.role === 'mentor' ? 'mentor_students' : 'students';
  const profileActions = `<button class="button secondary" data-page="${backPage}">← К списку</button>${state.role === 'admin' ? `<button class="button secondary" data-action="edit-profile-student" data-student-id="${student.id}">Изменить</button>` : ''}<button class="button primary" data-action="evaluate-profile-student" data-student-id="${student.id}">Добавить оценку</button>`;
  content.innerHTML = `
    ${pageHead('Личное дело', 'Карточка студента', 'Полная информация, результаты тестов, посещаемость, оценки и история производственного обучения.', profileActions)}
    <section class="profile-hero"><div class="profile-identity"><div class="avatar profile-avatar" style="background:${student.avatar_color}">${initials(student.full_name)}</div><div><span class="status ${statusClass(student.status)}">${escapeHTML(student.status)}</span><h2>${escapeHTML(student.full_name)}</h2><p>${escapeHTML(student.specialty)}</p></div></div><div class="profile-facts"><div><span>Телефон</span><strong>${escapeHTML(student.phone || 'Не указан')}</strong></div><div><span>Дата рождения</span><strong>${student.birth_date ? formatDate(student.birth_date, true) : 'Не указана'}</strong></div><div><span>Поток и курс</span><strong>${escapeHTML(student.stream)} · ${student.course} курс</strong></div><div><span>Адрес проживания</span><strong>${escapeHTML(student.address || 'Не указан')}</strong></div><div><span>Учебное заведение</span><strong>${escapeHTML(student.institution)}</strong></div><div><span>Наставник</span><strong>${escapeHTML(student.mentor_name || 'Не назначен')}</strong></div><div><span>Предприятие ротации</span><strong>${escapeHTML(currentRotation?.company || 'Не назначено')}</strong></div><div><span>Город ротации</span><strong>${escapeHTML(currentRotation?.city || 'Не назначен')}</strong></div><div><span>Период практики</span><strong>${currentRotation ? `${formatDate(currentRotation.start_date, true)} — ${formatDate(currentRotation.end_date, true)}` : 'Не назначен'}</strong></div></div></section>
    <div class="stats-grid profile-stats">
      ${statCard('Посещаемость', `${attendanceRate}%`, `${attended} из ${records.length} учебных дней`, 'П', 'green')}
      ${statCard('Средний результат', average || '—', `${profile.evaluations.length} ${plural(profile.evaluations.length, 'оценка', 'оценки', 'оценок')}`, 'О', 'orange')}
      ${statCard('Допуск ТБ', `<span class="safety-admission ${student.safety_passed ? 'passed' : 'denied'}">${student.safety_passed ? 'Допущен' : 'Не допущен'}</span>`, student.safety_passed ? 'Практика разрешена' : 'Требуется оформление допуска', 'Т', student.safety_passed ? 'green' : 'orange')}
      ${statCard('Компетенции', `${pct}%`, `${student.skills_confirmed} из ${student.skills_total} подтверждено`, '✓', 'purple')}
    </div>
    <section class="card"><div class="card-head"><div><h2>Результаты тестов по курсам</h2><p>Отдельный контроль: эти результаты не входят в электронный журнал и средний балл</p></div><span class="journal-count">${quizAttempts.length} ${plural(quizAttempts.length, 'попытка', 'попытки', 'попыток')}</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Курс</th><th>Попытка</th><th>Дата и время</th><th>Верных ответов</th><th>Результат</th><th>Статус</th></tr></thead><tbody>${quizAttempts.length ? quizAttemptRows(quizAttempts) : '<tr><td colspan="6"><div class="empty">Студент ещё не проходил тесты по курсам</div></td></tr>'}</tbody></table></div></section>
    <section class="card"><div class="card-head"><div><h2>Текущий профиль компетенций</h2><p>Hard и soft skills: последняя подтверждённая оценка наставника</p></div><div class="card-head-tools"><select class="select filter-select" id="profile-skill-type"><option value="all" ${selected('all', state.profileSkillType)}>Все компетенции</option><option value="Hard skill" ${selected('Hard skill', state.profileSkillType)}>Hard skills</option><option value="Soft skill" ${selected('Soft skill', state.profileSkillType)}>Soft skills</option></select><span class="journal-count">${filteredSkillProgress.filter(item => item.score).length} из ${filteredSkillProgress.length} оценено</span></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Код</th><th>Компетенция</th><th>Тип</th><th>Уровень</th><th>Статус</th><th>Обновлено</th></tr></thead><tbody>${filteredSkillProgress.length ? skillProgressRows(filteredSkillProgress) : '<tr><td colspan="6"><div class="empty">Компетенции выбранного типа не найдены</div></td></tr>'}</tbody></table></div></section>
    <section class="card"><div class="card-head"><div><h2>История анкет наставников</h2><p>Результаты из Telegram-бота не входят в электронный журнал</p></div><span class="journal-count">${skillBatches.length} ${plural(skillBatches.length, 'анкета', 'анкеты', 'анкет')}</span></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Дата и время</th><th>Наставник / предприятие</th><th>Средний уровень</th><th>Комментарии наставника</th><th>Источник</th></tr></thead><tbody>${skillBatches.length ? skillBatchRows(skillBatches) : '<tr><td colspan="5"><div class="empty">Анкеты наставников из чат-бота ещё не поступали</div></td></tr>'}</tbody></table></div></section>
    <div class="student-profile-grid"><div class="stack gap-20"><section class="card"><div class="card-head"><div><h2>История оценивания</h2><p>ЛПЗ, разделы, ротации, практика и демоэкзамен</p></div><button class="text-link" data-action="evaluate-profile-student" data-student-id="${student.id}">Добавить →</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Вид</th><th>Работа / этап</th><th>Дата</th><th>Результат</th><th></th></tr></thead><tbody>${profile.evaluations.length ? profile.evaluations.map(item => `<tr><td><span class="evaluation-type ${item.evaluation_type}">${evaluationLabels[item.evaluation_type] || escapeHTML(item.evaluation_type)}</span></td><td><strong>${escapeHTML(item.section_title)}</strong>${item.comment ? `<br><small>${escapeHTML(item.comment)}</small>` : ''}</td><td>${formatDate(item.evaluated_at, true)}</td><td><strong>${item.score}/100</strong> <span class="grade-display"><span class="grade grade-${item.grade}">${item.grade}</span><small>${gradeLabels[item.grade]}</small></span></td><td>${evaluationActions(item)}</td></tr>`).join('') : '<tr><td colspan="5"><div class="empty">Оценок пока нет</div></td></tr>'}</tbody></table></div></section><section class="card"><div class="card-head"><div><h2>Последние отметки посещаемости</h2><p>До 90 последних учебных дней</p></div></div><div class="attendance-history">${records.length ? records.slice(0, 12).map(record => `<div><span>${formatDate(record.attendance_date, true)}</span><strong class="attendance-text ${record.status}">${attendanceLabels[record.status]}</strong><small>${record.hours} ч${record.note ? ` · ${escapeHTML(record.note)}` : ''}</small></div>`).join('') : '<div class="empty">Отметок пока нет</div>'}</div></section></div><aside class="stack gap-20"><section class="card"><div class="card-head"><div><h2>Ротации</h2><p>История перемещений</p></div></div><div class="card-body"><div class="timeline">${profile.rotations.length ? profile.rotations.map(timelineItem).join('') : '<div class="empty">Ротации не назначены</div>'}</div></div></section><section class="card"><div class="card-head"><div><h2>Дополнительная информация</h2><p>Примечания к личному делу</p></div></div><div class="card-body profile-note">${student.additional_info ? escapeHTML(student.additional_info) : '<span>Дополнительные сведения пока не заполнены.</span>'}</div></section></aside></div>`;
}

function renderRotations() {
  const rotations = state.data.dashboard.rotations;
  const columns = [
    ['Активна', 'Сейчас на площадке'], ['Запланирована', 'Следующие ротации'], ['Завершена', 'Завершённые'],
  ];
  content.innerHTML = `
    ${pageHead('Практическое обучение', 'Ротации', 'Планируйте перемещения: статусы и текущая площадка обновляются автоматически по датам.', `<button class="button primary" data-action="add-rotation"><span class="plus">+</span> Новая ротация</button>`)}
    <div class="rotation-board">${columns.map(([status, title]) => {
      const list = rotations.filter(r => r.status === status);
      return `<section class="rotation-column"><div class="rotation-column-head"><h3>${title}</h3><span>${list.length}</span></div>${list.map(rotationCard).join('') || `<div class="empty">Записей нет</div>`}</section>`;
    }).join('')}</div>`;
}

function rotationCard(rotation) {
  const student = state.data.dashboard.students.find(s => s.id === rotation.student_id);
  return `<article class="rotation-card"><div class="rotation-card-head">${personCell(student)}<button class="button secondary small" data-action="edit-rotation" data-rotation-id="${rotation.id}">Изменить</button></div><div class="rotation-card-details"><div><span>Предприятие</span><strong>${escapeHTML(rotation.company)}</strong></div><div><span>Город ротации</span><strong>${escapeHTML(rotation.city)}</strong></div><div><span>Цех</span><strong>${escapeHTML(rotation.workshop)}</strong></div><div><span>Период</span><strong>${formatDate(rotation.start_date, true)} — ${formatDate(rotation.end_date, true)}</strong></div></div></article>`;
}

function matrixPeriod(row) {
  if (!Number(row.score) && row.status === 'not_started') return '—';
  if (row.period_start && row.period_end) return `${formatDate(row.period_start, true)} — ${formatDate(row.period_end, true)}`;
  return row.assessed_at ? formatDate(String(row.assessed_at).slice(0, 10), true) : '—';
}

async function renderMatrix() {
  if (!state.matrixRows.length) state.matrixRows = await api('/api/skill-matrix');
  const students = [...roleStudents()];
  const streams = sortedStreams(students);
  students.sort((a, b) => streams.indexOf(a.stream) - streams.indexOf(b.stream) || a.full_name.localeCompare(b.full_name, 'ru'));
  if (state.matrixStream && !streams.includes(state.matrixStream)) state.matrixStream = '';
  const streamStudents = students.filter(student => !state.matrixStream || student.stream === state.matrixStream);
  if (!streamStudents.some(student => student.id === Number(state.matrixStudentId))) state.matrixStudentId = Number(streamStudents[0]?.id || 0);
  const selectedStudent = streamStudents.find(student => student.id === Number(state.matrixStudentId));
  const rows = state.matrixRows.filter(row => row.student_id === Number(state.matrixStudentId)
    && (state.matrixSkillType === 'all' || row.category === state.matrixSkillType));
  const assessed = rows.filter(row => Number(row.score) > 0);
  const average = assessed.length ? (assessed.reduce((sum, row) => sum + Number(row.score), 0) / assessed.length).toFixed(2) : '—';
  content.innerHTML = `
    ${pageHead('Развитие компетенций', 'Матрица навыков', 'Индивидуальная таблица компетенций с оценкой, периодом освоения и наставником.')}
    <div class="matrix-toolbar">
      <label><span>Поток</span><select class="filter-select" data-matrix-filter="stream"><option value="">Все потоки</option>${streams.map(stream => `<option value="${escapeHTML(stream)}" ${selected(stream, state.matrixStream)}>${escapeHTML(stream)}</option>`).join('')}</select></label>
      <label><span>Студент</span><select class="filter-select" data-matrix-filter="student">${streamStudents.map(student => `<option value="${student.id}" ${selected(student.id, state.matrixStudentId)}>${escapeHTML(student.full_name)}</option>`).join('')}</select></label>
      <label><span>Тип компетенции</span><select class="filter-select" data-matrix-filter="type"><option value="all" ${selected('all', state.matrixSkillType)}>Все навыки</option><option value="Hard skill" ${selected('Hard skill', state.matrixSkillType)}>Hard skills</option><option value="Soft skill" ${selected('Soft skill', state.matrixSkillType)}>Soft skills</option></select></label>
    </div>
    <div class="stats-grid matrix-summary">
      ${statCard('Студент', selectedStudent ? escapeHTML(selectedStudent.full_name) : '—', selectedStudent ? escapeHTML(selectedStudent.stream) : 'Выберите студента', 'С', 'blue')}
      ${statCard('Оценено', assessed.length, `из ${rows.length} компетенций`, '✓', 'green')}
      ${statCard('Средняя оценка', average, assessed.length ? 'По пятибалльной шкале' : 'Оценок пока нет', 'О', 'orange')}
      ${statCard('Тип', state.matrixSkillType === 'all' ? 'Все' : state.matrixSkillType === 'Hard skill' ? 'Hard' : 'Soft', `${rows.length} ${plural(rows.length, 'компетенция', 'компетенции', 'компетенций')}`, 'H/S', 'purple')}
    </div>
    <section class="card matrix-table-card"><div class="card-head"><div><h2>${selectedStudent ? escapeHTML(selectedStudent.full_name) : 'Компетенции'}</h2><p>Последняя подтверждённая оценка по каждой компетенции</p></div></div><div class="table-wrap"><table class="data-table matrix-table"><thead><tr><th>Компетенция</th><th>Оценка</th><th>Период</th><th>Наставник</th></tr></thead><tbody>${rows.length ? rows.map(row => `<tr><td><span class="skill-code">${escapeHTML(row.code)}</span> <span class="type-pill ${row.category === 'Soft skill' ? 'soft' : 'practice'}">${escapeHTML(row.category)}</span><br><strong>${escapeHTML(row.title)}</strong><br><small>${escapeHTML(row.module)}</small></td><td>${row.score ? `<strong class="matrix-score grade-${Math.round(Number(row.score))}">${row.score}/5</strong><br><small>${skillLevelLabel(row.score)}</small>` : `<span class="status ${statusClass(row.status)}">${progressLabel(row.status)}</span><br><small>Оценка не выставлена</small>`}</td><td><strong>${matrixPeriod(row)}</strong>${row.assessed_at && (row.score || row.status !== 'not_started') ? `<br><small>Обновлено ${formatDateTime(row.assessed_at)}</small>` : ''}</td><td>${row.mentor_name ? `<strong>${escapeHTML(row.mentor_name)}</strong><br><small>${escapeHTML(row.enterprise || 'Предприятие не указано')}</small>` : '<span class="muted">Не назначен</span>'}</td></tr>`).join('') : '<tr><td colspan="4"><div class="empty"><strong>Компетенции не найдены</strong>Измените фильтр потока, студента или типа навыка.</div></td></tr>'}</tbody></table></div></section>`;
}

async function renderCourses() {
  const isStudent = state.role === 'student';
  const student = state.data.dashboard.students.find(s => s.id === state.studentId);
  const archiveMode = !isStudent && state.showArchivedCourses;
  const courses = isStudent
    ? await api(`/api/courses?student_id=${state.studentId}`)
    : archiveMode ? state.data.archived_courses : state.data.courses;
  const completed = courses.filter(course => isStudent
    ? course.status === 'completed'
    : Number(course.assigned_count) > 0 && Number(course.completed_count) === Number(course.assigned_count)).length;
  const adminActions = `<button class="button secondary" data-action="toggle-course-archive">${archiveMode ? '← Действующие курсы' : `Удалённые (${state.data.archived_courses.length})`}</button>${archiveMode ? '' : '<button class="button primary" data-action="add-course"><span class="plus">+</span> Добавить курс / модуль</button>'}`;
  content.innerHTML = `
    ${pageHead(isStudent ? 'Личный кабинет' : archiveMode ? 'Архив программы' : 'Программа обучения', isStudent ? 'Мои курсы' : archiveMode ? 'Удалённые курсы' : 'Учебные курсы', isStudent ? `Обязательные и профессиональные модули · ${escapeHTML(student.full_name)}` : archiveMode ? 'Удалённые модули скрыты у студентов, но их результаты и вопросы сохранены.' : 'Добавляйте модули, меняйте часы, описание и проходной балл.', isStudent ? studentSwitcher() : adminActions)}
    <div class="course-summary"><div><strong>${courses.length}</strong><span>${plural(courses.length, 'курс назначен', 'курса назначено', 'курсов назначено')}</span></div><div><strong>${completed}</strong><span>${isStudent ? 'завершено' : 'освоено всей группой'}</span></div><div><strong>${courses.reduce((sum, course) => sum + Number(course.duration_hours), 0)} ч</strong><span>общая длительность</span></div></div>
    <div class="courses-grid">${courses.length ? courses.map(course => {
      const pct = Number(course.percent || 0);
      const status = isStudent ? course.status : (Number(course.assigned_count) > 0 && Number(course.completed_count) === Number(course.assigned_count) ? 'completed' : 'in_progress');
      const action = isStudent
        ? course.questions_count
          ? `<button class="button ${course.id === 2 ? 'primary' : 'secondary'} small" data-action="take-quiz" data-course-id="${course.id}">${status === 'completed' ? 'Пройти повторно' : 'Пройти тест'}</button>`
          : '<span class="course-meta">Материалы назначены</span>'
        : `<span class="course-meta">${course.completed_count || 0} из ${course.assigned_count || state.data.dashboard.students.length} завершили</span>`;
      const controls = isStudent ? '' : archiveMode
        ? `<div class="course-actions"><button class="button secondary small" data-action="restore-course" data-course-id="${course.id}">Восстановить</button></div>`
        : `<div class="course-actions"><button class="button secondary small quiz-manage-button" data-action="manage-quiz" data-course-id="${course.id}">Тест: ${course.questions_count || 0}</button><button class="button secondary small" data-action="edit-course" data-course-id="${course.id}">Изменить</button>${canDeleteRecords() ? `<button class="button ghost small danger" data-action="archive-course" data-course-id="${course.id}">Удалить</button>` : ''}</div>`;
      const label = status === 'completed' ? 'Завершён' : progressLabel(status);
      return `<article class="course-card ${archiveMode ? 'archived' : ''}" style="--course-color:${course.color}"><div class="course-cover"><span class="course-category">${escapeHTML(course.category)}</span><span class="course-hours">${course.duration_hours} ч</span><div class="course-mark">${String(course.id).padStart(2, '0')}</div></div><div class="course-body"><h3>${escapeHTML(course.title)}</h3><p>${escapeHTML(course.description)}</p><div class="course-progress"><div class="progress-meta"><span>${isStudent ? label : 'Средний прогресс группы'}</span><b>${pct}%</b></div><div class="bar"><span style="width:${pct}%;background:${course.color}"></span></div></div><div class="course-footer"><span>Порог теста: ${course.pass_score}%</span>${action}</div>${controls}</div></article>`;
    }).join('') : `<div class="empty empty-card"><strong>${archiveMode ? 'Удалённых курсов нет' : 'Курсы ещё не добавлены'}</strong>${archiveMode ? 'Удалённые модули появятся здесь.' : 'Добавьте первый учебный курс или модуль.'}</div>`}</div>`;
}

function mentorOptions() {
  return state.data.mentors.filter(m => Boolean(m.can_mentor) || m.id === state.mentorId).map(m => `<option value="${m.id}" ${m.id === state.mentorId ? 'selected' : ''}>${escapeHTML(m.full_name)}</option>`).join('');
}

function assignedStudents() {
  return state.data.dashboard.students.filter(s => s.mentor_id === state.mentorId);
}

async function renderChecklist() {
  const mentor = state.data.mentors.find(m => m.id === state.mentorId) || state.data.mentors.find(m => Boolean(m.can_mentor));
  if (!mentor) {
    content.innerHTML = `${pageHead('Кабинет наставника', 'Чек-лист компетенций', 'Сначала добавьте наставника и закрепите за ним студентов.')}<div class="empty empty-card"><strong>Наставники ещё не добавлены</strong>Переключитесь в режим «Учебный центр», откройте раздел «Наставники» и создайте первую запись.</div>`;
    return;
  }
  const students = assignedStudents();
  if (!students.length) {
    content.innerHTML = `${pageHead('Кабинет наставника', 'Чек-лист компетенций', 'За выбранным наставником пока не закреплены студенты.')}<div class="mentor-toolbar"><label><span class="label">Наставник</span><select class="select" data-select="mentor">${mentorOptions()}</select></label></div><div class="empty empty-card"><strong>Нет закреплённых студентов</strong>Назначьте наставника в карточке студента.</div>`;
    return;
  }
  if (!students.some(s => s.id === state.studentId)) state.studentId = students[0]?.id || state.data.dashboard.students[0]?.id;
  const student = state.data.dashboard.students.find(s => s.id === state.studentId);
  const progress = await api(`/api/progress?student_id=${state.studentId}`);
  state.draftProgress = Object.fromEntries(progress.map(p => [p.skill_id, p.status]));
  const grouped = Object.groupBy ? Object.groupBy(progress, p => p.module) : progress.reduce((acc, item) => ((acc[item.module] ||= []).push(item), acc), {});
  const confirmed = progress.filter(p => p.status === 'confirmed').length;
  const currentRotation = state.data.dashboard.rotations.find(r => r.student_id === student.id && r.status === 'Активна');
  content.innerHTML = `
    ${pageHead('Кабинет наставника', 'Чек-лист компетенций', 'Отметьте состояние навыков студента по итогам сегодняшней практики.')}
    <div class="mentor-toolbar"><label><span class="label">Наставник</span><select class="select" data-select="mentor">${mentorOptions()}</select></label><label><span class="label">Студент</span><select class="select" data-select="checklist-student">${students.map(s => `<option value="${s.id}" ${s.id === state.studentId ? 'selected' : ''}>${escapeHTML(s.full_name)}</option>`).join('')}</select></label><button class="button secondary" data-action="reset-checklist">Сбросить изменения</button></div>
    <div class="mentor-summary"><div class="profile-panel"><div class="avatar" style="background:${student.avatar_color}">${initials(student.full_name)}</div><div><strong>${escapeHTML(student.full_name)}</strong><span>${escapeHTML(student.specialty)} · ${escapeHTML(student.stream)}</span></div></div><div class="mini-stat"><span>Подтверждено</span><strong>${confirmed}/${progress.length}</strong></div><div class="mini-stat"><span>Допуск ТБ</span><strong>${student.safety_passed ? 'Допущен' : 'Не допущен'}</strong></div><div class="mini-stat"><span>Площадка</span><strong>${escapeHTML(currentRotation?.company || '—')}</strong></div></div>
    <section class="card checklist">
      ${Object.entries(grouped).map(([module, items]) => `<div class="checklist-group"><div class="checklist-group-title"><h3>${escapeHTML(module)}</h3><span>${items.length} ${plural(items.length, 'навык', 'навыка', 'навыков')}</span></div>${items.map(checkItem).join('')}</div>`).join('')}
      <div class="checklist-footer"><button class="button secondary" data-page="mentor_students">К списку</button><button class="button success" data-action="save-progress">Сохранить результаты</button></div>
    </section>`;
}

function checkItem(item) {
  const buttons = [
    ['not_started', '—', 'Не начат'], ['in_progress', '◐', 'В процессе'], ['confirmed', '✓', 'Подтверждён'],
  ];
  const score = item.score ? ` · Последняя оценка ${item.score}/5` : '';
  return `<div class="check-item"><div class="check-copy"><span class="skill-code">${escapeHTML(item.code)}</span><div><strong>${escapeHTML(item.title)}</strong><small>${escapeHTML(item.description)}${score}</small></div></div><div class="segmented" role="group" aria-label="Статус навыка">${buttons.map(([status, mark, title]) => `<button type="button" title="${title}" data-skill="${item.skill_id}" data-status="${status}" class="${item.status === status ? 'selected' : ''}">${mark}</button>`).join('')}</div></div>`;
}

async function renderStudentView(skillsOnly = false) {
  const student = state.data.dashboard.students.find(s => s.id === state.studentId) || state.data.dashboard.students[0];
  const progress = await api(`/api/progress?student_id=${student.id}`);
  const rotations = state.data.dashboard.rotations.filter(r => r.student_id === student.id);
  const confirmed = progress.filter(p => p.status === 'confirmed').length;
  const pct = Math.round(confirmed / Math.max(progress.length, 1) * 100);
  const grouped = progress.reduce((acc, item) => ((acc[item.module] ||= []).push(item), acc), {});
  if (skillsOnly) {
    content.innerHTML = `
      ${pageHead('Личный кабинет', 'Мои навыки', 'Ваша матрица компетенций и статусы, подтверждённые наставником.', studentSwitcher())}
      <div class="stats-grid">${statCard('Подтверждено', confirmed, `из ${progress.length} компетенций`, '✓', 'green')}${statCard('В процессе', progress.filter(p => p.status === 'in_progress').length, 'Навыки текущей ротации', '◐', 'orange')}${statCard('Hard skills', progress.filter(p => p.category === 'Hard skill' && p.status === 'confirmed').length, 'Подтверждено навыков', 'H', 'blue')}${statCard('Soft skills', progress.filter(p => p.category === 'Soft skill' && p.status === 'confirmed').length, 'Подтверждено навыков', 'S', 'purple')}</div>
      <section class="card">${Object.entries(grouped).map(([module, items]) => `<div class="checklist-group"><div class="checklist-group-title"><h3>${escapeHTML(module)}</h3><span>${items.filter(i => i.status === 'confirmed').length} из ${items.length}</span></div>${items.map(item => `<div class="check-item"><div class="check-copy"><span class="skill-code">${escapeHTML(item.code)}</span><div><strong>${escapeHTML(item.title)}</strong><small>${escapeHTML(item.description)}${item.score ? ` · Оценка ${item.score}/5` : ''}</small></div></div><span class="status ${statusClass(item.status)}">${progressLabel(item.status)}</span></div>`).join('')}</div>`).join('')}</section>`;
    return;
  }
  content.innerHTML = `
    ${studentSwitcher(true)}
    <section class="student-hero"><div class="student-hero-copy"><div class="eyebrow">Личная траектория</div><h1>${escapeHTML(student.full_name)}</h1><p>${escapeHTML(student.institution)} · ${escapeHTML(student.specialty)}</p><div class="hero-tags"><span class="hero-tag">${escapeHTML(student.stream)}</span><span class="hero-tag">${student.course} курс</span><span class="hero-tag">Наставник: ${escapeHTML(student.mentor_name || 'не назначен')}</span></div></div><div class="hero-progress"><span>Общий прогресс</span><strong>${pct}%</strong><div class="bar"><span style="width:${pct}%"></span></div><small>${confirmed} из ${progress.length} компетенций подтверждено</small></div></section>
    <div class="student-layout"><section class="card"><div class="card-head"><div><h2>Маршрут практики</h2><p>Текущая и запланированные производственные ротации</p></div></div><div class="card-body"><div class="timeline">${rotations.length ? rotations.map(rotation => timelineItem(rotation)).join('') : `<div class="empty">Ротации пока не назначены</div>`}</div></div></section><aside class="stack gap-20"><section class="card"><div class="card-head"><div><h2>Допуск к практике</h2><p>Техника безопасности</p></div></div><div class="card-body"><div class="safety-score ${student.safety_passed ? '' : 'not-passed'}"><div class="safety-score-icon">${student.safety_passed ? '✓' : '!'}</div><div><strong>${student.safety_passed ? 'Допущен' : 'Не допущен'}</strong><span>${student.safety_passed ? 'Практическая подготовка разрешена' : 'Обратитесь в учебный центр для оформления допуска'}</span></div></div></div></section><section class="card"><div class="card-head"><div><h2>Прогресс по модулям</h2><p>Подтверждено наставником</p></div><button class="text-link" data-page="student_skills">Все →</button></div><div class="card-body">${Object.entries(grouped).slice(0,4).map(([module, items]) => { const done=items.filter(i=>i.status==='confirmed').length; const p=Math.round(done/items.length*100); return `<div class="skill-mini"><div class="skill-mini-top"><strong>${escapeHTML(module)}</strong><span>${done}/${items.length}</span></div><div class="bar"><span style="width:${p}%"></span></div></div>`; }).join('')}</div></section></aside></div>`;
}

function studentSwitcher(inline = false) {
  return `<label ${inline ? 'style="display:flex;justify-content:flex-end;margin-bottom:14px"' : ''}><select class="select filter-select" data-select="student-view">${state.data.dashboard.students.map(s => `<option value="${s.id}" ${s.id === state.studentId ? 'selected' : ''}>${escapeHTML(s.full_name)}</option>`).join('')}</select></label>`;
}

function timelineItem(rotation) {
  const className = rotation.status === 'Активна' ? 'current' : rotation.status === 'Завершена' ? 'done' : '';
  return `<div class="timeline-item ${className}"><div class="timeline-dot">${rotation.status === 'Завершена' ? '✓' : ''}</div><div class="timeline-copy"><span class="date">${formatDate(rotation.start_date, true)} — ${formatDate(rotation.end_date, true)}</span><h3>${escapeHTML(rotation.company)} · ${escapeHTML(rotation.city)}</h3><p>${escapeHTML(rotation.workshop)} · ${escapeHTML(rotation.status)}</p></div></div>`;
}

function renderReports() {
  const students = [...state.data.dashboard.students].sort((a,b) => progressPct(b)-progressPct(a));
  const avg = state.data.dashboard.stats.avg_progress;
  content.innerHTML = `
    ${pageHead('Аналитика программы', 'Прогресс обучения', 'Сводная динамика освоения компетенций и готовности студентов к производственным задачам.')}
    <div class="report-grid"><section class="card chart-card"><div class="card-head"><div><h2>Освоение компетенций</h2><p>Процент подтверждённых навыков по студентам</p></div></div><div class="card-body"><div class="bars-chart-scroll"><div class="bars-chart">${students.map(student => { const p=progressPct(student); return `<div class="chart-bar-group"><span class="chart-value">${p}%</span><div class="chart-bar" style="height:${Math.max(p,3)}%"></div><span class="chart-label" title="${escapeHTML(student.full_name)}">${escapeHTML(student.full_name.split(' ')[0])}</span></div>`; }).join('')}</div></div></div></section><section class="card"><div class="card-head"><div><h2>Средний результат</h2><p>Вся учебная группа</p></div></div><div class="card-body"><div class="donut-wrap"><div class="donut" style="--value:${avg}"><div class="donut-label"><strong>${avg}%</strong><span>освоено</span></div></div></div></div></section></div>
    <section class="card" style="margin-top:20px"><div class="card-head"><div><h2>Рейтинг готовности</h2><p>Для планирования следующих производственных задач</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Студент</th><th>Статус</th><th>Наставник</th><th>ТБ</th><th>Компетенции</th></tr></thead><tbody>${students.map(s => `<tr><td>${personCell(s)}</td><td><span class="status ${statusClass(s.status)}">${escapeHTML(s.status)}</span></td><td>${escapeHTML(s.mentor_name || '—')}</td><td><span class="account-state ${s.safety_passed ? 'active' : 'inactive'}">${s.safety_passed ? 'Допущен' : 'Не допущен'}</span></td><td><div class="progress-line"><div class="progress-meta"><span>${s.skills_confirmed}/${s.skills_total}</span><b>${progressPct(s)}%</b></div><div class="bar"><span style="width:${progressPct(s)}%"></span></div></div></td></tr>`).join('')}</tbody></table></div></section>`;
}

async function renderAccounts() {
  state.accounts = await api('/api/users');
  const roleLabels = { admin: 'Администратор', mentor: 'Наставник', student: 'Студент' };
  content.innerHTML = `
    ${pageHead('Безопасность', 'Учётные записи', 'Телефон используется как логин. При сбросе создаётся новый временный пароль.', '<a class="button secondary" href="/api/export/accounts.xlsx" download>⇩ Выгрузить Excel</a>')}
    <section class="card"><div class="card-head"><div><h2>Пользователи системы</h2><p>${state.accounts.length} учётных записей</p></div></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Пользователь</th><th>Роль</th><th>Телефон</th><th>Состояние</th><th>Последний вход</th><th></th></tr></thead><tbody>${state.accounts.map(account => `<tr><td><strong>${escapeHTML(account.full_name)}</strong></td><td><span class="account-role">${escapeHTML(account.account_title || roleLabels[account.role] || account.role)}</span></td><td>${escapeHTML(account.phone)}</td><td><span class="account-state ${account.is_active ? 'active' : 'inactive'}">${account.is_active ? (account.must_change_password ? 'Ожидает смены пароля' : 'Активна') : 'Отключена'}</span></td><td>${account.last_login_at ? formatDateTime(account.last_login_at) : 'Ещё не входил'}</td><td>${account.id === state.session.id && account.role === 'admin' ? '<button class="button secondary small" data-action="change-admin-phone">Изменить телефон</button>' : account.id === state.session.id ? '<small>Текущая запись</small>' : `<button class="button secondary small" data-action="reset-password" data-user-id="${account.id}">Сбросить пароль</button>`}</td></tr>`).join('')}</tbody></table></div></section>`;
}

function openHelp() {
  const roleLabel = state.session?.account_title ? 'руководителя' : { admin: 'администратора', mentor: 'наставника', student: 'студента' }[state.role];
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Справочный центр';
  el('#modal-title').textContent = 'Как работать в Learning Hub';
  form.dataset.type = 'help';
  form.innerHTML = `<div class="help-intro"><span class="support-icon">?</span><div><strong>Инструкция для ${roleLabel}</strong><p>Доступные разделы уже ограничены вашей ролью. Все изменения сохраняются в базе сразу после подтверждения.</p></div></div><div class="help-grid">
    <section class="help-section"><h3>Начало работы</h3><ol><li>Войдите по телефону из карточки пользователя.</li><li>При первом входе замените временный пароль.</li><li>Для завершения работы нажмите значок выхода справа вверху.</li></ol></section>
    <section class="help-section"><h3>Студенты и потоки</h3><ul><li>Потоки расположены по порядку: Поток 1, Поток 2, Поток 3.</li><li>Карточка студента содержит контакты, обучение, посещаемость, оценки и ротации.</li><li>Телефон в карточке одновременно является логином.</li></ul></section>
    <section class="help-section"><h3>Ежедневная работа</h3><ul><li>«Посещаемость» — отметки за выбранную дату и выгрузка Excel.</li><li>«Оценивание» — ЛПЗ, раздел, ротация, практика и демоэкзамен.</li><li>«Ротации» — планирование предприятия, города, цеха и периода.</li><li>«Матрица навыков» — hard и soft skills; оценки анкет наставника автоматически поступают из Telegram-бота.</li></ul></section>
    <section class="help-section"><h3>Курсы и тесты</h3><ul><li>Администратор добавляет модули, меняет часы и проходной балл.</li><li>Кнопка «Тест» открывает редактор вопросов курса.</li><li>Студент видит назначенные курсы и проходит доступные тесты.</li></ul></section>
    <section class="help-section"><h3>Пароль и доступ</h3><p>Администратор может открыть «Учётные записи», изменить собственный телефон-логин и сбросить пароль другому пользователю. Новый временный пароль показывается один раз. Если телефон студента или наставника изменён в карточке, его логин обновляется автоматически.</p></section>
    <section class="help-section"><h3>Если возникла ошибка</h3><p>Обновите страницу и повторите действие. Если проблема сохраняется, запишите раздел, ФИО пользователя и текст ошибки и передайте администратору учебного центра.</p></section>
  </div><div class="modal-actions"><button class="button primary" type="button" data-close-modal>Понятно</button></div>`;
  el('#modal').classList.add('wide', 'open');
  el('#modal-backdrop').classList.add('open');
}

function openChangePasswordModal() {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Безопасность';
  el('#modal-title').textContent = 'Изменить пароль';
  form.dataset.type = 'change-password';
  form.innerHTML = `<div class="form-grid"><div class="field full"><label>Текущий пароль *</label><input class="input" type="password" name="current_password" autocomplete="current-password" required></div><div class="field"><label>Новый пароль *</label><input class="input" type="password" name="new_password" minlength="8" autocomplete="new-password" required></div><div class="field"><label>Повторите пароль *</label><input class="input" type="password" name="confirm_password" minlength="8" autocomplete="new-password" required></div><div class="field full"><small class="field-hint">Не менее 8 символов, обязательно буквы и цифры.</small></div></div>${modalActions('Изменить пароль')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

function openChangeAdminPhoneModal() {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Учётная запись администратора';
  el('#modal-title').textContent = 'Изменить номер телефона';
  form.dataset.type = 'change-admin-phone';
  form.innerHTML = `<div class="form-grid"><div class="field full"><label>Новый номер телефона *</label><input class="input" type="tel" name="new_phone" autocomplete="tel" placeholder="+7 700 000 00 00" value="${escapeHTML(state.session.phone || '')}" required></div><div class="field full"><label>Текущий пароль *</label><input class="input" type="password" name="current_password" autocomplete="current-password" required></div><div class="field full"><div class="alert-card warning"><strong>Новый логин</strong><p>После сохранения используйте новый номер телефона для следующих входов. Пароль останется прежним.</p></div></div></div>${modalActions('Сохранить номер')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

function showTemporaryPassword(account, password) {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Пароль сброшен';
  el('#modal-title').textContent = account.full_name;
  form.dataset.type = 'temporary-password';
  form.innerHTML = `<div class="alert-card success"><strong>Новый временный пароль</strong><p>Передайте его пользователю безопасным способом. После первого входа система потребует заменить пароль.</p></div><div class="field" style="margin-top:16px"><label>Временный пароль</label><input class="input" value="${escapeHTML(password)}" readonly data-temporary-password></div><div class="modal-actions"><button class="button secondary" type="button" data-action="copy-password">Копировать</button><button class="button primary" type="button" data-close-modal>Готово</button></div>`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

async function renderPage() {
  renderChrome();
  if (state.page === 'dashboard') renderDashboard();
  else if (state.page === 'students') renderStudents(false);
  else if (state.page === 'attendance') await renderAttendance();
  else if (state.page === 'evaluations') await renderEvaluations();
  else if (state.page === 'demo_exam') await renderDemoExam();
  else if (state.page === 'student_profile') await renderStudentProfile();
  else if (state.page === 'mentors') renderMentors();
  else if (state.page === 'mentor_students') renderStudents(true);
  else if (state.page === 'rotations') renderRotations();
  else if (state.page === 'courses') await renderCourses();
  else if (state.page === 'matrix') await renderMatrix();
  else if (state.page === 'reports') renderReports();
  else if (state.page === 'accounts') await renderAccounts();
  else if (state.page === 'checklist') await renderChecklist();
  else if (state.page === 'trajectory') await renderStudentView(false);
  else if (state.page === 'student_skills') await renderStudentView(true);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderNotifications() {
  const list = state.data.dashboard.notifications;
  el('#notification-list').innerHTML = list.length ? list.map(n => `<article class="notification-item ${n.kind}" data-notification="${n.id}"><strong>${escapeHTML(n.title)}</strong><p>${escapeHTML(n.message)}</p><time>${formatDateTime(n.created_at)}</time></article>`).join('') : `<div class="empty"><strong>Новых событий нет</strong>Здесь появятся допуски и напоминания о ротациях.</div>`;
}

function openDrawer() {
  el('#notification-drawer').classList.add('open');
  el('#drawer-backdrop').classList.add('open');
}

function closeDrawer() {
  el('#notification-drawer').classList.remove('open');
  el('#drawer-backdrop').classList.remove('open');
}

function selected(value, current) {
  return String(value ?? '') === String(current ?? '') ? 'selected' : '';
}

function mentorSelectOptions(currentId = '', excludeId = null) {
  return `<option value="">Не назначен</option>${state.data.mentors.filter(mentor => mentor.id !== excludeId && (Boolean(mentor.can_mentor) || String(mentor.id) === String(currentId))).map(mentor => `<option value="${mentor.id}" ${selected(mentor.id, currentId)}>${escapeHTML(mentor.full_name)} · ${mentor.students_count}/${mentor.student_limit}</option>`).join('')}`;
}

function evaluationEvaluatorOptions(currentId = '') {
  const current = state.data.mentors.find(mentor => String(mentor.id) === String(currentId));
  const evaluators = state.data.mentors.filter(mentor => {
    const name = String(mentor.full_name || '').toLocaleLowerCase('ru');
    return name.includes('орленко') || name.includes('уткин');
  });
  if (current && !evaluators.some(mentor => mentor.id === current.id)) evaluators.push(current);
  const supervisors = state.data.mentors.filter(mentor => mentor.role_type === 'supervisor');
  const available = evaluators.length ? evaluators : (supervisors.length ? supervisors : state.data.mentors);
  return `<option value="">Выберите руководителя</option>${available.map(mentor => `<option value="${mentor.id}" ${selected(mentor.id, currentId)}>${escapeHTML(mentor.full_name)}</option>`).join('')}`;
}

function companyDatalist(id = 'company-options') {
  const companies = new Set(['CT Assembly', 'CT Agro', 'ТОО Reimann']);
  state.data.dashboard.rotations.forEach(rotation => companies.add(rotation.company));
  return `<datalist id="${id}">${[...companies].map(company => `<option value="${escapeHTML(company)}"></option>`).join('')}</datalist>`;
}

function rotationStatusForDates(startDate, endDate) {
  if (!startDate || !endDate) return 'Укажите даты начала и окончания.';
  if (endDate < startDate) return 'Дата окончания не может быть раньше даты начала.';
  const today = state.data?.dashboard?.as_of_date || new Date().toISOString().slice(0, 10);
  if (today < startDate) return `Запланирована — станет активной ${formatDate(startDate, true)}.`;
  if (today > endDate) return `Завершена — период закончился ${formatDate(endDate, true)}.`;
  return `Активна — текущая площадка до ${formatDate(endDate, true)}.`;
}

function updateRotationStatusPreview(form) {
  const preview = el('[data-rotation-status-preview]', form);
  if (!preview) return;
  preview.textContent = rotationStatusForDates(
    el('[name="start_date"]', form)?.value,
    el('[name="end_date"]', form)?.value,
  );
}

function evaluationRotationOptions(studentId, currentId = '') {
  const rotations = state.data.dashboard.rotations.filter(rotation => rotation.student_id === Number(studentId));
  return `<option value="">Без привязки к ротации</option>${rotations.map(rotation => `<option value="${rotation.id}" ${selected(rotation.id, currentId)}>${escapeHTML(rotation.company)} · ${escapeHTML(rotation.workshop)} · ${formatDate(rotation.start_date, true)}</option>`).join('')}`;
}

function evaluationStudentOptions(stream, currentId = '') {
  return roleStudents().filter(student => student.stream === stream).map(student => `<option value="${student.id}" ${selected(student.id, currentId)}>${escapeHTML(student.full_name)}</option>`).join('');
}

function evaluationCourseSelectOptions(currentId = '') {
  const courses = [...state.data.courses].sort((a, b) => a.title.localeCompare(b.title, 'ru'));
  return `<option value="">Без привязки к курсу</option>${courses.map(course => `<option value="${course.id}" ${selected(course.id, currentId)}>${escapeHTML(course.title)} · ${course.duration_hours} ч.</option>`).join('')}`;
}

function openEvaluationModal(studentId = null, record = null, preset = {}) {
  const students = roleStudents();
  const source = record || preset;
  const recordStudentId = Number(source?.student_id || studentId || students[0]?.id || 0);
  const recordStudent = students.find(student => student.id === recordStudentId);
  const streams = sortedStreams(students);
  const selectedStream = recordStudent?.stream || streams[0] || '';
  const streamStudents = students.filter(student => student.stream === selectedStream);
  const selectedStudentId = streamStudents.some(student => student.id === recordStudentId) ? recordStudentId : Number(streamStudents[0]?.id || 0);
  if (!selectedStudentId) {
    toast('Сначала добавьте или закрепите студента', 'error');
    return;
  }
  const form = el('#modal-form');
  const isEdit = Boolean(record);
  el('#modal-eyebrow').textContent = isEdit ? 'Запись журнала' : 'Новый результат';
  el('#modal-title').textContent = isEdit ? 'Редактировать оценку' : 'Добавить оценку';
  form.dataset.type = 'evaluation';
  form.dataset.recordId = record?.id || '';
  const today = new Date().toISOString().slice(0, 10);
  const evaluatorField = state.role === 'mentor'
    ? `<input type="hidden" name="evaluator_id" value="${state.mentorId}">`
    : `<div class="field"><label>Кто оценил *</label><select class="select" name="evaluator_id" required>${evaluationEvaluatorOptions(source?.evaluator_id)}</select><small class="field-hint">Орленко или Уткин</small></div>`;
  form.innerHTML = `<div class="form-grid"><div class="field"><label>Поток *</label><select class="select" data-select="evaluation-stream" required>${streams.map(stream => `<option value="${escapeHTML(stream)}" ${selected(stream, selectedStream)}>${escapeHTML(stream)}</option>`).join('')}</select></div><div class="field"><label>Студент *</label><select class="select" name="student_id" data-select="evaluation-student" required>${evaluationStudentOptions(selectedStream, selectedStudentId)}</select></div><div class="field full"><label>Учебный курс / модуль</label><select class="select" name="course_id">${evaluationCourseSelectOptions(source?.course_id)}</select><small class="field-hint">Связь с курсом позволяет фильтровать журнал и видеть результаты конкретного модуля.</small></div><div class="field"><label>Вид контроля *</label><select class="select" name="evaluation_type" required><option value="section" ${selected('section', source?.evaluation_type)}>Итоги раздела</option><option value="practical" ${selected('practical', source?.evaluation_type)}>Практическая работа (ЛПЗ)</option><option value="rotation" ${selected('rotation', source?.evaluation_type)}>Итоги ротации</option><option value="practice" ${selected('practice', source?.evaluation_type)}>Итоги практики</option><option value="demo_exam" ${selected('demo_exam', source?.evaluation_type)}>Демоэкзамен</option></select></div><div class="field"><label>Дата *</label><input class="input" type="date" name="evaluated_at" required value="${source?.evaluated_at || today}"></div><div class="field full"><label>Наименование работы / раздела / этапа *</label><input class="input" name="section_title" required placeholder="Например, ЛПЗ №2 — Сборка узлов" value="${escapeHTML(source?.section_title || '')}"></div><div class="field"><label>Балл из 100 *</label><input class="input" type="number" name="score" min="0" max="100" required value="${source?.score ?? 80}"><small class="field-hint">90–100 → 5 (Отлично) · 70–89 → 4 (Хорошо) · 50–69 → 3 (Удовлетворительно) · 0–49 → 2 (Неудовлетворительно)</small></div>${evaluatorField}<div class="field full"><label>Связанная ротация</label><select class="select" name="rotation_id" data-select="evaluation-rotation">${evaluationRotationOptions(selectedStudentId, source?.rotation_id)}</select></div><div class="field full"><label>Комментарий</label><textarea class="textarea" name="comment" placeholder="Сильные стороны, замечания и рекомендации">${escapeHTML(source?.comment || '')}</textarea></div></div>${modalActions(isEdit ? 'Сохранить изменения' : 'Сохранить оценку')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
  setTimeout(() => el('[name="section_title"]', form)?.focus(), 100);
}

function openDeleteEvaluation(record) {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Удаление записи';
  el('#modal-title').textContent = 'Удалить оценку?';
  form.dataset.type = 'delete-evaluation';
  form.dataset.recordId = record.id;
  form.innerHTML = `<div class="confirm-panel"><div class="confirm-mark">!</div><div><strong>${escapeHTML(record.student_name)} · ${record.score}/100</strong><p>${escapeHTML(evaluationLabels[record.evaluation_type] || record.evaluation_type)}: ${escapeHTML(record.section_title)}. После подтверждения запись будет удалена из журнала и карточки студента.</p></div></div>${modalActions('Удалить оценку')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

function openModal(type, record = null) {
  const form = el('#modal-form');
  const title = el('#modal-title');
  const eyebrow = el('#modal-eyebrow');
  el('#modal').classList.remove('wide');
  eyebrow.textContent = 'Новая запись';
  form.dataset.type = type;
  form.dataset.recordId = record?.id || '';
  if (type === 'student') {
    const isEdit = Boolean(record);
    eyebrow.textContent = isEdit ? 'Карточка студента' : 'Новая запись';
    title.textContent = isEdit ? 'Изменить данные студента' : 'Добавить студента';
    const rotationFields = isEdit && record.rotation_id
      ? `<input type="hidden" name="rotation_id" value="${record.rotation_id}"><div class="field full form-section"><strong>Текущая / ближайшая ротация</strong><small>Измените место прохождения практики.</small></div><div class="field"><label>Город ротации *</label><input class="input" name="rotation_city" required value="${escapeHTML(record.rotation_city || '')}"></div><div class="field"><label>Предприятие ротации *</label><input class="input" name="rotation_company" list="student-company-options" required value="${escapeHTML(record.rotation_company || '')}">${companyDatalist('student-company-options')}</div>`
      : (isEdit ? `<div class="field full"><small class="field-hint">У студента пока нет ротации. Создайте её в разделе «Ротации».</small></div>` : '');
    form.innerHTML = `<div class="form-grid"><div class="field full"><label>ФИО *</label><input class="input" name="full_name" required placeholder="Фамилия Имя Отчество" value="${escapeHTML(record?.full_name || '')}"></div><div class="field full"><label>Колледж / ВУЗ *</label><input class="input" name="institution" required value="${escapeHTML(record?.institution || 'Не указано')}"></div><div class="field"><label>Телефон</label><input class="input" name="phone" placeholder="+7 700 000 00 00" value="${escapeHTML(record?.phone || '')}"></div><div class="field"><label>Дата рождения</label><input class="input" type="date" name="birth_date" value="${escapeHTML(record?.birth_date || '')}"></div><div class="field full"><label>Адрес проживания</label><input class="input" name="address" placeholder="Район, населённый пункт, улица, дом" value="${escapeHTML(record?.address || '')}"></div><div class="field"><label>Специальность *</label><input class="input" name="specialty" required placeholder="Например, сварочное дело" value="${escapeHTML(record?.specialty || '')}"></div><div class="field"><label>Курс *</label><select class="select" name="course"><option ${selected(1, record?.course)}>1</option><option ${selected(2, record?.course)}>2</option><option ${selected(3, record?.course || 3)}>3</option><option ${selected(4, record?.course)}>4</option></select></div><div class="field"><label>Поток *</label><select class="select" name="stream"><option ${selected('Поток 1', record?.stream)}>Поток 1</option><option ${selected('Поток 2', record?.stream)}>Поток 2</option><option ${selected('Поток 3', record?.stream)}>Поток 3</option></select></div><div class="field"><label>Статус</label><select class="select" name="status"><option ${selected('Ожидает допуска', record?.status || 'Ожидает допуска')}>Ожидает допуска</option><option ${selected('Ожидает начала практики', record?.status)}>Ожидает начала практики</option><option ${selected('На практике', record?.status)}>На практике</option><option ${selected('Завершил ротацию', record?.status)}>Завершил ротацию</option></select></div><div class="field"><label>Наставник</label><select class="select" name="mentor_id">${mentorSelectOptions(record?.mentor_id)}</select></div>${rotationFields}<div class="field full"><label>Дополнительная информация</label><textarea class="textarea" name="additional_info" placeholder="Особенности обучения, допуски, важные примечания">${escapeHTML(record?.additional_info || '')}</textarea></div></div>${modalActions(isEdit ? 'Сохранить изменения' : 'Добавить студента')}`;
  } else if (type === 'mentor') {
    const isEdit = Boolean(record);
    eyebrow.textContent = isEdit ? 'Карточка сотрудника' : 'Новая запись';
    title.textContent = isEdit ? 'Изменить данные сотрудника' : 'Добавить наставника или руководителя';
    form.innerHTML = `<div class="form-grid"><div class="field full"><label>ФИО *</label><input class="input" name="full_name" required placeholder="Фамилия Имя Отчество" value="${escapeHTML(record?.full_name || '')}"></div><div class="field"><label>Основная роль *</label><select class="select" name="role_type" required><option value="mentor" ${selected('mentor', record?.role_type || 'mentor')}>Производственный наставник</option><option value="supervisor" ${selected('supervisor', record?.role_type)}>Руководитель практики</option></select></div><div class="field"><label>Ведение студентов *</label><select class="select" name="can_mentor" required><option value="1" ${selected(1, record ? Number(record.can_mentor) : 1)}>Может быть наставником</option><option value="0" ${selected(0, record ? Number(record.can_mentor) : 1)}>Только руководитель</option></select></div><div class="field"><label>Телефон</label><input class="input" name="phone" placeholder="+7 700 000 00 00" value="${escapeHTML(record?.phone || '')}"></div><div class="field"><label>Предприятие *</label><input class="input" name="enterprise" list="mentor-company-options" required placeholder="Например, CT Assembly" value="${escapeHTML(record?.enterprise || '')}">${companyDatalist('mentor-company-options')}</div><div class="field"><label>Город *</label><input class="input" name="city" required placeholder="Например, Костанай" value="${escapeHTML(record?.city || '')}"></div><div class="field"><label>Цех / отдел *</label><input class="input" name="workshop" required placeholder="Например, цех сборки" value="${escapeHTML(record?.workshop || '')}"></div><div class="field"><label>Квалификация / должность *</label><input class="input" name="qualification" required placeholder="Например, мастер участка" value="${escapeHTML(record?.qualification || '')}"></div><div class="field"><label>Лимит студентов *</label><input class="input" type="number" name="student_limit" min="1" max="50" required value="${record?.student_limit || 3}"><small class="field-hint">У двойной роли лимит применяется только к закреплённым студентам.</small></div></div>${modalActions(isEdit ? 'Сохранить изменения' : 'Добавить сотрудника')}`;
  } else if (type === 'course') {
    const isEdit = Boolean(record);
    eyebrow.textContent = isEdit ? 'Учебная программа' : 'Новый модуль';
    title.textContent = isEdit ? 'Изменить курс / модуль' : 'Добавить курс / модуль';
    form.innerHTML = `<div class="form-grid"><div class="field full"><label>Название *</label><input class="input" name="title" required placeholder="Например, Устройство сельхозтехники" value="${escapeHTML(record?.title || '')}"></div><div class="field"><label>Категория *</label><input class="input" name="category" required placeholder="Теория, ЛПЗ, обязательный" value="${escapeHTML(record?.category || '')}"></div><div class="field"><label>Количество часов *</label><input class="input" type="number" name="duration_hours" min="1" max="2000" required value="${record?.duration_hours || 1}"></div><div class="field"><label>Проходной балл, % *</label><input class="input" type="number" name="pass_score" min="0" max="100" required value="${record?.pass_score ?? 70}"></div><div class="field"><label>Цвет карточки *</label><input class="input color-input" type="color" name="color" required value="${escapeHTML(record?.color || '#D71920')}"></div><div class="field full"><label>Описание *</label><textarea class="textarea" name="description" required placeholder="Кратко опишите содержание и результат обучения">${escapeHTML(record?.description || '')}</textarea></div><div class="field full"><div class="alert-card success"><strong>${isEdit ? 'Изменения применятся сразу' : 'Назначение студентам'}</strong><p>${isEdit ? 'Новые часы, описание и проходной балл отобразятся в карточке курса.' : 'После сохранения модуль автоматически появится у всех активных студентов.'}</p></div></div></div>${modalActions(isEdit ? 'Сохранить изменения' : 'Добавить курс')}`;
  } else if (type === 'rotation') {
    const isEdit = Boolean(record);
    eyebrow.textContent = isEdit ? 'Карточка ротации' : 'Новая запись';
    title.textContent = isEdit ? 'Изменить ротацию' : 'Запланировать ротацию';
    const today = state.data.dashboard.as_of_date || new Date().toISOString().slice(0,10);
    form.innerHTML = `<div class="form-grid"><div class="field full"><label>Студент *</label><select class="select" name="student_id" required>${state.data.dashboard.students.map(s => `<option value="${s.id}" ${selected(s.id, record?.student_id)}>${escapeHTML(s.full_name)}</option>`).join('')}</select></div><div class="field"><label>Город ротации *</label><input class="input" name="city" required placeholder="Например, Костанай" value="${escapeHTML(record?.city || '')}"></div><div class="field"><label>Предприятие *</label><input class="input" name="company" list="rotation-company-options" required placeholder="Введите или выберите предприятие" value="${escapeHTML(record?.company || '')}">${companyDatalist('rotation-company-options')}</div><div class="field full"><label>Цех / отдел *</label><input class="input" name="workshop" required placeholder="Например, сварочный цех" value="${escapeHTML(record?.workshop || '')}"></div><div class="field"><label>Дата начала *</label><input class="input" name="start_date" data-rotation-date type="date" required value="${record?.start_date || today}"></div><div class="field"><label>Дата окончания *</label><input class="input" name="end_date" data-rotation-date type="date" required value="${record?.end_date || ''}"></div><div class="field full"><div class="alert-card rotation"><strong>Автоматический статус</strong><p data-rotation-status-preview>${rotationStatusForDates(record?.start_date || today, record?.end_date || '')}</p></div></div></div>${modalActions(isEdit ? 'Сохранить изменения' : 'Запланировать ротацию')}`;
  } else if (type === 'safety') {
    eyebrow.textContent = 'Техника безопасности';
    title.textContent = 'Оформить допуск к практике';
    form.innerHTML = `<div class="form-grid"><div class="field full"><label>Студент *</label><select class="select" name="student_id" required>${state.data.dashboard.students.map(s => `<option value="${s.id}">${escapeHTML(s.full_name)}</option>`).join('')}</select></div><div class="field full"><label>Решение по технике безопасности *</label><select class="select" name="passed" required><option value="1">Допущен</option><option value="0">Не допущен</option></select></div><div class="field full"><div class="alert-card success"><strong>Статус без процентов</strong><p>После сохранения в карточке студента будет показано только решение «Допущен» или «Не допущен».</p></div></div></div>${modalActions('Сохранить решение')}`;
  }
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
  setTimeout(() => el('input,select', form)?.focus(), 100);
}

function openArchiveStudent(student) {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Безопасное удаление';
  el('#modal-title').textContent = 'Переместить студента в архив?';
  form.dataset.type = 'archive-student';
  form.dataset.recordId = student.id;
  form.innerHTML = `<div class="confirm-panel"><div class="confirm-mark">!</div><div><strong>${escapeHTML(student.full_name)}</strong><p>Студент исчезнет из активных списков, но оценки, ротации и история обучения сохранятся. Запись можно восстановить.</p></div></div>${modalActions('Переместить в архив')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

function openArchiveMentor(mentor) {
  const form = el('#modal-form');
  const assigned = Number(mentor.students_count || 0);
  el('#modal-eyebrow').textContent = 'Безопасное удаление';
  el('#modal-title').textContent = 'Переместить наставника в архив?';
  form.dataset.type = 'archive-mentor';
  form.dataset.recordId = mentor.id;
  form.innerHTML = `<div class="confirm-panel"><div class="confirm-mark">!</div><div><strong>${escapeHTML(mentor.full_name)}</strong><p>${assigned ? `Закреплено студентов: ${assigned}. Перед архивацией выберите нового наставника — система проверит его лимит.` : 'Закреплённых студентов нет. История наставника будет сохранена.'}</p></div></div>${assigned ? `<div class="field archive-replacement"><label>Переназначить студентов *</label><select class="select" name="replacement_mentor_id" required>${mentorSelectOptions('', mentor.id)}</select></div>` : ''}${modalActions('Переместить в архив')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

function openArchiveCourse(course) {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Безопасное удаление';
  el('#modal-title').textContent = 'Удалить курс / модуль?';
  form.dataset.type = 'archive-course';
  form.dataset.recordId = course.id;
  form.innerHTML = `<div class="confirm-panel"><div class="confirm-mark">!</div><div><strong>${escapeHTML(course.title)}</strong><p>Модуль исчезнет из программы студентов. Прогресс, результаты и вопросы теста сохранятся — курс можно восстановить.</p></div></div>${modalActions('Удалить курс')}`;
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

async function openQuiz(courseId) {
  const quiz = await api(`/api/quiz?course_id=${courseId}`);
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = `Порог прохождения ${quiz.course.pass_score}%`;
  el('#modal-title').textContent = quiz.course.title;
  form.dataset.type = 'quiz';
  form.dataset.courseId = courseId;
  form.innerHTML = `<div class="quiz-list">${quiz.questions.map((question, qIndex) => `<fieldset class="quiz-question"><legend><span>${qIndex + 1}</span>${escapeHTML(question.question)}</legend><div class="quiz-options">${question.options.map((option, oIndex) => `<label><input type="radio" name="question_${qIndex}" value="${oIndex}" required><span>${escapeHTML(option)}</span></label>`).join('')}</div></fieldset>`).join('')}</div>${modalActions('Завершить тест')}`;
  el('#modal').classList.add('wide');
  el('#modal').classList.add('open');
  el('#modal-backdrop').classList.add('open');
}

async function openQuizEditor(courseId) {
  const quiz = await api(`/api/course-questions?course_id=${courseId}`);
  state.quizCourseId = courseId;
  state.quizQuestions = quiz.questions;
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = `Проходной балл ${quiz.course.pass_score}%`;
  el('#modal-title').textContent = `Тест · ${quiz.course.title}`;
  form.dataset.type = 'quiz-editor';
  form.dataset.courseId = courseId;
  form.dataset.recordId = '';
  form.innerHTML = `<div class="quiz-editor-toolbar"><div><strong>${quiz.questions.length} ${plural(quiz.questions.length, 'вопрос', 'вопроса', 'вопросов')}</strong><span>У каждого вопроса четыре варианта и один правильный ответ.</span></div><button class="button primary" type="button" data-action="add-quiz-question" data-course-id="${courseId}"><span class="plus">+</span> Добавить вопрос</button></div><div class="quiz-editor-list">${quiz.questions.length ? quiz.questions.map((item, index) => {
    const correctOption = item.options[item.correct_index] || '—';
    return `<article class="quiz-editor-item"><div class="quiz-editor-number">${index + 1}</div><div class="quiz-editor-copy"><strong>${escapeHTML(item.question)}</strong><span>Правильный ответ: ${String.fromCharCode(65 + Number(item.correct_index))}. ${escapeHTML(correctOption)}</span></div><div class="quiz-editor-actions"><button class="button secondary small" type="button" data-action="edit-quiz-question" data-question-id="${item.id}">Изменить</button>${canDeleteRecords() ? `<button class="button ghost small danger" type="button" data-action="delete-quiz-question" data-question-id="${item.id}">Удалить</button>` : ''}</div></article>`;
  }).join('') : '<div class="empty"><strong>В тесте пока нет вопросов</strong>Добавьте первый вопрос — после этого у студентов появится кнопка «Пройти тест».</div>'}</div><div class="modal-actions"><button class="button primary" type="button" data-close-modal>Готово</button></div>`;
  el('#modal').classList.add('wide', 'open');
  el('#modal-backdrop').classList.add('open');
}

function openQuizQuestionModal(courseId, record = null) {
  const form = el('#modal-form');
  const isEdit = Boolean(record);
  const options = record?.options || ['', '', '', ''];
  el('#modal-eyebrow').textContent = isEdit ? 'Редактор теста' : 'Новый вопрос';
  el('#modal-title').textContent = isEdit ? 'Изменить вопрос' : 'Добавить вопрос';
  form.dataset.type = 'quiz-question';
  form.dataset.courseId = courseId;
  form.dataset.recordId = record?.id || '';
  form.innerHTML = `<div class="form-grid"><div class="field full"><label>Вопрос *</label><textarea class="textarea" name="question" required placeholder="Введите формулировку вопроса">${escapeHTML(record?.question || '')}</textarea></div>${options.map((option, index) => `<div class="field"><label>Вариант ${String.fromCharCode(65 + index)} *</label><input class="input" name="option_${index}" required value="${escapeHTML(option)}"></div>`).join('')}<div class="field full"><label>Правильный ответ *</label><select class="select" name="correct_index" required>${options.map((_, index) => `<option value="${index}" ${selected(index, record?.correct_index ?? 0)}>Вариант ${String.fromCharCode(65 + index)}</option>`).join('')}</select><small class="field-hint">Укажите единственный правильный вариант. Порядок ответов для студента сохраняется таким же.</small></div></div>${modalActions(isEdit ? 'Сохранить вопрос' : 'Добавить вопрос')}`;
  el('#modal').classList.add('wide', 'open');
  el('#modal-backdrop').classList.add('open');
  setTimeout(() => el('[name="question"]', form)?.focus(), 100);
}

function openDeleteQuizQuestion(record) {
  const form = el('#modal-form');
  el('#modal-eyebrow').textContent = 'Редактор теста';
  el('#modal-title').textContent = 'Удалить вопрос?';
  form.dataset.type = 'delete-quiz-question';
  form.dataset.courseId = record.course_id;
  form.dataset.recordId = record.id;
  form.innerHTML = `<div class="confirm-panel"><div class="confirm-mark">!</div><div><strong>${escapeHTML(record.question)}</strong><p>Вопрос будет удалён из теста. Остальные вопросы и результаты студентов сохранятся.</p></div></div>${modalActions('Удалить вопрос')}`;
  el('#modal').classList.add('wide', 'open');
  el('#modal-backdrop').classList.add('open');
}

function modalActions(label) {
  return `<div class="modal-actions"><button class="button secondary" type="button" data-close-modal>Отмена</button><button class="button primary" type="submit">${label}</button></div>`;
}

function closeModal() {
  el('#modal').classList.remove('open');
  el('#modal').classList.remove('wide');
  el('#modal-backdrop').classList.remove('open');
}

function toast(message, type = 'success') {
  const node = document.createElement('div');
  node.className = `toast ${type}`;
  node.textContent = message;
  el('#toast-region').append(node);
  setTimeout(() => node.remove(), 3600);
}

function showLogin() {
  closeModal();
  closeDrawer();
  el('#loading').classList.add('is-hidden');
  el('#app').classList.add('is-hidden');
  el('#auth-screen').classList.remove('is-hidden');
  el('#login-panel').classList.remove('is-hidden');
  el('#password-panel').classList.add('is-hidden');
  el('#login-error').textContent = '';
  setTimeout(() => el('#login-form [name="phone"]')?.focus(), 50);
}

function showForcedPasswordChange(user) {
  state.session = user;
  el('#loading').classList.add('is-hidden');
  el('#app').classList.add('is-hidden');
  el('#auth-screen').classList.remove('is-hidden');
  el('#login-panel').classList.add('is-hidden');
  el('#password-panel').classList.remove('is-hidden');
  el('#password-error').textContent = '';
  el('#password-form').reset();
  setTimeout(() => el('#password-form [name="current_password"]')?.focus(), 50);
}

async function enterApplication(user) {
  state.session = user;
  state.role = user.role;
  state.page = roleDefaults[user.role];
  if (user.mentor_id) state.mentorId = Number(user.mentor_id);
  if (user.student_id) state.studentId = Number(user.student_id);
  el('#auth-screen').classList.add('is-hidden');
  el('#app').classList.remove('is-hidden');
  await loadData(true);
}

async function saveModal(form) {
  const button = el('[type="submit"]', form);
  button.disabled = true;
  const data = Object.fromEntries(new FormData(form));
  try {
    if (form.dataset.type === 'change-password') {
      if (data.new_password !== data.confirm_password) throw new Error('Новые пароли не совпадают');
      await api('/api/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: data.current_password, new_password: data.new_password }) });
      closeModal();
      toast('Пароль успешно изменён');
      return;
    } else if (form.dataset.type === 'change-admin-phone') {
      const result = await api('/api/auth/change-phone', { method: 'POST', body: JSON.stringify({ new_phone: data.new_phone, current_password: data.current_password }) });
      state.session = result.user;
      closeModal();
      toast('Номер администратора изменён');
      await loadData(true);
      return;
    } else if (form.dataset.type === 'quiz') {
      const answers = els('.quiz-question', form).map((_, index) => Number(el(`input[name="question_${index}"]:checked`, form).value));
      const courseId = Number(form.dataset.courseId);
      const result = await api('/api/quiz-attempts', { method: 'POST', body: JSON.stringify({ student_id: state.studentId, course_id: courseId, answers }) });
      closeModal();
      const successMessage = courseId === 2
        ? `Тест пройден: ${result.score}%. Допуск оформлен.`
        : `Тест пройден: ${result.score}%.`;
      toast(result.passed ? successMessage : `Результат ${result.score}%. Для прохождения нужно ${result.pass_score}%.`, result.passed ? 'success' : 'error');
      await loadData(true);
      return;
    } else if (form.dataset.type === 'quiz-question') {
      const courseId = Number(form.dataset.courseId);
      const recordId = form.dataset.recordId;
      const payload = {
        course_id: courseId,
        question: data.question,
        options: [data.option_0, data.option_1, data.option_2, data.option_3],
        correct_index: Number(data.correct_index),
      };
      await api(recordId ? `/api/quiz-questions/${recordId}` : '/api/quiz-questions', {
        method: recordId ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      });
      closeModal();
      toast(recordId ? 'Вопрос изменён' : 'Вопрос добавлен в тест');
      await loadData(true);
      await openQuizEditor(courseId);
      return;
    } else if (form.dataset.type === 'delete-quiz-question') {
      const courseId = Number(form.dataset.courseId);
      await api(`/api/quiz-questions/${form.dataset.recordId}`, { method: 'DELETE' });
      closeModal();
      toast('Вопрос удалён из теста');
      await loadData(true);
      await openQuizEditor(courseId);
      return;
    } else if (form.dataset.type === 'student') {
      const recordId = form.dataset.recordId;
      await api(recordId ? `/api/students/${recordId}` : '/api/students', { method: recordId ? 'PATCH' : 'POST', body: JSON.stringify(data) });
    } else if (form.dataset.type === 'mentor') {
      const recordId = form.dataset.recordId;
      await api(recordId ? `/api/mentors/${recordId}` : '/api/mentors', { method: recordId ? 'PATCH' : 'POST', body: JSON.stringify(data) });
    } else if (form.dataset.type === 'course') {
      const recordId = form.dataset.recordId;
      await api(recordId ? `/api/courses/${recordId}` : '/api/courses', { method: recordId ? 'PATCH' : 'POST', body: JSON.stringify(data) });
    } else if (form.dataset.type === 'evaluation') {
      const recordId = form.dataset.recordId;
      const result = await api(recordId ? `/api/evaluations/${recordId}` : '/api/evaluations', { method: recordId ? 'PATCH' : 'POST', body: JSON.stringify(data) });
      closeModal();
      toast(`${recordId ? 'Оценка обновлена' : 'Оценка сохранена'}: ${result.score}/100 → ${result.grade}`);
      await loadData(true);
      return;
    } else if (form.dataset.type === 'delete-evaluation') {
      await api(`/api/evaluations/${form.dataset.recordId}`, { method: 'DELETE' });
      closeModal();
      toast('Оценка удалена из журнала');
      await loadData(true);
      return;
    } else if (form.dataset.type === 'archive-student') {
      await api(`/api/students/${form.dataset.recordId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: true }) });
    } else if (form.dataset.type === 'archive-mentor') {
      await api(`/api/mentors/${form.dataset.recordId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: true, replacement_mentor_id: data.replacement_mentor_id || null }) });
    } else if (form.dataset.type === 'archive-course') {
      await api(`/api/courses/${form.dataset.recordId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: true }) });
    } else if (form.dataset.type === 'rotation') {
      const recordId = form.dataset.recordId;
      await api(recordId ? `/api/rotations/${recordId}` : '/api/rotations', { method: recordId ? 'PATCH' : 'POST', body: JSON.stringify(data) });
    }
    else if (form.dataset.type === 'safety') {
      const result = await api('/api/safety-tests', { method: 'POST', body: JSON.stringify(data) });
      toast(result.passed ? 'Допуск оформлен, наставник уведомлён' : 'Результат сохранён — требуется пересдача', result.passed ? 'success' : 'error');
      closeModal();
      await loadData(true);
      return;
    }
    const messages = { student: 'Данные студента и ротации сохранены', mentor: 'Данные наставника сохранены', course: 'Учебный курс сохранён', rotation: 'Данные ротации сохранены', 'archive-student': 'Студент перемещён в архив', 'archive-mentor': 'Наставник перемещён в архив', 'archive-course': 'Курс удалён из программы и сохранён в архиве' };
    toast(messages[form.dataset.type] || 'Данные успешно сохранены');
    closeModal();
    await loadData(true);
  } catch (error) {
    toast(error.message, 'error');
    button.disabled = false;
  }
}

async function saveProgress() {
  const button = el('[data-action="save-progress"]');
  button.disabled = true;
  try {
    await api('/api/progress', { method: 'POST', body: JSON.stringify({
      student_id: state.studentId,
      mentor_id: state.mentorId,
      items: Object.entries(state.draftProgress).map(([skill_id, status]) => ({ skill_id: Number(skill_id), status })),
    }) });
    toast('Результаты сохранены. Студент получил уведомление.');
    await loadData(true);
  } catch (error) {
    toast(error.message, 'error');
    button.disabled = false;
  }
}

function applyStudentFilters() {
  const query = (el('#student-search')?.value || '').trim().toLowerCase();
  const status = el('#status-filter')?.value || '';
  const stream = el('#stream-filter')?.value || '';
  els('.student-card').forEach(card => {
    card.style.display = (!query || card.dataset.search.includes(query)) && (!status || card.dataset.status === status) && (!stream || card.dataset.stream === stream) ? '' : 'none';
  });
}

document.addEventListener('click', async event => {
  if (event.target.closest('#help-button')) { openHelp(); return; }
  if (event.target.closest('#change-password-button')) { openChangePasswordModal(); return; }
  if (event.target.closest('[data-action="change-admin-phone"]')) { openChangeAdminPhoneModal(); return; }
  if (event.target.closest('#logout-button')) {
    try { await api('/api/auth/logout', { method: 'POST', body: '{}' }); }
    finally { state.session = null; state.data = null; showLogin(); }
    return;
  }
  const resetPassword = event.target.closest('[data-action="reset-password"]');
  if (resetPassword) {
    const account = state.accounts.find(item => item.id === Number(resetPassword.dataset.userId));
    if (!account || !confirm(`Сбросить пароль для «${account.full_name}»?`)) return;
    try {
      const result = await api(`/api/users/${account.id}/reset-password`, { method: 'POST', body: '{}' });
      showTemporaryPassword(account, result.temporary_password);
    } catch (error) { toast(error.message, 'error'); }
    return;
  }
  if (event.target.closest('[data-action="copy-password"]')) {
    const input = el('[data-temporary-password]');
    if (input) {
      try { await navigator.clipboard.writeText(input.value); toast('Пароль скопирован'); }
      catch (_) { input.select(); document.execCommand('copy'); toast('Пароль скопирован'); }
    }
    return;
  }
  const pageButton = event.target.closest('[data-page]');
  if (pageButton) {
    state.page = pageButton.dataset.page;
    el('#sidebar').classList.remove('open');
    await renderPage();
    return;
  }
  const scheduleStream = event.target.closest('[data-dashboard-schedule-stream]');
  if (scheduleStream) {
    state.dashboardScheduleStream = scheduleStream.dataset.dashboardScheduleStream;
    renderDashboard();
    return;
  }
  if (event.target.closest('#mobile-menu')) { el('#sidebar').classList.toggle('open'); return; }
  if (event.target.closest('#notifications-button') || event.target.closest('[data-action="notifications"]')) { openDrawer(); return; }
  if (event.target.closest('[data-close-drawer]') || event.target === el('#drawer-backdrop')) { closeDrawer(); return; }
  if (event.target.closest('[data-close-modal]') || event.target === el('#modal-backdrop')) { closeModal(); return; }
  if (event.target.closest('[data-action="add-student"]')) { openModal('student'); return; }
  if (event.target.closest('[data-action="add-mentor"]')) { openModal('mentor'); return; }
  if (event.target.closest('[data-action="add-course"]')) { openModal('course'); return; }
  if (event.target.closest('[data-action="toggle-course-archive"]')) { state.showArchivedCourses = !state.showArchivedCourses; await renderCourses(); return; }
  const manageQuiz = event.target.closest('[data-action="manage-quiz"]');
  if (manageQuiz) {
    try { await openQuizEditor(Number(manageQuiz.dataset.courseId)); }
    catch (error) { toast(error.message, 'error'); }
    return;
  }
  const addQuizQuestion = event.target.closest('[data-action="add-quiz-question"]');
  if (addQuizQuestion) { openQuizQuestionModal(Number(addQuizQuestion.dataset.courseId)); return; }
  const editQuizQuestion = event.target.closest('[data-action="edit-quiz-question"]');
  if (editQuizQuestion) {
    const question = state.quizQuestions.find(item => item.id === Number(editQuizQuestion.dataset.questionId));
    if (question) openQuizQuestionModal(state.quizCourseId, question);
    return;
  }
  const deleteQuizQuestion = event.target.closest('[data-action="delete-quiz-question"]');
  if (deleteQuizQuestion) {
    const question = state.quizQuestions.find(item => item.id === Number(deleteQuizQuestion.dataset.questionId));
    if (question) openDeleteQuizQuestion(question);
    return;
  }
  const editCourse = event.target.closest('[data-action="edit-course"]');
  if (editCourse) {
    const course = state.data.courses.find(item => item.id === Number(editCourse.dataset.courseId));
    if (course) openModal('course', course);
    return;
  }
  const archiveCourse = event.target.closest('[data-action="archive-course"]');
  if (archiveCourse) {
    const course = state.data.courses.find(item => item.id === Number(archiveCourse.dataset.courseId));
    if (course) openArchiveCourse(course);
    return;
  }
  const restoreCourse = event.target.closest('[data-action="restore-course"]');
  if (restoreCourse) {
    try {
      await api(`/api/courses/${restoreCourse.dataset.courseId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: false }) });
      toast('Курс восстановлен и назначен активным студентам');
      await loadData(true);
    } catch (error) { toast(error.message, 'error'); }
    return;
  }
  const evaluationView = event.target.closest('[data-evaluation-view]');
  if (evaluationView) {
    state.evaluationView = evaluationView.dataset.evaluationView;
    renderEvaluationWorkspace();
    return;
  }
  const journalScore = event.target.closest('[data-action="add-journal-score"]');
  if (journalScore) {
    const column = state.journalColumns[Number(journalScore.dataset.columnIndex)];
    if (column) openEvaluationModal(Number(journalScore.dataset.studentId), null, {
      student_id: Number(journalScore.dataset.studentId),
      course_id: column.course_id,
      evaluation_type: column.evaluation_type,
      evaluated_at: column.evaluated_at,
      section_title: column.section_title,
    });
    return;
  }
  if (event.target.closest('[data-action="add-evaluation"]')) {
    const streamStudents = roleStudents().filter(student => !state.evaluationStream || student.stream === state.evaluationStream);
    openEvaluationModal(null, null, {
      student_id: streamStudents[0]?.id,
      course_id: state.evaluationCourse && state.evaluationCourse !== 'unassigned' ? Number(state.evaluationCourse) : null,
      evaluation_type: state.evaluationType || 'section',
      evaluated_at: state.evaluationMonth ? `${state.evaluationMonth}-01` : undefined,
    });
    return;
  }
  const addDemoExam = event.target.closest('[data-action="add-demo-exam"]');
  if (addDemoExam) {
    const filteredStudents = roleStudents().filter(student => !state.demoExamStream || student.stream === state.demoExamStream);
    openEvaluationModal(Number(addDemoExam.dataset.studentId || state.demoExamStudentId || filteredStudents[0]?.id || 0), null, {
      student_id: Number(addDemoExam.dataset.studentId || state.demoExamStudentId || filteredStudents[0]?.id || 0),
      evaluation_type: 'demo_exam',
      section_title: 'Демонстрационный экзамен',
    });
    return;
  }
  const editEvaluation = event.target.closest('[data-action="edit-evaluation"]');
  if (editEvaluation) {
    const record = state.evaluations.find(item => item.id === Number(editEvaluation.dataset.evaluationId));
    if (record) openEvaluationModal(record.student_id, record);
    return;
  }
  const deleteEvaluation = event.target.closest('[data-action="delete-evaluation"]');
  if (deleteEvaluation) {
    const record = state.evaluations.find(item => item.id === Number(deleteEvaluation.dataset.evaluationId));
    if (record) openDeleteEvaluation(record);
    return;
  }
  const profileButton = event.target.closest('[data-student-profile]');
  if (profileButton) {
    state.profileStudentId = Number(profileButton.dataset.studentProfile);
    state.page = 'student_profile';
    await renderPage();
    return;
  }
  const evaluateProfile = event.target.closest('[data-action="evaluate-profile-student"]');
  if (evaluateProfile) { openEvaluationModal(Number(evaluateProfile.dataset.studentId)); return; }
  const editProfile = event.target.closest('[data-action="edit-profile-student"]');
  if (editProfile) {
    const student = state.data.dashboard.students.find(item => item.id === Number(editProfile.dataset.studentId));
    if (student) openModal('student', student);
    return;
  }
  if (event.target.closest('[data-action="save-attendance"]')) { await saveAttendance(); return; }
  if (event.target.closest('[data-action="mark-all-present"]')) {
    els('.attendance-row').forEach(row => {
      row.dataset.status = 'present';
      els('[data-att-status]', row).forEach(button => {
        button.classList.remove('selected', 'present', 'late', 'excused', 'absent');
        if (button.dataset.attStatus === 'present') button.classList.add('selected', 'present');
      });
      el('.attendance-hours', row).value = 8;
    });
    return;
  }
  const attendanceStatus = event.target.closest('[data-att-status]');
  if (attendanceStatus) {
    const row = attendanceStatus.closest('.attendance-row');
    const status = attendanceStatus.dataset.attStatus;
    row.dataset.status = status;
    els('[data-att-status]', row).forEach(button => button.classList.remove('selected', 'present', 'late', 'excused', 'absent'));
    attendanceStatus.classList.add('selected', status);
    el('.attendance-hours', row).value = ['present', 'late'].includes(status) ? 8 : 0;
    return;
  }
  if (event.target.closest('[data-action="toggle-student-archive"]')) { state.showArchivedStudents = !state.showArchivedStudents; renderStudents(false); return; }
  if (event.target.closest('[data-action="toggle-mentor-archive"]')) { state.showArchivedMentors = !state.showArchivedMentors; renderMentors(); return; }
  const editStudent = event.target.closest('[data-action="edit-student"]');
  if (editStudent) {
    const student = state.data.dashboard.students.find(item => item.id === Number(editStudent.dataset.studentId));
    openModal('student', student);
    return;
  }
  const archiveStudent = event.target.closest('[data-action="archive-student"]');
  if (archiveStudent) {
    const student = state.data.dashboard.students.find(item => item.id === Number(archiveStudent.dataset.studentId));
    openArchiveStudent(student);
    return;
  }
  const restoreStudent = event.target.closest('[data-action="restore-student"]');
  if (restoreStudent) {
    try {
      await api(`/api/students/${restoreStudent.dataset.studentId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: false }) });
      toast('Студент восстановлен в активном реестре');
      await loadData(true);
    } catch (error) { toast(error.message, 'error'); }
    return;
  }
  const editMentor = event.target.closest('[data-action="edit-mentor"]');
  if (editMentor) {
    const mentor = state.data.mentors.find(item => item.id === Number(editMentor.dataset.mentorId));
    openModal('mentor', mentor);
    return;
  }
  const archiveMentor = event.target.closest('[data-action="archive-mentor"]');
  if (archiveMentor) {
    const mentor = state.data.mentors.find(item => item.id === Number(archiveMentor.dataset.mentorId));
    openArchiveMentor(mentor);
    return;
  }
  const restoreMentor = event.target.closest('[data-action="restore-mentor"]');
  if (restoreMentor) {
    try {
      await api(`/api/mentors/${restoreMentor.dataset.mentorId}`, { method: 'PATCH', body: JSON.stringify({ is_archived: false }) });
      toast('Наставник восстановлен в активном реестре');
      await loadData(true);
    } catch (error) { toast(error.message, 'error'); }
    return;
  }
  if (event.target.closest('[data-action="add-rotation"]')) { openModal('rotation'); return; }
  const editRotation = event.target.closest('[data-action="edit-rotation"]');
  if (editRotation) {
    const rotation = state.data.dashboard.rotations.find(item => item.id === Number(editRotation.dataset.rotationId));
    if (rotation) openModal('rotation', rotation);
    return;
  }
  if (event.target.closest('[data-action="open-safety"]')) { openModal('safety'); return; }
  const quizButton = event.target.closest('[data-action="take-quiz"]');
  if (quizButton) { await openQuiz(Number(quizButton.dataset.courseId)); return; }
  const moduleButton = event.target.closest('[data-module]');
  if (moduleButton) { state.module = moduleButton.dataset.module; await renderMatrix(); return; }
  const skillButton = event.target.closest('[data-skill]');
  if (skillButton) {
    const group = skillButton.closest('.segmented');
    els('button', group).forEach(button => button.classList.remove('selected'));
    skillButton.classList.add('selected');
    state.draftProgress[Number(skillButton.dataset.skill)] = skillButton.dataset.status;
    return;
  }
  if (event.target.closest('[data-action="save-progress"]')) { await saveProgress(); return; }
  if (event.target.closest('[data-action="reset-checklist"]')) { await renderChecklist(); toast('Несохранённые изменения сброшены'); return; }
  const studentButton = event.target.closest('[data-open-student]');
  if (studentButton) {
    state.studentId = Number(studentButton.dataset.openStudent);
    if (state.role === 'student') state.page = 'trajectory';
    else { state.profileStudentId = state.studentId; state.page = 'student_profile'; }
    await renderPage();
  }
});

document.addEventListener('change', async event => {
  if (event.target.matches('[data-select="mentor"]')) {
    state.mentorId = Number(event.target.value);
    await renderPage();
  } else if (event.target.matches('[data-select="checklist-student"], [data-select="student-view"]')) {
    state.studentId = Number(event.target.value);
    await renderPage();
  } else if (event.target.id === 'attendance-date') {
    state.attendanceDate = event.target.value;
    await renderAttendance();
  } else if (event.target.id === 'attendance-stream') {
    state.attendanceStream = event.target.value;
    await renderAttendance();
  } else if (event.target.matches('[data-select="evaluation-stream"]')) {
    const studentSelect = el('[data-select="evaluation-student"]', event.target.form);
    studentSelect.innerHTML = evaluationStudentOptions(event.target.value);
    const selectedStudentId = Number(studentSelect.value || 0);
    const rotationSelect = el('[data-select="evaluation-rotation"]', event.target.form);
    if (rotationSelect) rotationSelect.innerHTML = evaluationRotationOptions(selectedStudentId);
  } else if (event.target.matches('[data-select="evaluation-student"]')) {
    const rotationSelect = el('[data-select="evaluation-rotation"]', event.target.form);
    if (rotationSelect) rotationSelect.innerHTML = evaluationRotationOptions(Number(event.target.value));
  } else if (event.target.matches('[data-evaluation-filter]')) {
    const filter = event.target.dataset.evaluationFilter;
    if (filter === 'stream') state.evaluationStream = event.target.value;
    if (filter === 'course') state.evaluationCourse = event.target.value;
    if (filter === 'month') state.evaluationMonth = event.target.value;
    if (filter === 'type') state.evaluationType = event.target.value;
    renderEvaluationWorkspace();
  } else if (event.target.id === 'profile-skill-type') {
    state.profileSkillType = event.target.value;
    await renderStudentProfile();
  } else if (event.target.matches('[data-matrix-filter]')) {
    const filter = event.target.dataset.matrixFilter;
    if (filter === 'stream') {
      state.matrixStream = event.target.value;
      state.matrixStudentId = 0;
    }
    if (filter === 'student') state.matrixStudentId = Number(event.target.value || 0);
    if (filter === 'type') state.matrixSkillType = event.target.value;
    await renderMatrix();
  } else if (event.target.matches('[data-demo-filter]')) {
    const filter = event.target.dataset.demoFilter;
    if (filter === 'stream') {
      state.demoExamStream = event.target.value;
      state.demoExamStudentId = 0;
    }
    if (filter === 'student') state.demoExamStudentId = Number(event.target.value || 0);
    await renderDemoExam();
  } else if (event.target.matches('#status-filter, #stream-filter')) applyStudentFilters();
});

document.addEventListener('input', event => {
  if (event.target.id === 'student-search') applyStudentFilters();
  if (event.target.matches('[data-rotation-date]')) updateRotationStatusPreview(event.target.form);
});

el('#modal-form').addEventListener('submit', event => {
  event.preventDefault();
  saveModal(event.currentTarget);
});

el('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = el('[type="submit"]', form);
  const data = Object.fromEntries(new FormData(form));
  el('#login-error').textContent = '';
  button.disabled = true;
  try {
    const result = await api('/api/auth/login', { method: 'POST', body: JSON.stringify(data) });
    form.reset();
    if (result.user.must_change_password) showForcedPasswordChange(result.user);
    else await enterApplication(result.user);
  } catch (error) {
    el('#login-error').textContent = error.message;
  } finally { button.disabled = false; }
});

el('#password-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = el('[type="submit"]', form);
  const data = Object.fromEntries(new FormData(form));
  el('#password-error').textContent = '';
  if (data.new_password !== data.confirm_password) {
    el('#password-error').textContent = 'Новые пароли не совпадают';
    return;
  }
  button.disabled = true;
  try {
    const result = await api('/api/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password: data.current_password, new_password: data.new_password }) });
    form.reset();
    await enterApplication(result.user);
  } catch (error) {
    el('#password-error').textContent = error.message;
  } finally { button.disabled = false; }
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') { closeModal(); closeDrawer(); el('#sidebar').classList.remove('open'); }
});

(async function init() {
  try {
    const session = await api('/api/auth/session');
    if (!session.authenticated) showLogin();
    else if (session.user.must_change_password) showForcedPasswordChange(session.user);
    else await enterApplication(session.user);
    el('#loading').classList.add('is-hidden');
    setInterval(async () => {
      if (!state.session || document.hidden || el('#modal').classList.contains('open')) return;
      try { await loadData(true); } catch (_) { /* Retry on the next interval. */ }
    }, 5 * 60 * 1000);
  } catch (error) {
    el('#loading').innerHTML = `<div class="empty" style="color:white"><strong style="color:white">Не удалось запустить LMS</strong>${escapeHTML(error.message)}<br><small>Проверьте, что приложение открыто через app.py.</small></div>`;
  }
})();
