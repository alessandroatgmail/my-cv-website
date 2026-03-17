/* ============================================
   CONFIGURATION
   ============================================ */
const CONFIG = {
  counterApiUrl: "https://k74gwscm4l.execute-api.eu-central-1.amazonaws.com/counter",
  chatbotApiUrl: "https://YOUR_API_GATEWAY_URL/chat",
};

/* ============================================
   i18n TRANSLATIONS
   Each key maps to a string in EN and IT.
   To add a new language: add a new locale key
   and translate every string.
   ============================================ */
const TRANSLATIONS = {
en: {
    tagline:       `Backend developer — and more. After 3 years of continuous work for Go Reply on the FAO client, I am now looking for new opportunities. This page is my online CV deployed on AWS, both as a presentation and a learning project. Anything you can't find about me here, you can ask Silvio — my virtual alter ego. The project is available on my GitHub page.`,
    counterLabel:  "👁️ This page has been visited",
    counterTimes:  "times",
    aboutTitle:    "About Me",
    aboutText:     `Starting out as an IT specialist and programmer, I worked as a technical sales consultant for innovative companies for over ten years across Italy, England and Northern Ireland — experiences that exposed me to and deepened my knowledge of the latest technologies, particularly in the fields of Data Science and Machine Learning. In recent years I have focused primarily on backend development while continuing to explore new technologies.`,

    skillsTitle:      "Skills",
    skillResponsive:  "Responsive Design",
    techSkillsTitle:  "Technical Skills",

    experienceTitle:  "Experience",
    present:          "Present",

    job1Title:    "Backend Developer",
    job1date2:    "February 2026",
    job1Desc:     `I designed and developed the backend for a data collection system based on online questionnaires, managing the acquisition of information from national focal points and the visualisation of results through charts and downloadable reports. Starting from the business requirements, I defined the data architecture and implemented the backend services in close collaboration with the client and the frontend team. The success of the initial project — focused on collecting data on forest genetic variability — led to the development of 6 additional projects built on the same architecture. Thanks to the experience gained and the effectiveness of the designed solution, we became extremely fast and efficient in the development and delivery of this type of application, significantly reducing development time while ensuring quality and scalability.`,
    job1Stack:    ["Python3", "Django REST", "PostgreSQL", "Google Cloud Platform"],

    job2Title:    "Python Developer",
    job2Desc:     `Developing dashboards for data visualisation and reporting using an internal fork of Dash.<br>
Backend development of an internal application based on Django REST.<br>
Data migrations, data transformation and migration to a new company application.`,
    job2Stack:    ["Python3", "Django REST", "PostgreSQL", "Dash", "Pandas", "Jupyter Notebook"],

    job3Title:    "Data Scientist",                 // ← era duplicato con job2Desc/job2Stack
    job3Desc:     `For a chemical analysis company, I developed an analysis and a machine learning model for the evaluation of soil and water samples, carrying out the following tasks:<br>
Data cleaning, exploratory data analysis, data transformation, and training and testing of machine learning models.<br>
I subsequently developed an API with Django REST to make the models available to end users.`,
    job3Stack:    ["Python3", "Django REST", "Pandas", "Jupyter Notebook", "TensorFlow", "scikit-learn"],

    job4Title:    "Django Web Developer",
    job4Desc:     `Design and development of a full stack web application using Django for the assessment of credit contracts.`,
    job4Stack:    ["Python3", "Django", "HTML", "Bootstrap", "Javascript", "CSS"],

    educationTitle:   "Education",
    edu1Degree:       "Bachelor's in International Economics",
    edu1School:       "Università degli studi di Padova",
    edu2Degree:       "High school diploma in Informatics",
    edu2School:       "ITIS F. Severi Padova",

    myDayTitle:       "My Typical Day 🍩",
    myDayCaption:     "How I usually split my time during a working day",

    coursesTitle:     "Other Courses",
    courseCertificate: "Certificate Link",
    course1Title:     "Google IT Automation with Python",
    course1Year:      "2020",
    course1Provider:  "Google / Coursera",
    course1Link:      "https://coursera.org/share/be889431ab71fbcec39fbda22269034e",

    course1Title:     "DeepLearning.AI TensorFlow Developer",
    course1Year:      "2020",
    course1Provider:  "Google / Coursera",
    course1Link:      "https://coursera.org/share/be889431ab71fbcec39fbda22269034e",

    languagesTitle:   "Languages",
    lang1Name:        "Italian",   lang1Level: "Native",
    lang2Name:        "English",   lang2Level: "Professional",

    hobbiesTitle:     "Hobbies & Interests",
    hobby1: "Swing dance", hobby2: "Jazz & Blues",
    hobby3: "Event organization",  hobby4: "Hiking",

    chartPlaceholder: "📊 Chart coming soon",

    chatTitle:        "Ask Me Anything 🤖",
    chatIntro:        "Have a question about my experience or skills? Ask my AI assistant!",
    chatWelcome:      "Hi! I'm an AI assistant trained on this CV. Ask me anything about skills, experience, or availability! 👋",
    chatPlaceholder:  "e.g. What are your main skills?",
    chatSend:         "Send",
    footerText:       "Built with ☁️ AWS · Hosted on S3 + CloudFront",
  },
  it: {
        tagline: `
    Backend developer ma non solo. Dopo 3 anni di lavoro continuativo per Go reply su cliente FAO sono alla ricerca di nuove opportunità.
    Questa pagina è il mio CV online deployato so AWS come presentazione e progetto didattico. Quello che non trovate su di me in questa pagina lo potete chiedere a Silvio il mio alter ego virtuale
    il progetto è disponbile sulla mia pagina github
    `,
    counterLabel:  "👁️ Questa pagina è stata visitata",
    counterTimes:  "volte",
    aboutTitle:    "Chi Sono",
    aboutText:     `Nato come perito informatico e programmatore ho lavorato come tecnico commerciale per aziende innovative per oltre dieci anni tra Italia, Inghilterra e Irlanda del Nord. che mi hanno esposto e portato ad approfondire le più recenti tecnologie in particolare in ambiente Data Science e Machine Learning. Ho lavorato negli ultimi anni in particolare come sviluppatore backend e ho continuato ad esplorare nuove teconologie`,
    skillsTitle:      "Competenze",
    skillResponsive:  "Design Responsivo",
    experienceTitle:  "Esperienza",
    job1date2:        "Febbraio 2026",
    job1Title:        "Backend Developer",
    job1Desc:         `Ho progettato e sviluppato il backend per un sistema di raccolta dati tramite questionari online, gestendo l'acquisizione delle informazioni dai referenti nazionali e la visualizzazione dei risultati attraverso grafici e report scaricabili.
                      Partendo dai business requirements, ho definito l'architettura dati e implementato i servizi backend in stretta collaborazione con il cliente e il team frontend. Il successo del progetto iniziale – focalizzato sulla raccolta dati della variabilità genetica delle foreste – ha portato alla realizzazione di altri 6 progetti basati sulla stessa architettura. Grazie all'esperienza acquisita e all'efficacia della soluzione progettata, siamo diventati estremamente rapidi ed efficienti nello sviluppo e nel delivery di questo tipo di applicazioni, riducendo significativamente i tempi di sviluppo e garantendo al contempo qualità e scalabilità.`,
    job1Stack:        ["Python3", "Django REST", "PostgreSQL", "Google Cloud Platform"],
    job2Title:        "Python Developer",
    job2Desc:         `Sviluppo dashboard per visualizzazione dati e reportistica utilizzando un fork interno di dash <br>
Sviluppo backend di applicativo interno basato su django-rest <br>
Data migrations, data trasformazione e migrazione dati in nuovo applicativo aziendale`,
    job2Stack:        ["Python3", "Django REST", "PostgreSQL", "Dash", "Pandas", "Jupyter Notebook"],

    job3Title:        "Data scientist",
    job3Desc:         `Per un’azienda di analisi chimiche ho sviluppato un'analisi e un modello per la valutazione dei campioni di terreno e acque effettuando le seguenti mansioni:<br>
Pulizia dati, analisi esplorativa dei dati, trasformazione dei dati e training e testing dei modelli di machine learning.<br>
Successivamente sviluppato una Api con django rest per far usufruire i modelli agli utenti`,
    job3Stack:        ["Python3", "Django REST", "Pandas", "Jupyter Notebook", "tensorflow", "scickit-learn"],

    job4Title:        "Sviluppatore Web Django",
    job4Desc:         `Progettazione è sviluppo applicazione web full stack con django per la valutazione dei contratti creditizi`,
    job4Stack:        ["Python3", "Django", "HTML", "Bootstrap", "Javascript", "CSS"],

    educationTitle:   "Formazione",
    edu1Degree:       "Laurea in Economia Internazionale",
    edu1School:       "Nome Università · Università degli studi di Padova",
    edu2Degree:       "Diploma di Perito in Informatica",
    edu2School:       "Nome istituto · ITIS F. Severi Padova",
    myDayTitle:       "La mia giornata",
    chatTitle:        "Chiedimi Qualcosa 🤖",
    chatIntro:        "Hai domande sulla mia esperienza o competenze? Chiedi al mio assistente AI!",
    chatWelcome:      "Ciao! Sono un assistente AI addestrato su questo CV. Chiedimi pure di competenze, esperienza o disponibilità! 👋",
    chatPlaceholder:  "es. Quali sono le tue competenze principali?",
    chatSend:         "Invia",
    footerText:       "Realizzato con ☁️ AWS · Ospitato su S3 + CloudFront",
    languagesTitle:   "Lingue",

    coursesTitle:     "Altri Corsi",
    courseCertificate: "Link al certificato",

    course1Title:     "Google IT Automation with Python",
    course1Year:      "2020",
    course1Provider:  "Google IT",
    course1Link:      "https://coursera.org/share/be889431ab71fbcec39fbda22269034e",

    course2Title:     "DeepLearning.AI TensorFlow Developer",
    course2Year:      "2020",
    course2Provider:  "DeepLearning.AI",
    course2Link:      "https://coursera.org/share/86ce8f88edc1044027daf38bacdfff3e",

    course3Title:     "Data Science with Databricks for Data Analysts",
    course3Year:      "2021",
    course3Provider:  "Databricks",
    course3Link:      "https://coursera.org/share/c2f44a6c70e3b9af0e4639a9c1d24a2c",


    languagesTitle:   "Lingue",
    lang1Name:        "Italiano",   lang1Level: "Madrelingua",
    lang2Name:        "Inglese",   lang2Level: "Avanzato",

    hobbiesTitle:     "Hobbies & Interessi",
    hobby1: "Balli swing", hobby2: "Jazz & Blues",
    hobby3: "Organizzazione di eventi",  hobby4: "Camminate",

  },
};

/* ============================================
   THEME MANAGEMENT
   Adds/removes the "light" class on <body>.
   CSS variables in body.light override the
   dark defaults defined in :root.
   ============================================ */
function toggleTheme() {
  const isLight = document.body.classList.toggle("light");
  // Persist preference so it survives page reload
  localStorage.setItem("preferredTheme", isLight ? "light" : "dark");
}

function initTheme() {
  const saved = localStorage.getItem("preferredTheme");
  // Also respect the OS-level preference if no saved choice
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const useDark = saved ? saved === "dark" : prefersDark;
  if (!useDark) document.body.classList.add("light");
}

/* ============================================
   ACTIVE LANGUAGE STATE
   ============================================ */
let currentLang = "en";

/* ============================================
   setLanguage(lang)
   Called by the EN / IT buttons.
   1. Updates the active button style
   2. Sets the <html lang=""> attribute
   3. Replaces every [data-i18n] element's text
   4. Updates input placeholders
   5. Persists the choice to localStorage
   6. Re-renders the chatbot welcome message
   ============================================ */
function setLanguage(lang) {
  if (!TRANSLATIONS[lang]) return;
  currentLang = lang;

  // ── Update button active state ─────────────────
  document.querySelectorAll(".lang-btn").forEach(btn => btn.classList.remove("active"));
  document.getElementById(`btn-${lang}`).classList.add("active");

  // ── Update <html> lang attribute (SEO + accessibility) ──
  document.documentElement.lang = lang;

  const t = TRANSLATIONS[lang];

  // ── Replace all [data-i18n] element inner texts ──
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key] !== undefined) el.innerHTML = t[key];
  });

  // ── Replace input placeholders ─────────────────
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (t[key] !== undefined) el.placeholder = t[key];
  });

  // Handle links — sets both text and href
  document.querySelectorAll("[data-i18n-href]").forEach(el => {
    const key = el.getAttribute("data-i18n-href");
    if (t[key] !== undefined) el.href = t[key];
});

  // Render array keys as <li> lists
 document.querySelectorAll("[data-i18n-list]").forEach(el => {
  const key = el.getAttribute("data-i18n-list");
  if (Array.isArray(t[key])) {
    el.innerHTML = t[key].map(item => `<li>${item}</li>`).join("");
  }
    });

  // ── Persist to localStorage so the choice survives page reload ──
  localStorage.setItem("preferredLang", lang);

  // ── Reset the chatbot welcome message in the new language ──
  renderChatWelcome();
}

/* ============================================
   VIEW COUNTER
   ============================================ */
async function loadViewCount() {
  const el = document.getElementById("view-count");
  try {
    const res  = await fetch(CONFIG.counterApiUrl, { method: "POST" });
    const data = await res.json();
    el.textContent = data.count.toLocaleString();
  } catch (err) {
    el.textContent = "—";
    console.warn("Counter API not configured yet:", err);
  }
}

/* ============================================
   CHATBOT
   ============================================ */
const chatHistory = [];

// Renders (or re-renders) the welcome message in the current language.
// Called on init and every time the language changes.
function renderChatWelcome() {
  const win = document.getElementById("chat-window");
  win.innerHTML = ""; // clear existing messages
  const div = document.createElement("div");
  div.className = "chat-message bot";
  div.textContent = TRANSLATIONS[currentLang].chatWelcome;
  win.appendChild(div);
}

function appendMessage(text, role) {
  const win = document.getElementById("chat-window");
  const div = document.createElement("div");
  div.className = `chat-message ${role}`;
  div.textContent = text;
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
  return div;
}

async function sendMessage() {
  const input   = document.getElementById("chat-input");
  const btn     = document.getElementById("chat-send-btn");
  const userText = input.value.trim();
  if (!userText) return;

  appendMessage(userText, "user");
  chatHistory.push({ role: "user", content: userText });
  input.value  = "";
  btn.disabled = true;

  // "Thinking..." indicator adapts to current language
  const thinkingText = currentLang === "it" ? "Sto elaborando..." : "Thinking...";
  const loadingDiv   = appendMessage(thinkingText, "loading");

  try {
    const res  = await fetch(CONFIG.chatbotApiUrl, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      // Pass the active language so the Lambda can instruct Claude
      // to reply in the correct language
      body: JSON.stringify({ messages: chatHistory, lang: currentLang }),
    });
    const data     = await res.json();
    const botReply = data.reply || (currentLang === "it"
      ? "Non sono riuscito a generare una risposta."
      : "Sorry, I couldn't generate a response.");

    loadingDiv.textContent = botReply;
    loadingDiv.className   = "chat-message bot";
    chatHistory.push({ role: "assistant", content: botReply });

  } catch (err) {
    loadingDiv.textContent = currentLang === "it"
      ? "⚠️ API chatbot non ancora configurata. (Fase 6)"
      : "⚠️ Chatbot API not configured yet. (Phase 6)";
    loadingDiv.className = "chat-message bot";
    console.warn("Chatbot API not configured yet:", err);
  } finally {
    btn.disabled = false;
    input.focus();
  }
}

document.getElementById("chat-input").addEventListener("keydown", e => {
  if (e.key === "Enter") sendMessage();
});

/* ============================================
   INIT
   ============================================ */
document.addEventListener("DOMContentLoaded", () => {
  // Restore language from localStorage, or detect from browser, fallback to EN
  const saved    = localStorage.getItem("preferredLang");
  const browser  = navigator.language?.startsWith("it") ? "it" : "en";
  const initLang = saved || browser;

  initTheme();             // apply dark/light before first render
  setLanguage(initLang);   // renders all text + welcome message
  loadViewCount();
});